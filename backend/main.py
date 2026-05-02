import os
import time
import json
import asyncio
import traceback
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# LangChain & DB Imports
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
from dotenv import load_dotenv

load_dotenv()

# --- 1. Throttling Configuration ---
# Gemini 2.5 Flash-Lite allows higher throughput, but we keep 
# the 10-second gap to ensure multi-step Graph chains succeed.
rate_limiter = InMemoryRateLimiter(
    requests_per_second=0.1, 
    max_bucket_size=1  
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. Config & Clients ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


# Primary LLM: configurable Gemini model
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "models/gemini-1.5-pro-latest")
llm = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    rate_limiter=rate_limiter
)

# Multimodal Embedding Model (3072 Dimensions)
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-2-preview", 
    rate_limiter=rate_limiter,
    task_type="retrieval_document"
)

QDRANT_URL = "http://qdrant:6333"
COLLECTION_NAME = "multimodal_collection_v2" 
q_client = QdrantClient(url=QDRANT_URL)

# --- 3. Database Initialization ---
graph = None
for i in range(15):
    try:
        graph = Neo4jGraph(
            url=os.getenv("NEO4J_URI","bolt://neo4j:7687"),
            username=os.getenv("NEO4J_USERNAME","neo4j"),
            password=os.getenv("NEO4J_PASSWORD")
        )
        collections = q_client.get_collections().collections
        if not any(c.name == COLLECTION_NAME for c in collections):
            q_client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=rest.VectorParams(size=3072, distance=rest.Distance.COSINE)
            )
        print(f"✅ Connected to Databases (Attempt {i+1})")
        break
    except Exception as e:
        print(f"⏳ Waiting for DBs... {e}")
        time.sleep(5)

# --- 4. Core Logic Functions ---

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=5, max=60),
    retry=retry_if_exception_type(Exception)
)
def safe_graph_call(chain, query):
    """Retries graph calls if the API is throttled."""
    return chain.invoke(query)

async def get_multimodal_summary(file_bytes: bytes, mime_type: str):
    """Uses rate-limited Gemini for file analysis."""
    try:
        message = HumanMessage(
            content=[
                {"type": "text", "text": "Analyze this file. Extract key entities and relationships for a knowledge graph. Be concise."},
                {"type": "media", "mime_type": mime_type, "data": file_bytes}
            ]
        )
        response = await llm.ainvoke([message])
        return response.content
    except Exception as e:
        print(f"❌ Multimodal Error: {e}")
        raise e

def update_knowledge_graph(text: str, filename: str):
    """Extracts entities and updates Neo4j."""
    prompt = f"Extract nodes/edges from text. JSON ONLY: {{'nodes':[],'edges':[]}}. Text: {text}"
    try:
        raw = llm.invoke(prompt).content
        clean_json = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)

        nodes = data.get("nodes") or []
        edges = data.get("edges") or []

        for n in nodes:
            node_type = n.get("type")
            node_id = n.get("id") or n.get("name")
            if not node_type or not node_id:
                continue
            graph.query(
                "MERGE (node:" + node_type + " {name: $id})",
                {"id": node_id}
            )
        for e in edges:
            source = e.get("source")
            target = e.get("target")
            rel = e.get("rel") or e.get("type")
            if not source or not target or not rel:
                continue
            graph.query(
                "MATCH (a {name: $s}), (b {name: $t}) MERGE (a)-[:" + rel + "]->(b)",
                {"s": source, "t": target}
            )
        graph.query("MERGE (:Document {name: $name})", {"name": filename})
    except Exception as e:
        print(f"❌ Graph Extraction Error: {e}")

async def run_vector_fallback(query_text: str):
    """Standard RAG fallback using Qdrant with specific query task_type."""
    try:
        query_embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-2-preview",
            task_type="retrieval_query",
            rate_limiter=rate_limiter
        )
        vector_store = QdrantVectorStore(
            client=q_client,
            collection_name=COLLECTION_NAME,
            embedding=query_embeddings
        )
        docs = vector_store.similarity_search(query_text, k=3)
        context = "\n".join([d.page_content for d in docs])
        
        if not context:
            return {"answer": "No relevant info found in vector store."}

        res = await llm.ainvoke(f"Context: {context}\n\nQuestion: {query_text}")
        return {"answer": res.content}
    except Exception as e:
        return {"answer": f"Vector fallback failed: {str(e)}"}

# --- 5. API Endpoints ---

@app.post("/upload")
async def handle_upload(file: UploadFile = File(...)):
    try:
        print(f"📥 1. Processing: {file.filename}")
        content = await file.read()
        
        print("🤖 2. Generating Multimodal Summary...")
        summary = await get_multimodal_summary(content, file.content_type)
        
        print("🔢 3. Indexing into Qdrant...")
        await QdrantVectorStore.afrom_texts(
            texts=[summary],
            embedding=embeddings,
            url=QDRANT_URL,
            collection_name=COLLECTION_NAME,
            metadatas=[{"source": file.filename}]
        )
        
        print("🕸️ 4. Updating Knowledge Graph...")
        update_knowledge_graph(summary, file.filename)
        
        print(f"✅ Success: {file.filename}")
        return {"status": "success", "filename": file.filename}
    except Exception as e:
        print("❌ Upload Route Failed")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

class Query(BaseModel):
    query: str

@app.post("/chat")
async def handle_chat(payload: Query):
    try:
        print(f"🧐 Querying: {payload.query}")
        chain = GraphCypherQAChain.from_llm(
            llm, 
            graph=graph, 
            verbose=True, 
            allow_dangerous_requests=True
        )
        
        result = safe_graph_call(chain, payload.query)
        answer = result.get("result")

        if not answer or "I don't know" in answer:
            print("🔍 Falling back to Vector...")
            return await run_vector_fallback(payload.query)

        return {"answer": answer}

    except Exception as e:
        if "429" in str(e):
            return {"answer": "API Busy. Retrying automatically..."}
        return await run_vector_fallback(payload.query)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
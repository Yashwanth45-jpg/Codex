import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
import google.generativeai as genai

# 2026 Multimodal Embedding Model
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2")

async def process_multimodal_file(file_content: bytes, mime_type: str, filename: str):
    """
    Analyzes Text, Images, or Audio using Gemini 3 and stores in Qdrant.
    """
    model = genai.GenerativeModel("models/gemini-3-flash")
    
    # 1. Generate a descriptive summary for the modality
    # This acts as our "text bridge" for retrieval and graph extraction
    prompt = f"Analyze this {mime_type} file. Extract key entities, facts, and a detailed summary for a RAG system."
    
    response = model.generate_content([
        prompt,
        {"mime_type": mime_type, "data": file_content}
    ])
    
    description = response.text

    # 2. Vectorize the description and raw metadata into Qdrant
    # Qdrant supports the 3072 dimensions of Gemini Embedding 2
    QdrantVectorStore.from_texts(
        texts=[description],
        embedding=embeddings,
        url="http://qdrant:6333",
        collection_name="multimodal_rag",
        metadatas=[{"filename": filename, "type": mime_type}]
    )
    
    return description
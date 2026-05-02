from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from langchain_google_genai import ChatGoogleGenerativeAI
import json

# Connection to Neo4j container
graph = Neo4jGraph(url="bolt://neo4j:7687", username="neo4j", password="password")
llm = ChatGoogleGenerativeAI(model="models/gemini-3-flash-preview")

def extract_to_graph(text: str, source_name: str):
    """
    Uses Gemini 3 to convert text into Neo4j Nodes and Relationships.
    """
    extraction_prompt = f"""
    Extract entities (Person, Organization, Concept, Event) and relationships 
    from the following text. Return ONLY valid JSON:
    {{ "nodes": [ {{"id": "name", "type": "label"}} ], "edges": [ {{"source": "id", "target": "id", "rel": "action"}} ] }}
    
    Text: {text}
    """
    
    response = llm.invoke(extraction_prompt)
    try:
        data = json.loads(response.content)
        
        # Inject into Neo4j
        for node in data.get("nodes", []):
            graph.query("MERGE (n:" + node['type'] + " {id: $id})", {"id": node['id']})
            
        for edge in data.get("edges", []):
            graph.query(
                "MATCH (a {id: $source}), (b {id: $target}) MERGE (a)-[:" + edge['rel'] + "]->(b)",
                {"source": edge['source'], "target": edge['target']}
            )
            
        # Link entities to the source document
        graph.query("MATCH (n) WHERE n.id IN $ids MERGE (d:Document {name: $doc})-[:MENTIONS]->(n)", 
                    {"ids": [n['id'] for n in data.get("nodes", [])], "doc": source_name})
    except:
        print("Graph extraction failed for this chunk.")

def query_hybrid_rag(user_query: str):
    """
    The 'Hybrid' part: Searches the Knowledge Graph using Cypher.
    """
    # GraphCypherQAChain automatically generates Cypher from natural language
    chain = GraphCypherQAChain.from_llm(llm, graph=graph, allow_dangerous_requests=True)
    return chain.invoke(user_query)
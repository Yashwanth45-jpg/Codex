# Signal Forge - Project Presentation

## Executive Summary
Signal Forge is a multi-modal research cockpit that ingests files, builds a knowledge graph and vector index, and delivers grounded answers through a briefing-style chat interface. It pairs a FastAPI backend with Neo4j (graph) and Qdrant (vector), while the React + Vite frontend provides a polished briefing experience.

## Problem Statement
Teams often struggle to transform unstructured documents into actionable knowledge. Signal Forge solves this by combining:
- Structured reasoning via a knowledge graph
- Semantic recall via vector search
- A simple briefing UI that narrates the analysis

## Tech Stack
- Frontend: React, Vite, CSS (custom UI), Axios
- Backend: FastAPI, LangChain, Google Gemini models
- Datastores: Neo4j (graph), Qdrant (vector)
- Infra: Docker + docker-compose

## Architecture Overview
1. Client UI (Signal Forge)
   - File staging
   - Briefing chat
   - Prompt presets
2. API (FastAPI)
   - /upload for ingestion
   - /chat for questions
3. LLM layer (Gemini)
   - Multimodal analysis for file summaries
   - Graph QA chain for reasoning
4. Storage
   - Neo4j for entities and relationships
   - Qdrant for semantic search

## End-to-End Flow (Detailed)
1. Start services
   - Docker Compose launches backend, Neo4j, and Qdrant.
   - Frontend runs via Vite locally for development.
2. Upload a file
   - User selects a file in the UI and clicks "Index brief".
   - Frontend posts the file to `/upload`.
3. Multimodal analysis
   - Backend sends file bytes to Gemini for summarization and entity extraction.
   - The summary becomes the core representation of the file.
4. Vector indexing
   - The summary is embedded and stored in Qdrant.
   - Metadata records the source filename.
5. Graph extraction
   - Entities and relationships are parsed into nodes and edges.
   - Neo4j stores the resulting knowledge graph.
6. Ask a question
   - User enters a query in the briefing chat.
   - Backend runs a GraphCypherQAChain over the Neo4j graph.
7. Fallback retrieval
   - If the graph yields no confident answer, the system falls back to vector search in Qdrant.
   - Context is retrieved and passed back through the LLM for a grounded answer.
8. Response delivery
   - The answer is returned to the UI and displayed as a briefing response.
   - Status updates keep the user informed of pipeline state.

## How to Run (Presentation Steps)
1. Start backend services:
   - `docker compose up --build`
2. Start the frontend:
   - `cd frontend`
   - `npm install`
   - `npm run dev`
3. Open the browser at the Vite URL and use the Signal Forge UI.

## Configuration Notes
- Backend environment variables
  - GOOGLE_API_KEY: Gemini access
  - NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
- Qdrant is exposed via Docker Compose and used by the API service.

## Key Features (Explainable in a Demo)
- Multimodal ingestion
  - Accepts files and transforms them into a concise knowledge summary.
- Dual retrieval engine
  - Graph queries for reasoning + vector search for semantic similarity.
- Knowledge graph construction
  - Entities and relationships mapped into Neo4j for structured queries.
- Fallback logic
  - If the graph cannot answer, vector search is used automatically.
- Briefing-style UI
  - A command-center layout with upload staging, pipeline progress, and chat.
- Prompt presets
  - One-click prompts for a clean and repeatable demo narrative.
- Status tracking
  - Clear pipeline state updates (ingest, forge, brief).

## UI Interaction Flow
1. Upload Card
   - Shows file name and size
   - Controls indexing
2. Pipeline Panel
   - Highlights ingest, forge, brief stages
3. Quick Prompts
   - Launches common demo questions
4. Briefing Stream
   - Shows user and AI turns with clear roles

## API Summary
- POST `/upload`
  - Input: file
  - Output: status + filename
  - Action: summarize file, index vectors, update graph
- POST `/chat`
  - Input: { query }
  - Output: { answer }
  - Action: graph-based QA, fallback to vector search if needed

## Demo Script (Suggested)
1. Open the UI and explain the "Signal Forge" idea.
2. Upload a sample file and mention the three pipeline steps.
3. Ask a question about entities or relationships.
4. Ask a second question that triggers the vector fallback.
5. Highlight the system behavior and the final answer quality.
6. Conclude with the hybrid retrieval advantage.

## Strengths
- Clear separation of structured reasoning and semantic recall.
- Deterministic pipeline stages make the demo predictable.
- Works for mixed content types thanks to multimodal analysis.

## Limitations
- Quality depends on LLM extraction fidelity.
- Large files increase processing latency.
- Graph extraction may be incomplete for noisy inputs.

## Future Enhancements
- Batch uploads and multi-file sessions
- Exportable reports or briefing PDFs
- More explicit confidence scoring in responses
- UI filters for graph exploration

## Notes for Presentation
- Emphasize the hybrid retrieval design (graph + vector).
- Explain the role of Gemini in multimodal understanding.
- Show how the UI supports a clear, story-driven demo.

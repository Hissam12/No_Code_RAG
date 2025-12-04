# GraphWeaver

GraphWeaver is a "No-Code RAG Builder" that automatically extracts Entities and Relationships from your documents to build a Knowledge Graph.

## Features
-   **Drag-and-Drop Ingestion:** Upload PDF or TXT files.
-   **Auto-Graph Construction:** Uses LLMs to extract nodes and edges.
-   **Hybrid RAG:** Combines Vector Search (ChromaDB) and Graph Search (NetworkX).
-   **Visual Canvas:** Explore your knowledge graph interactively.

## Setup

1.  **Prerequisites:**
    -   Python 3.11+
    -   Node.js 18+

2.  **Environment Variables:**
    -   Copy `backend/.env.example` to `backend/.env`
    -   Add your `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`.

3.  **Run:**
    ```bash
    ./run.sh
    ```
    -   Backend: http://localhost:8000
    -   Frontend: http://localhost:5173

## Tech Stack
-   **Backend:** FastAPI, NetworkX, ChromaDB, LiteLLM
-   **Frontend:** React, Vite, React Flow

from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from typing import Dict, Any
from app.core.graph_builder import GraphBuilder
from app.core.ingestion import IngestionService
from app.core.chunking import ChunkingService

router = APIRouter()

# Singleton instances
graph_builder = GraphBuilder()
ingestion_service = IngestionService()
chunking_service = ChunkingService()

@router.post("/process-document")
async def process_document(file: UploadFile = File(...)):
    """
    Ingests a document, chunks it, extracts graph data, and updates the graph.
    """
    try:
        # 1. Ingest
        text = await ingestion_service.process_file(file)
        
        # 2. Chunk
        chunks = chunking_service.chunk_text(text)
        
        # 3. Extract & Build Graph
        for chunk in chunks:
            graph_builder.extract_graph_from_text(chunk)
                
        return {"message": f"Processed {file.filename}, extracted {len(chunks)} chunks."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/graph")
async def get_graph():
    """Returns the current graph data for visualization."""
    return graph_builder.visualize_graph()

@router.post("/chat")
async def chat(query: str = Body(..., embed=True)):
    """
    Queries the graph using Anti-Hallucination logic.
    """
    try:
        answer = graph_builder.query_graph(query)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

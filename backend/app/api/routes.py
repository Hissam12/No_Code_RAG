from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from typing import Dict, Any
from app.core.graph_builder import GraphBuilder
from app.core.ingestion import IngestionService
from app.core.chunking import ChunkingService
from app.core.rag_service import RAGService
from pydantic import BaseModel

router = APIRouter()

# Singleton instances
graph_builder = GraphBuilder()
ingestion_service = IngestionService()
chunking_service = ChunkingService()
rag_service = RAGService()


# Pydantic models for request/response
class RAGQueryRequest(BaseModel):
    query: str
    n_results: int = 5


class RAGQueryResponse(BaseModel):
    answer: str
    sources: list[int]
    retrieved_chunks: list[Dict[str, Any]]
    question: str


# ============ GraphWeaver Endpoints ============

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


# ============ RAG System Endpoints ============

@router.post("/rag/ingest")
async def ingest_textbook():
    """
    Ingests the Computer Science textbook PDF into the RAG system.
    """
    try:
        import os
        pdf_path = os.path.join(
            os.path.dirname(__file__), 
            "..", "..", "data", "pdfs", "computer_science_textbook.pdf"
        )
        
        if not os.path.exists(pdf_path):
            raise HTTPException(
                status_code=404, 
                detail=f"PDF not found at {pdf_path}. Please ensure the textbook PDF is copied to backend/data/pdfs/"
            )
        
        result = rag_service.ingest_pdf(pdf_path)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rag/query", response_model=RAGQueryResponse)
async def query_rag(request: RAGQueryRequest):
    """
    Query the RAG system with a question.
    Returns an answer based on the textbook content.
    """
    try:
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        result = rag_service.query(request.query, n_results=request.n_results)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rag/stats")
async def get_rag_stats():
    """
    Get statistics about the RAG system.
    """
    try:
        stats = rag_service.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/rag/clear")
async def clear_rag():
    """
    Clear all documents from the RAG collection.
    Use with caution!
    """
    try:
        rag_service.clear_collection()
        return {"message": "RAG collection cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ Knowledge Graph Endpoints ============

from app.core.knowledge_graph import KnowledgeGraph

# Singleton instance
kg_service = KnowledgeGraph()


class KGIngestRequest(BaseModel):
    batch_size: int = 10
    use_fast: bool = False
    sampling_rate: float = 1.0


class KGQueryRequest(BaseModel):
    query: str
    hop_depth: int = 2


class KGAddTextRequest(BaseModel):
    text: str
    source: str = "manual"


@router.post("/kg/ingest")
async def ingest_kg(request: KGIngestRequest):
    """
    Ingest the Computer Science textbook into the knowledge graph.
    Uses batch processing for efficiency.
    """
    try:
        import os
        pdf_path = os.path.join(
            os.path.dirname(__file__), 
            "..", "..", "data", "pdfs", "computer_science_textbook.pdf"
        )
        
        if not os.path.exists(pdf_path):
            raise HTTPException(
                status_code=404, 
                detail="PDF not found. Please ensure the textbook PDF is in backend/data/pdfs/"
            )
        
        result = kg_service.ingest_document(
            pdf_path, 
            batch_size=request.batch_size,
            use_fast=request.use_fast,
            sampling_rate=request.sampling_rate
        )
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/kg/add-text")
async def add_text_to_kg(request: KGAddTextRequest):
    """Add a text chunk to the knowledge graph."""
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        result = kg_service.add_text(request.text, request.source)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/kg/query")
async def query_kg(request: KGQueryRequest):
    """
    Query the knowledge graph with multi-hop traversal.
    """
    try:
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        result = kg_service.query(request.query, hop_depth=request.hop_depth)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kg/stats")
async def get_kg_stats():
    """Get knowledge graph statistics."""
    try:
        return kg_service.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kg/graph")
async def get_kg_visualization():
    """Get graph data for visualization."""
    try:
        return kg_service.visualize()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/kg/save")
async def save_kg():
    """Save knowledge graph to disk."""
    try:
        filepath = kg_service.save()
        return {"message": "Graph saved", "path": filepath}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/kg/load")
async def load_kg():
    """Load knowledge graph from disk."""
    try:
        success = kg_service.load()
        if success:
            return {"message": "Graph loaded", "stats": kg_service.get_stats()}
        else:
            return {"message": "No saved graph found"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/kg/clear")
async def clear_kg():
    """Clear the knowledge graph."""
    try:
        kg_service.clear()
        return {"message": "Knowledge graph cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

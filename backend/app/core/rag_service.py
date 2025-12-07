import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from app.core.vector_store import VectorStore
from app.core.chunking import ChunkingService
from app.core.llm_service import LLMService

# Load environment variables
load_dotenv()


class RAGService:
    """
    Retrieval-Augmented Generation service for querying documents.
    Integrates PDF ingestion, chunking, vector search, and LLM generation.
    """
    
    def __init__(self, collection_name: str = "computer_science_textbook"):
        """
        Initialize RAG service with dedicated collection.
        
        Args:
            collection_name: Name of the ChromaDB collection to use
        """
        self.collection_name = collection_name
        self.vector_store = VectorStore(collection_name=collection_name)
        self.chunking_service = ChunkingService()
        self.llm_service = LLMService()
        
    def ingest_pdf(self, pdf_path: str, chunk_size: int = 1000, overlap: int = 200) -> Dict[str, Any]:
        """
        Ingests a PDF file into the vector database.
        
        Args:
            pdf_path: Path to the PDF file
            chunk_size: Size of text chunks
            overlap: Overlap between chunks for context preservation
            
        Returns:
            Dictionary with ingestion statistics
        """
        # Load PDF
        loader = PyPDFLoader(pdf_path)
        pages = loader.load()
        
        print(f"Loaded {len(pages)} pages from {pdf_path}")
        
        # Process each page
        all_chunks = []
        all_metadatas = []
        all_ids = []
        chunk_counter = 0
        
        for page_num, page in enumerate(pages, start=1):
            # Extract text from page
            page_text = page.page_content
            
            # Skip empty pages
            if not page_text.strip():
                continue
            
            # Chunk the page text
            chunks = self.chunking_service.chunk_text(
                page_text, 
                chunk_size=chunk_size, 
                overlap=overlap
            )
            
            # Create metadata for each chunk
            for i, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                all_metadatas.append({
                    "page": page_num,
                    "chunk_index": i,
                    "source": os.path.basename(pdf_path)
                })
                all_ids.append(f"page_{page_num}_chunk_{i}")
                chunk_counter += 1
        
        # Add all chunks to vector store
        print(f"Adding {chunk_counter} chunks to vector store...")
        self.vector_store.add_documents(
            documents=all_chunks,
            metadatas=all_metadatas,
            ids=all_ids
        )
        
        return {
            "status": "success",
            "pages": len(pages),
            "chunks": chunk_counter,
            "collection": self.collection_name
        }
    
    def query(self, question: str, n_results: int = 5) -> Dict[str, Any]:
        """
        Query the RAG system with a question.
        Retrieves relevant chunks and generates an answer.
        
        Args:
            question: User's question
            n_results: Number of relevant chunks to retrieve
            
        Returns:
            Dictionary with answer, sources, and retrieved chunks
        """
        # Retrieve relevant chunks
        results = self.vector_store.query_similar(question, n_results=n_results)
        
        if not results:
            return {
                "answer": "I couldn't find any relevant information in the textbook to answer your question.",
                "sources": [],
                "retrieved_chunks": []
            }
        
        # Build context from retrieved chunks
        context_parts = []
        sources = []
        
        for i, result in enumerate(results, start=1):
            page_num = result["metadata"].get("page", "Unknown")
            chunk_text = result["document"]
            
            context_parts.append(f"[Source {i} - Page {page_num}]:\n{chunk_text}\n")
            
            if page_num not in sources:
                sources.append(page_num)
        
        context = "\n".join(context_parts)
        
        # Generate answer using LLM
        answer = self.llm_service.generate_answer(question, context)
        
        # Format retrieved chunks for response
        retrieved_chunks = [
            {
                "page": result["metadata"].get("page", "Unknown"),
                "text": result["document"][:200] + "..." if len(result["document"]) > 200 else result["document"],
                "distance": result["distance"]
            }
            for result in results
        ]
        
        return {
            "answer": answer,
            "sources": sorted(sources),
            "retrieved_chunks": retrieved_chunks,
            "question": question
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the RAG system.
        
        Returns:
            Dictionary with collection statistics
        """
        doc_count = self.vector_store.get_document_count()
        
        return {
            "collection_name": self.collection_name,
            "document_count": doc_count,
            "status": "active" if doc_count > 0 else "empty"
        }
    
    def clear_collection(self):
        """Delete all documents from the collection."""
        self.vector_store.delete_collection()
        # Reinitialize the collection
        self.vector_store = VectorStore(collection_name=self.collection_name)

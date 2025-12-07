import os
from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings

# Load environment variables
load_dotenv()


def get_embeddings():
    """
    Returns the appropriate embedding model based on environment configuration.
    Supports Ollama (local) and OpenAI.
    """
    provider = os.getenv("EMBEDDING_PROVIDER", "ollama").lower()
    
    if provider == "ollama":
        from langchain_ollama import OllamaEmbeddings
        model = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        return OllamaEmbeddings(
            model=model,
            base_url=base_url
        )
    else:
        # Fallback to OpenAI
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(model="text-embedding-3-small")


class VectorStore:
    def __init__(self, collection_name: str = "graphweaver"):
        self.collection_name = collection_name
        self.embeddings = get_embeddings()
        
        # Initialize ChromaDB with persistent storage
        persist_directory = os.path.join(os.path.dirname(__file__), "..", "..", "data", "chroma_db")
        os.makedirs(persist_directory, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def add_documents(self, documents: list[str], metadatas: list[dict], ids: list[str]):
        """Adds documents to the vector store."""
        # Generate embeddings using the configured embedding model
        embeddings = self.embeddings.embed_documents(documents)
        
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )

    def query_similar(self, query: str, n_results: int = 5) -> list[dict]:
        """Finds similar documents and returns their content and metadata."""
        # Generate query embedding
        query_embedding = self.embeddings.embed_query(query)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        formatted_results = []
        if results and results.get("ids"):
            for i, doc_id in enumerate(results["ids"][0]):
                formatted_results.append({
                    "id": doc_id,
                    "document": results["documents"][0][i] if results.get("documents") else "",
                    "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                    "distance": results["distances"][0][i] if results.get("distances") else 0
                })
        
        return formatted_results
    
    def get_document_count(self) -> int:
        """Returns the number of documents in the collection."""
        return self.collection.count()
    
    def delete_collection(self):
        """Deletes the collection."""
        self.client.delete_collection(name=self.collection_name)


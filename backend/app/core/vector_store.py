import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any

class VectorStore:
    def __init__(self, collection_name: str = "graph_nodes"):
        self.client = chromadb.Client(Settings(
            is_persistent=True,
            persist_directory="./chroma_db"
        ))
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add_documents(self, documents: List[str], metadatas: List[Dict[str, Any]], ids: List[str]):
        """Adds documents to the vector store."""
        self.collection.upsert(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    def query_similar(self, query: str, n_results: int = 5) -> List[str]:
        """Finds similar documents and returns their IDs."""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results["ids"][0] if results["ids"] else []

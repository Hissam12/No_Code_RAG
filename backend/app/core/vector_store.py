import os
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone

class VectorStore:
    def __init__(self, index_name: str = None):
        self.index_name = index_name or os.getenv("PINECONE_INDEX_NAME")
        if not self.index_name:
            raise ValueError("PINECONE_INDEX_NAME not found in environment variables")
            
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        
        # Initialize Pinecone
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        
        # Initialize Vector Store
        self.vector_store = PineconeVectorStore(
            index_name=self.index_name,
            embedding=self.embeddings
        )

    def add_documents(self, documents: list[str], metadatas: list[dict], ids: list[str]):
        """Adds documents to the vector store."""
        self.vector_store.add_texts(
            texts=documents,
            metadatas=metadatas,
            ids=ids
        )

    def query_similar(self, query: str, n_results: int = 5) -> list[str]:
        """Finds similar documents and returns their IDs."""
        results = self.vector_store.similarity_search(
            query=query,
            k=n_results
        )
        return [doc.metadata.get("id") for doc in results if doc.metadata.get("id")]

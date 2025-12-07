import os
import json
from typing import List, Tuple
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.models.schemas import Node, Edge

# Load environment variables
load_dotenv()

def get_llm():
    """
    Returns the appropriate LLM based on environment configuration.
    Supports Ollama (local) and OpenAI.
    """
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    
    if provider == "ollama":
        from langchain_ollama import ChatOllama
        model = os.getenv("OLLAMA_MODEL", "qwen2.5:20b")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        return ChatOllama(
            model=model,
            base_url=base_url,
            temperature=0
        )
    else:
        # Fallback to OpenAI
        from langchain_openai import ChatOpenAI
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        return ChatOpenAI(model=model, temperature=0)


class LLMService:
    def __init__(self, model: str = None):
        self.llm = get_llm()

    def extract_graph_data(self, text_chunk: str) -> Tuple[List[Node], List[Edge]]:
        """
        Extracts entities and relationships from a text chunk using an LLM.
        Returns a tuple of (nodes, edges).
        """
        parser = JsonOutputParser()
        
        prompt = PromptTemplate(
            template="""
            You are a Knowledge Graph extraction engine.
            Analyze the following text and extract:
            1. Entities (Nodes): Person, Company, Date, Location, Concept, etc.
            2. Relationships (Edges): Founded, Signed, Sued, Located_In, etc.

            Return ONLY a JSON object with the following structure:
            {{
                "nodes": [
                    {{"id": "unique_id", "label": "Name", "type": "Type", "properties": {{}} }}
                ],
                "edges": [
                    {{"source": "source_id", "target": "target_id", "relation": "RELATION_TYPE", "properties": {{}} }}
                ]
            }}

            Text:
            {text}
            """,
            input_variables=["text"],
        )

        chain = prompt | self.llm | parser

        try:
            data = chain.invoke({"text": text_chunk})
            
            nodes = []
            for n in data.get("nodes", []):
                nodes.append(Node(**n))
                
            edges = []
            for e in data.get("edges", []):
                edges.append(Edge(**e))
                
            return nodes, edges

        except Exception as e:
            print(f"Error extracting graph data: {e}")
            return [], []

    def generate_answer(self, query: str, context: str) -> str:
        """Generates an answer to a user query based on the provided context."""
        prompt = PromptTemplate(
            template="""
            Answer the user's question based ONLY on the following context.
            Include citations like [Source: DocName, Page X] if available in the context.
            
            Context:
            {context}
            
            Question:
            {query}
            """,
            input_variables=["context", "query"],
        )
        
        chain = prompt | self.llm
        response = chain.invoke({"context": context, "query": query})
        return response.content


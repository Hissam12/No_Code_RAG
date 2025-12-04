import json
from typing import List, Tuple
from litellm import completion
from app.models.schemas import Node, Edge

class LLMService:
    def __init__(self, model: str = "gpt-3.5-turbo"):
        self.model = model

    def extract_graph_data(self, text_chunk: str) -> Tuple[List[Node], List[Edge]]:
        """
        Extracts entities and relationships from a text chunk using an LLM.
        Returns a tuple of (nodes, edges).
        """
        prompt = f"""
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
        {text_chunk}
        """

        try:
            response = completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            data = json.loads(content)
            
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
        prompt = f"""
        Answer the user's question based ONLY on the following context.
        Include citations like [Source: DocName, Page X] if available in the context.
        
        Context:
        {context}
        
        Question:
        {query}
        """
        
        response = completion(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

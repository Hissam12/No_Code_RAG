import networkx as nx
import json
from typing import List, Dict, Any, Tuple
from litellm import completion
from app.core.vector_store import VectorStore
from app.models.schemas import Node, Edge, GraphData

class GraphBuilder:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.vector_store = VectorStore()
        self.model = "gpt-4o-mini" # Or "llama-3-8b" via LiteLLM config

    def extract_graph_from_text(self, text: str):
        """
        Extracts Nodes and Edges from text using an LLM and updates the graph.
        """
        prompt = f"""
        Analyze the following text and extract a Knowledge Graph.
        Return ONLY a JSON object with this exact structure:
        {{
            "nodes": [{{"id": "EntityName", "type": "Person/Company/Location/Date/Concept"}}],
            "edges": [{{"source": "EntityA", "target": "EntityB", "relationship": "FOUNDED/SIGNED/LOCATED_IN/etc"}}]
        }}
        
        Text:
        {text}
        """

        try:
            response = completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            data = json.loads(content)

            # Update NetworkX and Vector Store
            for n in data.get("nodes", []):
                node_id = n["id"]
                node_type = n.get("type", "Entity")
                self.graph.add_node(node_id, type=node_type, label=node_id)
                
                # Add to Vector Store
                self.vector_store.add_documents(
                    documents=[f"{node_id} ({node_type})"],
                    metadatas=[{"type": node_type}],
                    ids=[node_id]
                )

            for e in data.get("edges", []):
                self.graph.add_edge(e["source"], e["target"], relation=e["relationship"])

        except Exception as e:
            print(f"Error extracting graph: {e}")

    def visualize_graph(self) -> Dict[str, Any]:
        """
        Returns graph data in a format compatible with frontend visualizers (e.g., React Flow).
        """
        nodes = []
        for n, attrs in self.graph.nodes(data=True):
            nodes.append({
                "id": str(n),
                "label": attrs.get("label", str(n)),
                "type": attrs.get("type", "default")
            })

        edges = []
        for u, v, attrs in self.graph.edges(data=True):
            edges.append({
                "source": str(u),
                "target": str(v),
                "relation": attrs.get("relation", "related_to")
            })

        return {"nodes": nodes, "edges": edges}

    def query_graph(self, question: str) -> str:
        """
        Anti-Hallucination Retrieval:
        1. Find entities in the question.
        2. Get graph neighbors (context).
        3. Answer ONLY using context.
        """
        # 1. Find relevant nodes via Vector Search
        # (Simple approach: search the whole question against node index)
        relevant_node_ids = self.vector_store.query_similar(question, n_results=3)
        
        if not relevant_node_ids:
            return "I couldn't find any relevant entities in the knowledge graph to answer your question."

        # 2. Build Context (1-hop neighbors)
        context_lines = []
        for node_id in relevant_node_ids:
            if self.graph.has_node(node_id):
                neighbors = self.graph.neighbors(node_id)
                for neighbor in neighbors:
                    edge_data = self.graph.get_edge_data(node_id, neighbor)
                    relation = edge_data.get("relation", "related to")
                    context_lines.append(f"{node_id} --[{relation}]--> {neighbor}")
        
        context = "\n".join(context_lines)
        
        if not context:
             return "I found relevant entities but no relationships in the graph."

        # 3. LLM Answer with Constraints
        prompt = f"""
        You are a helpful assistant answering questions based on a Knowledge Graph.
        
        Context (Graph Relationships):
        {context}
        
        Question: {question}
        
        Constraint: Answer ONLY using the provided graph context. If the relationship is not found, say "I don't know".
        Do not use outside knowledge.
        """
        
        response = completion(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

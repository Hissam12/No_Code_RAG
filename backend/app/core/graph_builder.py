import networkx as nx
from typing import Dict, Any
from app.core.vector_store import VectorStore
from app.core.llm_service import LLMService

class GraphBuilder:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.vector_store = VectorStore()
        self.llm_service = LLMService()

    def extract_graph_from_text(self, text: str):
        """
        Extracts Nodes and Edges from text using LLMService and updates the graph.
        """
        nodes, edges = self.llm_service.extract_graph_data(text)

        # Update NetworkX and Vector Store
        for node in nodes:
            self.graph.add_node(node.id, type=node.type, label=node.label)
            
            # Add to Vector Store
            self.vector_store.add_documents(
                documents=[f"{node.id} ({node.type})"],
                metadatas=[{"type": node.type, "id": node.id}],
                ids=[node.id]
            )

        for edge in edges:
            self.graph.add_edge(edge.source, edge.target, relation=edge.relation)

    def visualize_graph(self) -> Dict[str, Any]:
        """
        Returns graph data in a format compatible with frontend visualizers.
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

        # 3. LLM Answer via Service
        return self.llm_service.generate_answer(question, context)

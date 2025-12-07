"""
Efficient Knowledge Graph Engine
Optimized for M3 Max with 128GB RAM

Features:
- Batch LLM extraction for parallel processing
- Entity resolution using embeddings
- Persistent storage (JSON)
- Incremental document updates
"""

import os
import json
import hashlib
from typing import List, Dict, Any, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import networkx as nx
from langchain_community.document_loaders import PyPDFLoader

from app.core.vector_store import VectorStore, get_embeddings
from app.core.chunking import ChunkingService
from app.models.schemas import Node, Edge

load_dotenv()

# Performance configuration - optimized for M3 Max
BATCH_SIZE = int(os.getenv("KG_BATCH_SIZE", "10"))
MAX_PARALLEL_CALLS = int(os.getenv("KG_MAX_PARALLEL", "4"))
ENTITY_SIMILARITY_THRESHOLD = float(os.getenv("KG_ENTITY_THRESHOLD", "0.85"))
DEFAULT_HOP_DEPTH = int(os.getenv("KG_HOP_DEPTH", "2"))


class KnowledgeGraph:
    """
    High-performance knowledge graph with batch processing and persistence.
    """
    
    def __init__(self, collection_name: str = "knowledge_graph"):
        self.collection_name = collection_name
        self.graph = nx.DiGraph()
        self.vector_store = VectorStore(collection_name=collection_name)
        self.embeddings = get_embeddings()
        self.chunking_service = ChunkingService()
        
        # Entity cache for deduplication
        self._entity_cache: Dict[str, str] = {}  # label -> canonical_id
        self._entity_embeddings: Dict[str, List[float]] = {}
        
        # Storage path
        self.storage_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "kg")
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # LLM for extraction
        self._init_llm()
        
        # Auto-load if exists
        if os.path.exists(os.path.join(self.storage_dir, f"{self.collection_name}.json")):
            print(f"Loading existing knowledge graph from {self.storage_dir}")
            self.load()
    
    def _init_llm(self):
        """Initialize LLM for entity extraction."""
        provider = os.getenv("LLM_PROVIDER", "ollama").lower()
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        if provider == "ollama":
            from langchain_ollama import ChatOllama
            # Default model for extraction
            model = os.getenv("OLLAMA_MODEL", "gpt-oss:20b")
            self.llm = ChatOllama(model=model, base_url=base_url, temperature=0)
        else:
            from langchain_openai import ChatOpenAI
            self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        
        # Fast model: Use OpenAI gpt-4o-mini (cloud API = ~50x faster than local 20B)
        # Reads OPENAI_API_KEY from environment automatically
        from langchain_openai import ChatOpenAI
        self.fast_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    def _generate_entity_id(self, label: str, entity_type: str) -> str:
        """Generate consistent ID for an entity."""
        normalized = f"{entity_type}:{label.lower().strip()}"
        return hashlib.md5(normalized.encode()).hexdigest()[:12]
    
    def _extract_entities_from_chunk(self, text: str, source: str = "", use_fast: bool = False) -> Tuple[List[Node], List[Edge]]:
        """Extract entities and relationships from a single text chunk."""
        prompt = f"""Extract key entities and relationships. Return ONLY valid JSON, no explanation.

Text: {text[:1500]}

Format: {{"nodes": [{{"id": "short_id", "label": "Name", "type": "Concept|Technology|Process"}}], "edges": [{{"source": "id1", "target": "id2", "relation": "RELATES_TO"}}]}}"""

        try:
            llm_to_use = self.fast_llm if use_fast else self.llm
            response = llm_to_use.invoke(prompt)
            content = response.content
            
            # Parse JSON from response
            start = content.find('{')
            end = content.rfind('}') + 1
            if start >= 0 and end > start:
                data = json.loads(content[start:end])
                
                nodes = []
                llm_id_map = {}  # Map LLM-generated ID to our hashed ID
                
                for n in data.get("nodes", []):
                    llm_id = n.get("id")
                    node_id = self._generate_entity_id(n.get("label", ""), n.get("type", "entity"))
                    
                    if llm_id:
                        llm_id_map[llm_id] = node_id
                    
                    nodes.append(Node(
                        id=node_id,
                        label=n.get("label", ""),
                        type=n.get("type", "entity"),
                        properties={"source": source}
                    ))
                
                edges = []
                for e in data.get("edges", []):
                    source_llm_id = e.get("source", "")
                    target_llm_id = e.get("target", "")
                    
                    # Translate LLM IDs to our hashed IDs
                    source_id = llm_id_map.get(source_llm_id, source_llm_id)
                    target_id = llm_id_map.get(target_llm_id, target_llm_id)
                    
                    edges.append(Edge(
                        source=source_id,
                        target=target_id,
                        relation=e.get("relation", "RELATES_TO")
                    ))
                
                return nodes, edges
        except Exception as e:
            print(f"Extraction error: {e}")
        
        return [], []
    
    def _extract_batch(self, chunks: List[Tuple[str, str]], use_fast: bool = False) -> List[Tuple[List[Node], List[Edge]]]:
        """
        Extract entities from multiple chunks in parallel.
        
        Args:
            chunks: List of (text, source) tuples
            use_fast: Use fast model for extraction
        
        Returns:
            List of (nodes, edges) tuples
        """
        results = []
        max_workers = 8 if use_fast else MAX_PARALLEL_CALLS  # More parallel for fast model
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._extract_entities_from_chunk, text, source, use_fast): i
                for i, (text, source) in enumerate(chunks)
            }
            
            # Collect results in order
            result_map = {}
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    result_map[idx] = future.result()
                except Exception as e:
                    print(f"Batch extraction error at {idx}: {e}")
                    result_map[idx] = ([], [])
            
            results = [result_map[i] for i in range(len(chunks))]
        
        return results
    
    def _resolve_entity(self, node: Node) -> str:
        """
        Resolve entity to canonical ID using embedding similarity.
        Returns existing ID if similar entity found, otherwise returns node's ID.
        """
        # Check cache first
        cache_key = f"{node.type}:{node.label.lower()}"
        if cache_key in self._entity_cache:
            return self._entity_cache[cache_key]
        
        # If no entities yet, this is canonical
        if not self._entity_embeddings:
            self._entity_cache[cache_key] = node.id
            self._entity_embeddings[node.id] = self.embeddings.embed_query(node.label)
            return node.id
        
        # Compute embedding and find similar
        node_embedding = self.embeddings.embed_query(node.label)
        
        max_similarity = 0
        best_match = None
        
        for entity_id, entity_emb in self._entity_embeddings.items():
            # Cosine similarity
            dot = sum(a * b for a, b in zip(node_embedding, entity_emb))
            norm_a = sum(a * a for a in node_embedding) ** 0.5
            norm_b = sum(b * b for b in entity_emb) ** 0.5
            similarity = dot / (norm_a * norm_b) if norm_a and norm_b else 0
            
            if similarity > max_similarity:
                max_similarity = similarity
                best_match = entity_id
        
        if max_similarity >= ENTITY_SIMILARITY_THRESHOLD and best_match:
            self._entity_cache[cache_key] = best_match
            return best_match
        
        # New entity
        self._entity_cache[cache_key] = node.id
        self._entity_embeddings[node.id] = node_embedding
        return node.id
    
    def _add_to_graph(self, nodes: List[Node], edges: List[Edge]) -> Dict[str, str]:
        """
        Add nodes and edges to graph with entity resolution.
        Returns mapping of original IDs to resolved IDs.
        """
        id_mapping = {}
        
        # Add nodes with resolution
        for node in nodes:
            resolved_id = self._resolve_entity(node)
            id_mapping[node.id] = resolved_id
            
            if not self.graph.has_node(resolved_id):
                self.graph.add_node(
                    resolved_id,
                    label=node.label,
                    type=node.type,
                    properties=node.properties
                )
                
                # Add to vector store for search
                self.vector_store.add_documents(
                    documents=[f"{node.label} ({node.type})"],
                    metadatas=[{"type": node.type, "label": node.label}],
                    ids=[resolved_id]
                )
        
        # Add edges with resolved IDs
        for edge in edges:
            source = id_mapping.get(edge.source, edge.source)
            target = id_mapping.get(edge.target, edge.target)
            
            if self.graph.has_node(source) and self.graph.has_node(target):
                self.graph.add_edge(source, target, relation=edge.relation)
        
        return id_mapping
    
    def ingest_document(self, pdf_path: str, batch_size: int = BATCH_SIZE, use_fast: bool = False, sampling_rate: float = 1.0) -> Dict[str, Any]:
        """
        Ingest a PDF document with batch processing.
        
        Args:
            pdf_path: Path to PDF file
            batch_size: Number of chunks per batch
            use_fast: Use fast model (gpt-4o-mini) for extraction
            sampling_rate: Percentage of chunks to process (0.0 to 1.0) to save costs
        """
        # Load PDF
        loader = PyPDFLoader(pdf_path)
        pages = loader.load()
        
        print(f"Loaded {len(pages)} pages from {pdf_path}")
        
        # Chunk all pages
        all_chunks = []
        for page_num, page in enumerate(pages, start=1):
            text = page.page_content
            if not text.strip():
                continue
            
            chunks = self.chunking_service.chunk_text(text, chunk_size=800, overlap=150)
            for chunk in chunks:
                all_chunks.append((chunk, f"page_{page_num}"))
        
        # Apply sampling if requested
        if sampling_rate < 1.0:
            import random
            # Deterministic sampling for reproducibility
            random.seed(42) 
            sample_size = int(len(all_chunks) * sampling_rate)
            all_chunks = random.sample(all_chunks, sample_size)
            print(f"Sampled {len(all_chunks)} chunks ({int(sampling_rate*100)}%) for cost optimization")
        
        print(f"Processing {len(all_chunks)} chunks in batches of {batch_size} (Fast Mode: {use_fast})")
        
        # Process in batches
        total_nodes = 0
        total_edges = 0
        
        for i in range(0, len(all_chunks), batch_size):
            batch = all_chunks[i:i + batch_size]
            print(f"Processing batch {i // batch_size + 1}/{(len(all_chunks) + batch_size - 1) // batch_size}")
            
            results = self._extract_batch(batch, use_fast=use_fast)
            
            for nodes, edges in results:
                self._add_to_graph(nodes, edges)
                total_nodes += len(nodes)
                total_edges += len(edges)
        
        # Auto-save after ingestion
        self.save()
        print("Graph saved to disk after ingestion")
        
        return {
            "status": "success",
            "pages": len(pages),
            "chunks": len(all_chunks),
            "nodes_extracted": total_nodes,
            "edges_extracted": total_edges,
            "unique_nodes": self.graph.number_of_nodes(),
            "unique_edges": self.graph.number_of_edges()
        }
    
    def add_text(self, text: str, source: str = "manual") -> Dict[str, Any]:
        """Add a single text chunk to the graph."""
        nodes, edges = self._extract_entities_from_chunk(text, source)
        self._add_to_graph(nodes, edges)
        
        return {
            "nodes_added": len(nodes),
            "edges_added": len(edges),
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges()
        }
    
    def query(self, question: str, hop_depth: int = DEFAULT_HOP_DEPTH) -> Dict[str, Any]:
        """
        Query the knowledge graph with multi-hop traversal.
        
        Args:
            question: User question
            hop_depth: Number of hops to traverse
        
        Returns:
            Answer with graph context
        """
        # Find relevant nodes via vector search
        results = self.vector_store.query_similar(question, n_results=5)
        
        if not results:
            return {
                "answer": "No relevant entities found in the knowledge graph.",
                "nodes": [],
                "edges": [],
                "context": ""
            }
        
        # Build context with multi-hop traversal
        visited_nodes = set()
        context_edges = []
        
        for result in results:
            node_id = result["id"]
            if not self.graph.has_node(node_id):
                continue
            
            # BFS traversal
            queue = [(node_id, 0)]
            while queue:
                current, depth = queue.pop(0)
                if current in visited_nodes or depth > hop_depth:
                    continue
                visited_nodes.add(current)
                
                # Get neighbors
                for neighbor in self.graph.neighbors(current):
                    edge_data = self.graph.get_edge_data(current, neighbor)
                    relation = edge_data.get("relation", "related_to")
                    
                    current_label = self.graph.nodes[current].get("label", current)
                    neighbor_label = self.graph.nodes[neighbor].get("label", neighbor)
                    
                    context_edges.append(f"{current_label} --[{relation}]--> {neighbor_label}")
                    
                    if depth + 1 <= hop_depth:
                        queue.append((neighbor, depth + 1))
        
        context = "\n".join(context_edges) if context_edges else "No relationships found."
        
        # Generate answer using LLM
        if context_edges:
            prompt = f"""Based on this knowledge graph context, answer the question.

Context:
{context}

Question: {question}

Answer based ONLY on the context provided. If the context doesn't contain the answer, say so."""

            response = self.llm.invoke(prompt)
            answer = response.content
        else:
            answer = "Found nodes but no relationships in the knowledge graph."
        
        # Get node details
        nodes_data = []
        for node_id in visited_nodes:
            if self.graph.has_node(node_id):
                node = self.graph.nodes[node_id]
                nodes_data.append({
                    "id": node_id,
                    "label": node.get("label", node_id),
                    "type": node.get("type", "entity")
                })
        
        return {
            "answer": answer,
            "nodes": nodes_data,
            "edges": context_edges,
            "context": context,
            "hops": hop_depth
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge graph statistics."""
        # Count entity types
        type_counts = {}
        for _, attrs in self.graph.nodes(data=True):
            entity_type = attrs.get("type", "unknown")
            type_counts[entity_type] = type_counts.get(entity_type, 0) + 1
        
        # Count relationship types
        relation_counts = {}
        for _, _, attrs in self.graph.edges(data=True):
            relation = attrs.get("relation", "unknown")
            relation_counts[relation] = relation_counts.get(relation, 0) + 1
        
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "entity_types": type_counts,
            "relation_types": relation_counts,
            "density": nx.density(self.graph) if self.graph.number_of_nodes() > 0 else 0,
            "components": nx.number_weakly_connected_components(self.graph) if self.graph.number_of_nodes() > 0 else 0
        }
    
    def visualize(self) -> Dict[str, Any]:
        """Return graph data for frontend visualization."""
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
    
    def save(self) -> str:
        """Save graph and entity cache to disk."""
        filepath = os.path.join(self.storage_dir, f"{self.collection_name}.json")
        
        data = {
            "nodes": [
                {"id": n, **attrs}
                for n, attrs in self.graph.nodes(data=True)
            ],
            "edges": [
                {"source": u, "target": v, **attrs}
                for u, v, attrs in self.graph.edges(data=True)
            ],
            "entity_cache": self._entity_cache
        }
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        
        return filepath
    
    def load(self) -> bool:
        """Load graph from disk."""
        filepath = os.path.join(self.storage_dir, f"{self.collection_name}.json")
        
        if not os.path.exists(filepath):
            return False
        
        with open(filepath, "r") as f:
            data = json.load(f)
        
        # Rebuild graph
        self.graph.clear()
        
        for node in data.get("nodes", []):
            node_id = node.pop("id")
            self.graph.add_node(node_id, **node)
        
        for edge in data.get("edges", []):
            source = edge.pop("source")
            target = edge.pop("target")
            self.graph.add_edge(source, target, **edge)
        
        self._entity_cache = data.get("entity_cache", {})
        
        return True
    
    def clear(self):
        """Clear the graph and vector store."""
        self.graph.clear()
        self._entity_cache.clear()
        self._entity_embeddings.clear()
        self.vector_store.delete_collection()
        self.vector_store = VectorStore(collection_name=self.collection_name)

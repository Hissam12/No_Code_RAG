from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class Node(BaseModel):
    id: str
    label: str
    type: str = "entity"
    properties: Dict[str, Any] = Field(default_factory=dict)

class Edge(BaseModel):
    source: str
    target: str
    relation: str
    properties: Dict[str, Any] = Field(default_factory=dict)

class GraphData(BaseModel):
    nodes: List[Node]
    edges: List[Edge]

class SearchResult(BaseModel):
    answer: str
    citations: List[str]
    graph_context: Optional[GraphData] = None

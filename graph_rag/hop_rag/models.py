"""HopRAG Data Models."""

from dataclasses import dataclass, field
from typing import Dict, List, Any


@dataclass
class HopResult:
    node_id: str
    node_type: str
    node_data: Dict[str, Any]
    visit_count: int = 1
    similarity_score: float = 0.0
    hop_path: List[str] = field(default_factory=list)

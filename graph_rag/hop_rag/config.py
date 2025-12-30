"""HopRAG Configuration."""

import os
from dataclasses import dataclass


@dataclass
class HopRAGConfig:
    enabled: bool = True
    n_hops: int = 2
    top_k: int = 5
    similarity_weight: float = 0.5
    prune_threshold: float = 0.3
    max_neighbors_per_hop: int = 3
    use_llm_reasoning: bool = True
    llm_model: str = "llama-3.3-70b-versatile"
    log_level: str = "INFO"

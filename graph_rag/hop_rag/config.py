import os
from dataclasses import dataclass


@dataclass
class HopRAGConfig:
    enabled: bool = True
    n_hops: int = 3  # 3-hop traversal for deeper reasoning
    top_k: int = 10
    similarity_weight: float = 0.5
    prune_threshold: float = 0.2
    max_neighbors_per_hop: int = 5  # More neighbors per hop
    
    # MORE LLM reasoning
    use_llm_reasoning: bool = True
    llm_model: str = "llama-3.1-8b-instant"
    log_level: str = "INFO"
    
    # Allow more LLM calls for deeper reasoning
    fast_mode: bool = True
    fast_mode_threshold: float = 0.9  # Almost always use LLM
    max_llm_calls_per_query: int = 5  # 5 LLM calls allowed
    use_async: bool = True
    parallel_workers: int = 10
    early_termination_count: int = 8  # Rarely skip
    
    # Speed guards
    skip_multi_hop: bool = False
    max_total_time_seconds: int = 30

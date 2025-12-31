import os
from dataclasses import dataclass, field
from typing import Optional

# Determine project root dynamically
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DEFAULT_DATA_DIR = os.path.join(PROJECT_ROOT, "processed_data")


@dataclass
class LLMConfig:
    provider: str = "groq"
    model_name: str = "qwen/qwen3-32b"
    temperature: float = 0.0
    api_key: Optional[str] = None
    
    def __post_init__(self):
        if not self.api_key:
            key_map = {"groq": "GROQ_API_KEY", "google": "GOOGLE_API_KEY", "openai": "OPENAI_API_KEY"}
            self.api_key = os.getenv(key_map.get(self.provider, "GROQ_API_KEY"))


@dataclass
class GraphConfig:
    data_dir: str = ""
    graph_file: str = "clinical_trial_graph.graphml"
    auto_build: bool = True
    
    def __post_init__(self):
        if not self.data_dir:
            self.data_dir = DEFAULT_DATA_DIR
    
    @property
    def graph_path(self) -> str:
        return os.path.join(PROJECT_ROOT, "crag", self.graph_file)


@dataclass
class CRAGConfig:
    # Core settings
    enabled: bool = True
    n_hops: int = 3
    top_k: int = 15
    batch_size: int = 15
    
    # Scoring
    similarity_weight: float = 0.5
    prune_threshold: float = 0.2
    max_neighbors_per_hop: int = 5
    
    # LLM settings
    use_llm_reasoning: bool = True
    llm_model: str = "qwen/qwen3-32b"
    log_level: str = "INFO"
    
    # Budget controls
    fast_mode: bool = False
    fast_mode_threshold: float = 0.95
    max_llm_calls_per_query: int = 10
    max_total_time_seconds: int = 45
    
    # Async
    use_async: bool = True
    parallel_workers: int = 10
    early_termination_count: int = 5
    
    # Novel features
    use_cot_guided_traversal: bool = True  # Chain-of-Thought Reasoning
    use_llm_selection: bool = True         # Data-Aware Pruning
    selection_batch_size: int = 20
    max_candidates_to_score: int = 40
    beam_width: int = 20
    
    skip_multi_hop: bool = False


@dataclass
class AgentConfig:
    llm: LLMConfig = field(default_factory=LLMConfig)
    graph: GraphConfig = field(default_factory=GraphConfig)
    crag: CRAGConfig = field(default_factory=CRAGConfig)
    verbose: bool = False
    max_iterations: int = 15


def get_default_config() -> AgentConfig:
    return AgentConfig()

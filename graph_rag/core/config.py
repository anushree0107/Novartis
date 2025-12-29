"""Configuration for Graph RAG Agent."""

import os
from dataclasses import dataclass, field
from typing import Optional

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DEFAULT_DATA_DIR = os.path.join(PROJECT_ROOT, "processed_data")


@dataclass
class LLMConfig:
    provider: str = "groq"
    model_name: str = "openai/gpt-oss-120b"
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
        return os.path.join(os.path.dirname(SCRIPT_DIR), "graph_rag", self.graph_file)

# Import HopRAGConfig from the hop_rag package
try:
    from ..hop_rag.config import HopRAGConfig
except ImportError:
    try:
        from graph_rag.hop_rag.config import HopRAGConfig
    except ImportError:
        from hop_rag.config import HopRAGConfig


@dataclass
class AgentConfig:
    llm: LLMConfig = field(default_factory=LLMConfig)
    graph: GraphConfig = field(default_factory=GraphConfig)
    hop_rag: HopRAGConfig = field(default_factory=HopRAGConfig)
    verbose: bool = False
    max_iterations: int = 15


def get_default_config() -> AgentConfig:
    return AgentConfig()

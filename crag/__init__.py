"""
CRAG: Code-augmented Reasoning on Adaptive Graphs
A novel framework for hybrid Graph RAG with dynamic code execution.
"""

from .agent import CRAGAgent
from .engine import CRAGEngine
from .config import CRAGConfig, AgentConfig

__all__ = [
    "CRAGAgent",
    "CRAGEngine",
    "CRAGConfig",
    "AgentConfig",
]

__version__ = "1.0.0"

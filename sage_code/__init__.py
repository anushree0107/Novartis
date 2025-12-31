"""
SAGE: Code-augmented Reasoning on Adaptive Graphs
A novel framework for hybrid Graph RAG with dynamic code execution.
"""

from .agent import SAGEAgent
from .engine import SAGEEngine
from .config import SAGEConfig, AgentConfig

__all__ = [
    "SAGEAgent",
    "SAGEEngine",
    "SAGEConfig",
    "AgentConfig",
]

__version__ = "1.0.0"

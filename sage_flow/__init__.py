"""
SAGE-Flow: SQL-Augmented Graph Execution Flow

A novel framework combining Text2SQL and GraphRAG for clinical trial intelligence.
"""
from .orchestrator import SAGEFlowOrchestrator, create_sage_flow
from .router import IntentRouter, QueryIntent
from .merger import SmartMerger

__all__ = [
    "SAGEFlowOrchestrator",
    "create_sage_flow",
    "IntentRouter",
    "QueryIntent",
    "SmartMerger",
]

__version__ = "1.0.0"

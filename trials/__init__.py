"""TRIALS: Text-to-SQL with RAG, Iterative Agents, & Learning Systems."""

from .agents import (
    InformationRetrieverAgent,
    SchemaSelectorAgent,
    CandidateGeneratorAgent,
    UnitTesterAgent,
    ResultExplainerAgent,
)
from .pipeline import Orchestrator

__all__ = [
    "InformationRetrieverAgent",
    "SchemaSelectorAgent", 
    "CandidateGeneratorAgent",
    "UnitTesterAgent",
    "ResultExplainerAgent",
    "Orchestrator",
]

__version__ = "1.0.0"

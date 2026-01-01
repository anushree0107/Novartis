"""
Agents module - NEXUS multi-agent Text-to-SQL system

5 Agents with their Tools:
1. Information Retriever (IR): extract_keywords, retrieve_entity, retrieve_context
2. Schema Selector (SS): filter_column, select_tables, select_columns
3. Candidate Generator (CG): generate_candidate_query, revise
4. Unit Tester (UT): generate_unit_test, evaluate
5. Result Explainer (RE): explain_results, summarize_large_results, split_complex_query
"""
from agents.base_agent import BaseAgent, BaseTool, AgentResult, ToolResult
from agents.information_retriever import InformationRetrieverAgent
from agents.schema_selector import SchemaSelectorAgent
from agents.candidate_generator import CandidateGeneratorAgent
from agents.unit_tester import UnitTesterAgent
from agents.result_explainer import ResultExplainerAgent

__all__ = [
    'BaseAgent',
    'BaseTool',
    'AgentResult',
    'ToolResult',
    'InformationRetrieverAgent',
    'SchemaSelectorAgent', 
    'CandidateGeneratorAgent',
    'UnitTesterAgent',
    'ResultExplainerAgent'
]

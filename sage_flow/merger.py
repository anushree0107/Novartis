import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from prompts import MERGER_SYSTEM_PROMPT


@dataclass
class MergerInput:
    question: str
    sql_result: Optional[Dict[str, Any]] = None
    graph_result: Optional[Dict[str, Any]] = None
    execution_order: str = "parallel"


@dataclass 
class MergedResult:
    answer: str
    data_summary: Optional[str] = None
    context_summary: Optional[str] = None
    sources_used: List[str] = None
    confidence: float = 1.0
    
    def __post_init__(self):
        if self.sources_used is None:
            self.sources_used = []


class SmartMerger:    
    def __init__(self, llm, verbose: bool = False):
        self.llm = llm
        self.verbose = verbose
    
    def log(self, msg: str):
        if self.verbose:
            print(f"🔀 [Merger] {msg}")
    
    def _extract_sql_summary(self, sql_result: Dict[str, Any]) -> str:
        if not sql_result:
            return "No SQL data available."
        if sql_result.get('error'):
            return f"SQL Error: {sql_result['error']}"
        execution = sql_result.get('execution_result', sql_result)
        if not execution.get('success', sql_result.get('success', True)):
            return f"SQL execution failed: {execution.get('error', 'Unknown error')}"
        row_count = execution.get('row_count', len(execution.get('data', [])))
        columns = execution.get('columns', [])
        data = execution.get('data', [])
        summary_parts = [f"Retrieved {row_count} record(s)"]
        if columns:
            summary_parts.append(f"Columns: {', '.join(columns[:5])}")
        if data:
            for row in data[:3]:
                if isinstance(row, dict):
                    row_str = ", ".join(f"{k}: {v}" for k, v in list(row.items())[:4])
                    summary_parts.append(f"  - {row_str}")
        return "\n".join(summary_parts)
    
    def _extract_graph_summary(self, graph_result: Dict[str, Any]) -> str:
        if not graph_result:
            return "No Graph data available."
        if graph_result.get('error'):
            return f"Graph Error: {graph_result['error']}"
        output = graph_result.get('output', graph_result)
        if isinstance(output, str):
            return output
        return str(output)[:1500]
    
    def _detect_conflicts(self, sql_summary: str, graph_summary: str) -> List[str]:
        conflicts = []
        if "0 record" in sql_summary.lower() and len(graph_summary) > 100:
            conflicts.append("SQL returned no records, but Graph found related information.")
        return conflicts
    
    def merge(self, input_data: MergerInput) -> MergedResult:
        self.log(f"Merging results for: {input_data.question[:50]}...")
        
        if input_data.sql_result and not input_data.graph_result:
            self.log("Single source: SQL only")
            sql_summary = self._extract_sql_summary(input_data.sql_result)
            explanation = input_data.sql_result.get('explanation')
            if explanation:
                return MergedResult(answer=explanation, data_summary=sql_summary, sources_used=["Text2SQL"])
            return MergedResult(answer=f"Based on database query:\n\n{sql_summary}", data_summary=sql_summary, sources_used=["Text2SQL"])
        
        if input_data.graph_result and not input_data.sql_result:
            self.log("Single source: Graph only")
            graph_summary = self._extract_graph_summary(input_data.graph_result)
            return MergedResult(answer=graph_summary, context_summary=graph_summary, sources_used=["GraphRAG"])
        
        self.log("Dual source: Performing smart merge")
        sql_summary = self._extract_sql_summary(input_data.sql_result)
        graph_summary = self._extract_graph_summary(input_data.graph_result)
        conflicts = self._detect_conflicts(sql_summary, graph_summary)
        
        from langchain_core.messages import SystemMessage, HumanMessage
        merge_prompt = f"""Question: {input_data.question}

=== SQL OUTPUT ===
{sql_summary}

=== GRAPH OUTPUT ===
{graph_summary}

{f"=== CONFLICTS ===" + chr(10) + chr(10).join(conflicts) if conflicts else ""}

Synthesize a comprehensive answer combining both sources."""
        
        messages = [SystemMessage(content=MERGER_SYSTEM_PROMPT), HumanMessage(content=merge_prompt)]
        response = self.llm.invoke(messages)
        
        return MergedResult(
            answer=response.content,
            data_summary=sql_summary,
            context_summary=graph_summary,
            sources_used=["Text2SQL", "GraphRAG"],
            confidence=0.9 if not conflicts else 0.7
        )
    
    def quick_merge(self, question: str, sql_result: Dict = None, graph_result: Dict = None) -> str:
        return self.merge(MergerInput(question=question, sql_result=sql_result, graph_result=graph_result)).answer

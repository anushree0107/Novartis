import time
import sys
import os
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from router import IntentRouter, QueryIntent, RouterResult
from merger import SmartMerger, MergerInput, MergedResult


@dataclass
class SAGEFlowResult:
    success: bool
    answer: str
    question: str
    intent: QueryIntent = None
    routing_reasoning: str = ""
    sql_result: Dict[str, Any] = None
    graph_result: Dict[str, Any] = None
    cross_modal_context: str = None
    execution_order: str = "single"
    total_time: float = 0.0
    routing_time: float = 0.0
    sql_time: float = 0.0
    graph_time: float = 0.0
    merge_time: float = 0.0
    error: str = None
    
    def summary(self) -> str:
        return f"""
{'='*60}
🔮 SAGE-FLOW RESULT
{'='*60}
Question: {self.question}
Intent: {self.intent.value if self.intent else 'N/A'}
Execution: {self.execution_order}
Success: {self.success}

📊 ANSWER:
{'-'*40}
{self.answer}
{'-'*40}

⏱️ Timing:
  Routing: {self.routing_time:.2f}s
  SQL: {self.sql_time:.2f}s
  Graph: {self.graph_time:.2f}s
  Merge: {self.merge_time:.2f}s
  Total: {self.total_time:.2f}s
{'='*60}"""


class SAGEFlowOrchestrator:
    """SAGE-Flow: SQL-Augmented Graph Execution Flow Orchestrator."""
    
    def __init__(self, graph_agent, sql_pipeline, llm, verbose: bool = True):
        self.graph_agent = graph_agent
        self.sql_pipeline = sql_pipeline
        self.llm = llm
        self.verbose = verbose
        self.router = IntentRouter(llm, use_fast_classification=True)
        self.merger = SmartMerger(llm, verbose=verbose)
        self._executor = ThreadPoolExecutor(max_workers=2)
    
    def log(self, msg: str, level: str = "info"):
        if self.verbose:
            prefix = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌", "step": "🔄", "sage": "🔮"}.get(level, "")
            print(f"{prefix} [SAGE-Flow] {msg}")
    
    def _run_sql(self, question: str) -> Tuple[Dict[str, Any], float]:
        start = time.time()
        try:
            result = self.sql_pipeline.run(question, execute_result=True, explain_result=True)
            return {'success': result.success, 'sql': result.sql, 'execution_result': result.execution_result, 'explanation': result.explanation}, time.time() - start
        except Exception as e:
            return {'success': False, 'error': str(e)}, time.time() - start
    
    def _run_graph(self, question: str) -> Tuple[Dict[str, Any], float]:
        start = time.time()
        try:
            return self.graph_agent.query(question), time.time() - start
        except Exception as e:
            return {'output': f"Error: {e}", 'error': True}, time.time() - start
    
    def _run_parallel(self, question: str) -> Tuple[Dict, Dict, float, float]:
        self.log("Executing SQL and Graph in PARALLEL", "sage")
        sql_future = self._executor.submit(self._run_sql, question)
        graph_future = self._executor.submit(self._run_graph, question)
        sql_result, sql_time = sql_future.result()
        graph_result, graph_time = graph_future.result()
        return sql_result, graph_result, sql_time, graph_time
    
    def _sql_then_graph(self, question: str, router_result: RouterResult) -> Tuple[Dict, Dict, float, float, str]:
        self.log("Executing SQL -> Graph (Grounded Traversal)", "sage")
        sql_result, sql_time = self._run_sql(question)
        
        if not sql_result.get('success'):
            self.log("SQL failed, falling back to Graph only", "warning")
            graph_result, graph_time = self._run_graph(question)
            return sql_result, graph_result, sql_time, graph_time, ""
        
        execution_result = sql_result.get('execution_result', {})
        data = execution_result.get('data', [])
        
        if not data:
            self.log("SQL returned no data, running Graph with original question", "warning")
            graph_result, graph_time = self._run_graph(question)
            return sql_result, graph_result, sql_time, graph_time, ""
        
        id_columns = ['id', 'study_id', 'site_id', 'subject_id', 'trial_id', 'name']
        entity_ids = []
        for row in data[:10]:
            if isinstance(row, dict):
                for col in id_columns:
                    if col in row and row[col]:
                        entity_ids.append(str(row[col]))
                        break
        
        grounded_context = f"Focus on entities: {', '.join(entity_ids[:5])}" if entity_ids else ""
        grounded_question = f"{question}\n\n[CONTEXT: {grounded_context}]" if grounded_context else question
        
        if entity_ids:
            self.log(f"Grounding Graph with {len(entity_ids)} entities", "sage")
        
        graph_result, graph_time = self._run_graph(grounded_question)
        return sql_result, graph_result, sql_time, graph_time, grounded_context
    
    def _graph_then_sql(self, question: str, router_result: RouterResult) -> Tuple[Dict, Dict, float, float, str]:
        self.log("Executing Graph -> SQL (Semantic Expansion)", "sage")
        expansion_question = f"What are related terms for concepts in: {question}"
        graph_result, graph_time = self._run_graph(expansion_question)
        
        graph_output = graph_result.get('output', '')
        if isinstance(graph_output, list):
            graph_output = " ".join(str(item) for item in graph_output)
        
        expansion_context = f"Consider related terms: {graph_output[:500]}" if graph_output else ""
        enhanced_question = f"{question}\n\n[SEMANTIC CONTEXT: {expansion_context}]" if expansion_context else question
        
        sql_result, sql_time = self._run_sql(enhanced_question)
        full_graph_result, additional_graph_time = self._run_graph(question)
        graph_time += additional_graph_time
        
        return sql_result, full_graph_result, sql_time, graph_time, expansion_context
    
    def query(self, question: str) -> SAGEFlowResult:
        start_time = time.time()
        self.log(f"Processing: {question[:80]}...", "step")
        
        routing_start = time.time()
        router_result = self.router.classify(question)
        routing_time = time.time() - routing_start
        self.log(f"Classified as: {router_result.intent.value} ({router_result.reasoning})", "success")
        
        sql_result, graph_result = None, None
        sql_time, graph_time = 0.0, 0.0
        cross_modal_context, execution_order = None, "single"
        
        try:
            if router_result.intent == QueryIntent.SQL_ONLY:
                self.log("Executing SQL ONLY", "step")
                sql_result, sql_time = self._run_sql(question)
                execution_order = "sql_only"
            elif router_result.intent == QueryIntent.GRAPH_ONLY:
                self.log("Executing Graph ONLY", "step")
                graph_result, graph_time = self._run_graph(question)
                execution_order = "graph_only"
            elif router_result.intent == QueryIntent.SQL_THEN_GRAPH:
                sql_result, graph_result, sql_time, graph_time, cross_modal_context = self._sql_then_graph(question, router_result)
                execution_order = "sql_then_graph"
            elif router_result.intent == QueryIntent.GRAPH_THEN_SQL:
                sql_result, graph_result, sql_time, graph_time, cross_modal_context = self._graph_then_sql(question, router_result)
                execution_order = "graph_then_sql"
            else:
                sql_result, graph_result, sql_time, graph_time = self._run_parallel(question)
                execution_order = "parallel"
        except Exception as e:
            return SAGEFlowResult(success=False, answer=f"Execution error: {e}", question=question, intent=router_result.intent, error=str(e), total_time=time.time() - start_time, routing_time=routing_time)
        
        merge_start = time.time()
        merged = self.merger.merge(MergerInput(question=question, sql_result=sql_result, graph_result=graph_result, execution_order=execution_order))
        merge_time = time.time() - merge_start
        
        total_time = time.time() - start_time
        self.log(f"Complete in {total_time:.2f}s", "success")
        
        return SAGEFlowResult(
            success=True, answer=merged.answer, question=question, intent=router_result.intent,
            routing_reasoning=router_result.reasoning, sql_result=sql_result, graph_result=graph_result,
            cross_modal_context=cross_modal_context, execution_order=execution_order,
            total_time=total_time, routing_time=routing_time, sql_time=sql_time, graph_time=graph_time, merge_time=merge_time
        )
    
    def quick_query(self, question: str) -> str:
        return self.query(question).answer


def create_sage_flow(verbose: bool = True) -> SAGEFlowOrchestrator:
    """Factory function to create SAGE-Flow orchestrator."""
    from dotenv import load_dotenv
    load_dotenv()
    
    from graph_rag.agent import create_agent as create_graph_agent
    graph_agent = create_graph_agent(auto_load=True)
    
    from pipeline.orchestrator import create_pipeline
    sql_pipeline = create_pipeline(verbose=verbose)
    
    from langchain_groq import ChatGroq
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.0, groq_api_key=os.getenv("GROQ_API_KEY"))
    
    return SAGEFlowOrchestrator(graph_agent=graph_agent, sql_pipeline=sql_pipeline, llm=llm, verbose=verbose)


if __name__ == "__main__":
    print("🔮 SAGE-Flow: SQL-Augmented Graph Execution Flow")
    print("="*60)
    
    try:
        orchestrator = create_sage_flow(verbose=True)
        print("\n✅ SAGE-Flow initialized successfully!\n")
        
        question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else input("Enter your question: ")
        result = orchestrator.query(question)
        print(result.summary())
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()

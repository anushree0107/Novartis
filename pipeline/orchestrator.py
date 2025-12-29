"""
CHESS Pipeline Orchestrator
Coordinates all 4 agents in sequence for Text-to-SQL synthesis
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import time

from agents import (
    InformationRetrieverAgent,
    SchemaSelectorAgent,
    CandidateGeneratorAgent,
    UnitTesterAgent,
    AgentResult
)
from database.connection import DatabaseManager, db_manager
from database.schema_manager import SchemaManager, schema_manager
from preprocessing.indexer import DatabasePreprocessor, preprocessor
from utils.llm_client import GroqLLMClient
from config.settings import GROQ_API_KEY


@dataclass
class PipelineResult:
    """Result from the complete CHESS pipeline"""
    success: bool
    sql: str
    question: str
    execution_result: Dict = None
    
    # Agent results for transparency
    ir_result: AgentResult = None
    ss_result: AgentResult = None
    cg_result: AgentResult = None
    ut_result: AgentResult = None
    
    # Metrics
    total_tokens: int = 0
    total_time: float = 0.0
    error: str = None
    
    def summary(self) -> str:
        """Generate a summary of the pipeline execution"""
        lines = [
            f"\n{'='*60}",
            f"CHESS Pipeline Result",
            f"{'='*60}",
            f"Question: {self.question}",
            f"Success: {self.success}",
            f"",
        ]
        
        if self.sql:
            lines.append("Generated SQL:")
            lines.append(f"```sql\n{self.sql}\n```")
        
        if self.execution_result:
            lines.append(f"\nExecution Result:")
            lines.append(f"  Rows: {self.execution_result.get('row_count', 'N/A')}")
            if self.execution_result.get('columns'):
                lines.append(f"  Columns: {self.execution_result['columns']}")
        
        lines.extend([
            f"\nMetrics:",
            f"  Total Tokens: {self.total_tokens}",
            f"  Total Time: {self.total_time:.2f}s",
        ])
        
        if self.ir_result:
            lines.append(f"  IR Agent: {self.ir_result.execution_time:.2f}s, {self.ir_result.tokens_used} tokens")
        if self.ss_result:
            lines.append(f"  SS Agent: {self.ss_result.execution_time:.2f}s, {self.ss_result.tokens_used} tokens")
        if self.cg_result:
            lines.append(f"  CG Agent: {self.cg_result.execution_time:.2f}s, {self.cg_result.tokens_used} tokens")
        if self.ut_result:
            lines.append(f"  UT Agent: {self.ut_result.execution_time:.2f}s, {self.ut_result.tokens_used} tokens")
        
        if self.error:
            lines.append(f"\nError: {self.error}")
        
        lines.append('='*60)
        
        return "\n".join(lines)


class CHESSPipeline:
    """
    CHESS Text-to-SQL Pipeline
    
    Orchestrates 4 agents:
    1. Information Retriever (IR) - Extracts keywords, entities, context
    2. Schema Selector (SS) - Selects relevant tables and columns
    3. Candidate Generator (CG) - Generates and refines SQL candidates
    4. Unit Tester (UT) - Selects best candidate via unit tests
    """
    
    def __init__(
        self,
        llm_client: GroqLLMClient = None,
        db: DatabaseManager = None,
        schema_mgr: SchemaManager = None,
        preprocess: DatabasePreprocessor = None,
        verbose: bool = True
    ):
        """
        Initialize the CHESS pipeline
        
        Args:
            llm_client: Groq LLM client
            db: Database manager
            schema_mgr: Schema manager
            preprocess: Preprocessor with LSH and vector indices
            verbose: Whether to print progress
        """
        # Initialize components
        self.llm = llm_client or GroqLLMClient()
        self.db = db or db_manager
        self.schema = schema_mgr or schema_manager
        self.preprocessor = preprocess or preprocessor
        self.verbose = verbose
        
        # Initialize agents
        self.ir_agent = InformationRetrieverAgent(
            self.llm, 
            self.schema, 
            self.preprocessor
        )
        self.ss_agent = SchemaSelectorAgent(self.llm, self.schema)
        self.cg_agent = CandidateGeneratorAgent(self.llm, self.db)
        self.ut_agent = UnitTesterAgent(self.llm, self.db)
    
    def log(self, message: str, level: str = "info"):
        """Log pipeline progress"""
        if self.verbose:
            prefix = {
                "info": "ℹ️",
                "success": "✅", 
                "warning": "⚠️",
                "error": "❌",
                "step": "🔄"
            }.get(level, "")
            print(f"{prefix} [Pipeline] {message}")
    
    def run(
        self,
        question: str,
        num_candidates: int = 3,
        num_unit_tests: int = 5,
        execute_result: bool = True
    ) -> PipelineResult:
        """
        Run the complete CHESS pipeline
        
        Args:
            question: Natural language question
            num_candidates: Number of SQL candidates to generate
            num_unit_tests: Number of unit tests for selection
            execute_result: Whether to execute final SQL
            
        Returns:
            PipelineResult with generated SQL and metadata
        """
        start_time = time.time()
        total_tokens = 0
        
        self.log(f"Processing question: {question[:100]}...", "step")
        
        # ========== Stage 1: Information Retriever ==========
        self.log("Stage 1: Information Retriever", "step")
        
        ir_result = self.ir_agent.execute(question)
        total_tokens += ir_result.tokens_used
        
        if not ir_result.success:
            return PipelineResult(
                success=False,
                sql=None,
                question=question,
                ir_result=ir_result,
                error=f"IR Agent failed: {ir_result.error}",
                total_tokens=total_tokens,
                total_time=time.time() - start_time
            )
        
        self.log(f"IR complete: {ir_result.reasoning}", "success")
        
        # ========== Stage 2: Schema Selector ==========
        self.log("Stage 2: Schema Selector", "step")
        
        ss_result = self.ss_agent.execute(
            question=question,
            ir_result=ir_result.data
        )
        total_tokens += ss_result.tokens_used
        
        if not ss_result.success:
            return PipelineResult(
                success=False,
                sql=None,
                question=question,
                ir_result=ir_result,
                ss_result=ss_result,
                error=f"SS Agent failed: {ss_result.error}",
                total_tokens=total_tokens,
                total_time=time.time() - start_time
            )
        
        self.log(f"SS complete: {ss_result.reasoning}", "success")
        
        # ========== Stage 3: Candidate Generator ==========
        self.log("Stage 3: Candidate Generator", "step")
        
        cg_result = self.cg_agent.execute(
            question=question,
            ss_result=ss_result.data,
            ir_result=ir_result.data,
            num_candidates=num_candidates
        )
        total_tokens += cg_result.tokens_used
        
        if not cg_result.success:
            return PipelineResult(
                success=False,
                sql=None,
                question=question,
                ir_result=ir_result,
                ss_result=ss_result,
                cg_result=cg_result,
                error=f"CG Agent failed: {cg_result.error}",
                total_tokens=total_tokens,
                total_time=time.time() - start_time
            )
        
        self.log(f"CG complete: {cg_result.reasoning}", "success")
        
        candidates = cg_result.data.get('candidates', [])
        
        # ========== Stage 4: Unit Tester ==========
        self.log("Stage 4: Unit Tester", "step")
        
        ut_result = self.ut_agent.execute(
            question=question,
            candidates=candidates,
            num_tests=num_unit_tests
        )
        total_tokens += ut_result.tokens_used
        
        if not ut_result.success:
            # Fallback: use best candidate from CG
            self.log("UT failed, using CG best candidate", "warning")
            best_sql = cg_result.data.get('best_candidate', {}).get('sql')
        else:
            best_sql = ut_result.data.get('selected_sql')
            self.log(f"UT complete: {ut_result.reasoning}", "success")
        
        # ========== Execute Final SQL ==========
        execution_result = None
        if execute_result and best_sql:
            self.log("Executing final SQL...", "step")
            execution_result = self.db.safe_execute(best_sql, timeout_seconds=30)
            
            if execution_result.get('success'):
                self.log(f"Execution success: {execution_result.get('row_count', 0)} rows", "success")
            else:
                self.log(f"Execution failed: {execution_result.get('error', 'Unknown')}", "warning")
        
        total_time = time.time() - start_time
        self.log(f"Pipeline complete in {total_time:.2f}s", "success")
        
        return PipelineResult(
            success=best_sql is not None,
            sql=best_sql,
            question=question,
            execution_result=execution_result,
            ir_result=ir_result,
            ss_result=ss_result,
            cg_result=cg_result,
            ut_result=ut_result,
            total_tokens=total_tokens,
            total_time=total_time
        )
    
    def quick_query(self, question: str) -> Dict[str, Any]:
        """
        Quick query mode - simplified output
        
        Args:
            question: Natural language question
            
        Returns:
            Dict with sql, success, data, and error
        """
        result = self.run(question, execute_result=True)
        
        return {
            'success': result.success,
            'sql': result.sql,
            'data': result.execution_result.get('data', []) if result.execution_result else [],
            'columns': result.execution_result.get('columns', []) if result.execution_result else [],
            'row_count': result.execution_result.get('row_count', 0) if result.execution_result else 0,
            'error': result.error
        }


def create_pipeline(verbose: bool = True) -> CHESSPipeline:
    """Factory function to create a configured pipeline"""
    llm = GroqLLMClient() if GROQ_API_KEY else None
    
    if not llm:
        raise ValueError("GROQ_API_KEY not set. Please configure it in .env file")
    
    # Try to load preprocessor cache
    preprocessor.load_cache()
    
    return CHESSPipeline(
        llm_client=llm,
        verbose=verbose
    )

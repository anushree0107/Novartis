"""
SQL Refiner for CHASE-SQL.

Implements the self-refinement loop with execution feedback.
Iteratively improves SQL queries based on execution errors or empty results.
"""
import logging
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass

from .config import default_config
from .schema_context import SchemaContext, get_schema_context
from .database import DatabaseConnection, QueryResult, get_database
from .llm_client import BaseLLMClient, get_llm_client
from .prompts.refinement import REFINEMENT_PROMPT, EMPTY_RESULT_REFINEMENT_PROMPT

logger = logging.getLogger(__name__)


@dataclass
class RefinementResult:
    """Result of the refinement process"""
    final_sql: str
    success: bool
    iterations: int
    query_result: Optional[QueryResult] = None
    refinement_history: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.refinement_history is None:
            self.refinement_history = []


class SQLRefiner:
    """
    SQL Refiner implementing CHASE-SQL self-refinement loop.
    
    Executes SQL queries and uses LLM to fix errors iteratively.
    """
    
    def __init__(
        self,
        schema_context: Optional[SchemaContext] = None,
        db: Optional[DatabaseConnection] = None,
        llm_client: Optional[BaseLLMClient] = None,
        max_iterations: int = None
    ):
        self.schema_context = schema_context or get_schema_context()
        self.db = db
        self.llm_client = llm_client or get_llm_client()
        self.max_iterations = max_iterations or default_config.max_refinement_iterations
    
    def refine(
        self,
        sql: str,
        question: str,
        execute: bool = True
    ) -> RefinementResult:
        """
        Refine SQL query through iterative execution and correction.
        
        Args:
            sql: Initial SQL query
            question: Original natural language question
            execute: Whether to execute SQL for validation
            
        Returns:
            RefinementResult with final SQL and execution results
        """
        current_sql = sql
        history = []
        
        for iteration in range(self.max_iterations):
            logger.debug(f"Refinement iteration {iteration + 1}")
            
            # Step 1: Validate syntax (without execution)
            is_valid, syntax_error = self._validate_syntax(current_sql)
            
            if not is_valid:
                # Fix syntax error
                logger.info(f"Syntax error detected: {syntax_error}")
                history.append({
                    "iteration": iteration + 1,
                    "sql": current_sql,
                    "error_type": "syntax",
                    "error": syntax_error
                })
                current_sql = self._fix_with_llm(
                    current_sql, question, f"Syntax error: {syntax_error}"
                )
                continue
            
            # Step 2: Execute if requested
            if execute and self.db:
                result = self.db.execute_query(current_sql)
                
                if not result.success:
                    # Fix execution error
                    logger.info(f"Execution error: {result.error}")
                    history.append({
                        "iteration": iteration + 1,
                        "sql": current_sql,
                        "error_type": "execution",
                        "error": result.error
                    })
                    current_sql = self._fix_with_llm(
                        current_sql, question, 
                        f"Execution error ({result.error_type}): {result.error}"
                    )
                    continue
                
                # Check for empty results
                if result.row_count == 0:
                    logger.info("Query returned 0 rows")
                    history.append({
                        "iteration": iteration + 1,
                        "sql": current_sql,
                        "error_type": "empty_result",
                        "error": "Query returned 0 rows"
                    })
                    # Try to fix or confirm empty result is expected
                    fixed_sql = self._handle_empty_result(
                        current_sql, question
                    )
                    if fixed_sql and fixed_sql != current_sql:
                        current_sql = fixed_sql
                        continue
                    # Empty result confirmed as expected
                    return RefinementResult(
                        final_sql=current_sql,
                        success=True,
                        iterations=iteration + 1,
                        query_result=result,
                        refinement_history=history
                    )
                
                # Success with data
                return RefinementResult(
                    final_sql=current_sql,
                    success=True,
                    iterations=iteration + 1,
                    query_result=result,
                    refinement_history=history
                )
            
            # If not executing, just validate syntax
            return RefinementResult(
                final_sql=current_sql,
                success=True,
                iterations=iteration + 1,
                refinement_history=history
            )
        
        # Max iterations reached
        logger.warning(f"Max refinement iterations ({self.max_iterations}) reached")
        return RefinementResult(
            final_sql=current_sql,
            success=False,
            iterations=self.max_iterations,
            refinement_history=history
        )
    
    def _validate_syntax(self, sql: str) -> Tuple[bool, Optional[str]]:
        """Validate SQL syntax without execution"""
        if self.db:
            return self.db.validate_sql(sql)
        
        # Basic validation without database
        import sqlparse
        try:
            parsed = sqlparse.parse(sql)
            if not parsed or not parsed[0].tokens:
                return False, "Could not parse SQL"
            return True, None
        except Exception as e:
            return False, str(e)
    
    def _fix_with_llm(
        self,
        sql: str,
        question: str,
        error_feedback: str
    ) -> str:
        """Use LLM to fix the SQL based on error feedback"""
        
        # Get relevant schema context
        schema_str = self.schema_context.to_prompt_context(
            include_samples=True,
            max_tables=10
        )
        
        prompt = REFINEMENT_PROMPT.format(
            question=question,
            sql_query=sql,
            execution_feedback=error_feedback,
            schema_context=schema_str
        )
        
        response = self.llm_client.complete(prompt)
        fixed_sql = self.llm_client.extract_sql(response)
        
        if fixed_sql:
            logger.debug(f"LLM suggested fix:\n{fixed_sql}")
            return fixed_sql
        
        logger.warning("LLM could not generate a fix")
        return sql  # Return original if no fix
    
    def _handle_empty_result(
        self,
        sql: str,
        question: str
    ) -> Optional[str]:
        """Handle queries that return 0 rows"""
        
        # Get sample data context
        sample_context = self._get_sample_data_context()
        
        prompt = EMPTY_RESULT_REFINEMENT_PROMPT.format(
            question=question,
            sql_query=sql,
            sample_data=sample_context
        )
        
        response = self.llm_client.complete(prompt)
        
        # Check if LLM suggests a fix or confirms empty is expected
        if "correct" in response.lower() or "expected" in response.lower():
            logger.info("Empty result confirmed as expected")
            return None
        
        fixed_sql = self.llm_client.extract_sql(response)
        return fixed_sql
    
    def _get_sample_data_context(self) -> str:
        """Get sample data from key tables for context"""
        tables = ["studies", "sites", "subjects", "data_queries"]
        context_lines = []
        
        if self.db:
            for table in tables:
                samples = self.db.get_sample_data(table, limit=2)
                if samples:
                    context_lines.append(f"\n{table} sample:")
                    for row in samples:
                        row_str = ", ".join(f"{k}={repr(v)}" for k, v in list(row.items())[:4])
                        context_lines.append(f"  {row_str}")
        
        return "\n".join(context_lines) if context_lines else "No sample data available"


def refine_sql(sql: str, question: str, db: Optional[DatabaseConnection] = None) -> str:
    """Convenience function to refine SQL with execution validation"""
    refiner = SQLRefiner(db=db or get_database())
    result = refiner.refine(sql, question)
    return result.final_sql

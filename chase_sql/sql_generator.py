"""
SQL Generator for CHASE-SQL.

Implements multi-strategy SQL generation:
1. Chain-of-Thought (CoT) - Step-by-step reasoning
2. Query Decomposition - Build from sub-queries
3. Direct Generation - Single-shot generation
"""
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from .config import default_config
from .schema_context import SchemaContext, get_schema_context
from .schema_linker import SchemaLinker, LinkedSchema
from .llm_client import BaseLLMClient, get_llm_client
from .prompts.sql_generation import SQL_GENERATION_PROMPTS
from .prompts.clinical_prompts import CLINICAL_DOMAIN_CONTEXT

logger = logging.getLogger(__name__)


@dataclass
class SQLCandidate:
    """A generated SQL query candidate"""
    sql: str
    strategy: str
    reasoning: Optional[str] = None
    confidence: float = 0.0


class SQLGenerator:
    """
    SQL Generator implementing CHASE-SQL multi-strategy approach.
    
    Generates SQL queries using multiple strategies and returns candidates
    for validation and refinement.
    """
    
    def __init__(
        self,
        schema_context: Optional[SchemaContext] = None,
        llm_client: Optional[BaseLLMClient] = None,
        strategies: Optional[List[str]] = None
    ):
        self.schema_context = schema_context or get_schema_context()
        self.llm_client = llm_client or get_llm_client()
        self.strategies = strategies or default_config.generation_strategies
        self.schema_linker = SchemaLinker(self.schema_context, self.llm_client)
    
    def generate(
        self,
        question: str,
        linked_schema: Optional[LinkedSchema] = None,
        strategy: Optional[str] = None
    ) -> List[SQLCandidate]:
        """
        Generate SQL candidates for the given question.
        
        Args:
            question: Natural language question
            linked_schema: Pre-computed schema linking result (optional)
            strategy: Specific strategy to use (optional, uses all configured if None)
            
        Returns:
            List of SQL candidates from different strategies
        """
        # Step 1: Schema linking if not provided
        if linked_schema is None:
            linked_schema = self.schema_linker.link(question)
        
        # Get filtered schema context
        schema_str = self.schema_linker.get_filtered_schema(linked_schema)
        
        # Prepare join path description
        join_path_str = self._format_join_path(linked_schema.join_path)
        
        # Step 2: Generate candidates using selected strategies
        candidates = []
        strategies_to_use = [strategy] if strategy else self.strategies
        
        for strat in strategies_to_use:
            try:
                candidate = self._generate_with_strategy(
                    question=question,
                    schema_str=schema_str,
                    linked_schema=linked_schema,
                    join_path_str=join_path_str,
                    strategy=strat
                )
                if candidate:
                    candidates.append(candidate)
            except Exception as e:
                logger.warning(f"Strategy {strat} failed: {e}")
        
        if not candidates:
            logger.error("All generation strategies failed")
        
        return candidates
    
    def _generate_with_strategy(
        self,
        question: str,
        schema_str: str,
        linked_schema: LinkedSchema,
        join_path_str: str,
        strategy: str
    ) -> Optional[SQLCandidate]:
        """Generate SQL using a specific strategy"""
        
        prompt_template = SQL_GENERATION_PROMPTS.get(strategy)
        if not prompt_template:
            logger.warning(f"Unknown strategy: {strategy}")
            return None
        
        # Build prompt
        prompt = prompt_template.format(
            schema_context=schema_str,
            question=question,
            linked_tables=", ".join(linked_schema.tables),
            linked_columns=self._format_columns(linked_schema.columns),
            join_path=join_path_str or "Direct query (no joins needed)"
        )
        
        # Add clinical domain context as system prompt
        system_prompt = f"""You are a PostgreSQL expert for clinical trials databases.
        
{CLINICAL_DOMAIN_CONTEXT}

Important rules:
- Always use explicit JOIN syntax
- Use table aliases for readability
- Quote string values properly
- Handle NULL values with IS NULL/IS NOT NULL
- Use proper enum values from schema
"""
        
        # Generate
        logger.debug(f"Generating SQL with strategy: {strategy}")
        response = self.llm_client.complete(prompt, system_prompt)
        
        # Extract SQL
        sql = self.llm_client.extract_sql(response)
        
        if sql:
            return SQLCandidate(
                sql=self._clean_sql(sql),
                strategy=strategy,
                reasoning=response if strategy == "cot" else None
            )
        
        logger.warning(f"Could not extract SQL from {strategy} response")
        return None
    
    def _format_join_path(self, join_path: List[tuple]) -> str:
        """Format join path for prompt"""
        if not join_path:
            return ""
        
        lines = []
        for src, src_col, tgt, tgt_col in join_path:
            lines.append(f"{src}.{src_col} = {tgt}.{tgt_col}")
        return "\n".join(lines)
    
    def _format_columns(self, columns: Dict[str, List[str]]) -> str:
        """Format column selections for prompt"""
        lines = []
        for table, cols in columns.items():
            lines.append(f"{table}: {', '.join(cols)}")
        return "\n".join(lines)
    
    def _clean_sql(self, sql: str) -> str:
        """Clean and normalize SQL query"""
        # Remove extra whitespace
        sql = " ".join(sql.split())
        
        # Ensure ends with semicolon
        sql = sql.rstrip(';').strip() + ';'
        
        return sql
    
    def generate_single(
        self,
        question: str,
        linked_schema: Optional[LinkedSchema] = None
    ) -> Optional[str]:
        """
        Generate a single best SQL query.
        
        Convenience method that returns just the SQL string.
        Uses Chain-of-Thought strategy by default as it typically produces best results.
        """
        candidates = self.generate(question, linked_schema, strategy="cot")
        if candidates:
            return candidates[0].sql
        
        # Fallback to direct if CoT fails
        candidates = self.generate(question, linked_schema, strategy="direct")
        return candidates[0].sql if candidates else None


def generate_sql(question: str) -> Optional[str]:
    """Convenience function to generate SQL from natural language"""
    generator = SQLGenerator()
    return generator.generate_single(question)

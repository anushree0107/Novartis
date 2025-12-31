"""
Candidate Generator Agent (CG)
CHESS Agent 3: Generates and revises SQL query candidates

Tools:
1. generate_candidate_query - Generate a candidate SQL query using multi-step reasoning
2. revise - Fix faulty queries based on execution errors
"""
from typing import Dict, Any, List, Optional
import time

from agents.base_agent import BaseAgent, BaseTool, AgentResult, ToolResult
from database.connection import DatabaseManager, db_manager
from utils.llm_client import GroqLLMClient
from config.settings import MODELS, AGENT_CONFIG


# ============== TOOLS ==============

class GenerateCandidateQueryTool(BaseTool):
    """
    Tool: generate_candidate_query
    Generates a single candidate SQL query using multi-step reasoning.
    Takes question, schema, and context to produce SQL.
    """
    
    def __init__(self, llm_client: GroqLLMClient):
        super().__init__(
            name="generate_candidate_query",
            description="Generate a candidate SQL query",
            llm_client=llm_client
        )
    
    def execute(
        self,
        question: str,
        schema_context: str,
        entities: Dict = None,
        strategy: str = "standard"
    ) -> ToolResult:
        """
        Generate a SQL query candidate
        
        Args:
            question: Natural language question
            schema_context: Selected schema from SS agent
            entities: Retrieved entities from IR agent
            strategy: Generation strategy (standard/cot/decomposition)
        """
        # Build entity context if available
        entity_context = ""
        if entities and entities.get('matched_entities'):
            entity_lines = []
            for keyword, matches in entities['matched_entities'].items():
                if matches:
                    match_str = ", ".join([f"'{m['value']}' in {m['table']}.{m['column']}" for m in matches[:3]])
                    entity_lines.append(f"- '{keyword}' matches: {match_str}")
            if entity_lines:
                entity_context = "\n\nENTITY MATCHES FROM DATABASE:\n" + "\n".join(entity_lines)
        
        # Strategy-specific prompts
        if strategy == "cot":
            return self._generate_with_cot(question, schema_context, entity_context)
        elif strategy == "decomposition":
            return self._generate_with_decomposition(question, schema_context, entity_context)
        else:
            return self._generate_standard(question, schema_context, entity_context)
    
    def _generate_standard(
        self, 
        question: str, 
        schema_context: str, 
        entity_context: str
    ) -> ToolResult:
        """Standard multi-step reasoning generation"""
        
        system_prompt = """You are an expert PostgreSQL developer for clinical trial databases.
Generate accurate SQL queries following these guidelines:

CRITICAL PRINCIPLE - SIMPLICITY FIRST:
- Use the SIMPLEST query that answers the question correctly
- Do NOT combine multiple tables with UNION unless explicitly needed
- Do NOT add redundant WHERE filters (e.g., study_10_ tables already contain only Study 10 data)
- A single table query is usually correct - avoid over-engineering

Table Naming Convention:
- Tables are prefixed with study number (e.g., study_10_*, study_1_*)
- Data for a study is ONLY in its prefixed tables
- DO NOT filter by _study_number column if table name already specifies the study

Data Format Conventions:
- Country values use 3-letter ISO codes: USA, JPN, CHN, CAN, ITA, POL, HUN, CZE, ESP, etc.
- For patient counts, prefer "subject_level_metric" tables which have one row per subject
- Use COUNT(DISTINCT subject_id) for patient counts to avoid duplicates

SQL Guidelines:
1. Use ONLY tables and columns from the provided schema
2. Use explicit column names, never SELECT *
3. Only JOIN tables when data spans multiple tables
4. Apply proper WHERE clauses for filtering (but not redundant ones)
5. Use GROUP BY for aggregations
6. Include ORDER BY only for ranking/list questions
7. Add LIMIT for large result sets
8. Handle NULLs appropriately (COALESCE, IS NULL)

Output ONLY the SQL query in ```sql``` code blocks."""

        user_content = f"""Generate a PostgreSQL query for this question:

QUESTION: {question}

DATABASE SCHEMA:
{schema_context}
{entity_context}

Think step by step:
1. What data is being requested?
2. Which tables contain this data?
3. What columns to SELECT?
4. What JOINs are needed?
5. What WHERE conditions apply?
6. Is GROUP BY needed?
7. What ORDER BY makes sense?

Generate the SQL query:"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        response = self.call_llm(
            messages, 
            model=MODELS.get('sql_generator'),
            temperature=0.1,
            max_tokens=1500
        )
        
        if not response.get('content'):
            return ToolResult(
                success=False,
                data=None,
                tool_name=self.name,
                error=response.get('error', 'Failed to generate SQL')
            )
        
        sql = self.llm.extract_sql(response['content'])
        tokens = response['usage']['input_tokens'] + response['usage']['output_tokens']
        
        return ToolResult(
            success=sql is not None,
            data={
                "sql": sql,
                "strategy": "standard",
                "raw_response": response['content'][:500]
            },
            tool_name=self.name,
            tokens_used=tokens,
            error=None if sql else "Could not extract SQL from response"
        )
    
    def _generate_with_cot(
        self, 
        question: str, 
        schema_context: str, 
        entity_context: str
    ) -> ToolResult:
        """Chain-of-thought reasoning generation"""
        
        system_prompt = """You are an expert PostgreSQL developer. 
Use chain-of-thought reasoning to generate accurate SQL queries.
Think through each step explicitly before writing the final query.

CRITICAL PRINCIPLE - SIMPLICITY FIRST:
- Use the SIMPLEST query that answers the question correctly
- Do NOT combine multiple tables with UNION unless explicitly needed
- Tables are prefixed with study number (e.g., study_10_*) - they already contain only that study's data
- A single table query is usually correct - avoid over-engineering

Data Format Conventions:
- Country values use 3-letter ISO codes: USA, JPN, CHN, CAN, ITA, POL, HUN, CZE, ESP, etc.
- For patient counts, prefer "subject_level_metric" tables which have one row per subject
- Use COUNT(DISTINCT subject_id) for patient counts"""

        user_content = f"""Generate a PostgreSQL query using step-by-step reasoning:

QUESTION: {question}

DATABASE SCHEMA:
{schema_context}
{entity_context}

Let's think through this step by step:

Step 1 - Understand the question:
What is being asked? What metrics or data are needed?

Step 2 - Identify tables:
Which tables contain the required data?

Step 3 - Identify columns:
What columns are needed for SELECT, WHERE, and JOIN?

Step 4 - Plan JOINs:
How do tables connect? What are the join conditions?

Step 5 - Plan filters:
What WHERE conditions filter the data correctly?

Step 6 - Plan aggregations:
Is GROUP BY needed? What aggregations (COUNT, SUM, etc.)?

Step 7 - Write the query:
Combine all parts into a complete SQL query.

Now provide your reasoning and final SQL query in ```sql``` blocks:"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        response = self.call_llm(
            messages,
            model=MODELS.get('sql_generator'),
            temperature=0.2,
            max_tokens=2000
        )
        
        if not response.get('content'):
            return ToolResult(
                success=False,
                data=None,
                tool_name=self.name,
                error=response.get('error', 'Failed to generate SQL')
            )
        
        sql = self.llm.extract_sql(response['content'])
        tokens = response['usage']['input_tokens'] + response['usage']['output_tokens']
        
        # Extract reasoning
        reasoning = response['content'].split('```')[0] if '```' in response['content'] else ""
        
        return ToolResult(
            success=sql is not None,
            data={
                "sql": sql,
                "strategy": "chain_of_thought",
                "reasoning": reasoning[:1000]
            },
            tool_name=self.name,
            tokens_used=tokens,
            error=None if sql else "Could not extract SQL from response"
        )
    
    def _generate_with_decomposition(
        self, 
        question: str, 
        schema_context: str, 
        entity_context: str
    ) -> ToolResult:
        """Decomposition strategy for complex queries"""
        
        system_prompt = """You are an expert PostgreSQL developer.
For complex queries, break them into manageable parts using CTEs (WITH clauses).
This helps with clarity and debugging.

CRITICAL PRINCIPLE - SIMPLICITY FIRST:
- Tables are prefixed with study number (e.g., study_10_*) - they already contain only that study's data
- Do NOT add redundant WHERE filters on _study_number
- Use the SIMPLEST query that answers the question correctly

Data Format Conventions:
- Country values use 3-letter ISO codes: USA, JPN, CHN, CAN, ITA, POL, HUN, CZE, ESP, etc.
- For patient counts, prefer "subject_level_metric" tables which have one row per subject
- Use COUNT(DISTINCT subject_id) for patient counts"""

        user_content = f"""Generate a PostgreSQL query by decomposing the complex question:

QUESTION: {question}

DATABASE SCHEMA:
{schema_context}
{entity_context}

Decomposition approach:
1. Identify the main goal
2. Break into logical sub-parts
3. Use CTEs (WITH clauses) for intermediate results
4. Combine CTEs into final query

For complex queries, structure like:
WITH 
  step1 AS (SELECT ...),
  step2 AS (SELECT ... FROM step1 ...),
  ...
SELECT ... FROM stepN ...;

Generate the decomposed SQL query:"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        response = self.call_llm(
            messages,
            model=MODELS.get('sql_generator'),
            temperature=0.15,
            max_tokens=2500
        )
        
        if not response.get('content'):
            return ToolResult(
                success=False,
                data=None,
                tool_name=self.name,
                error=response.get('error', 'Failed to generate SQL')
            )
        
        sql = self.llm.extract_sql(response['content'])
        tokens = response['usage']['input_tokens'] + response['usage']['output_tokens']
        
        return ToolResult(
            success=sql is not None,
            data={
                "sql": sql,
                "strategy": "decomposition",
                "raw_response": response['content'][:500]
            },
            tool_name=self.name,
            tokens_used=tokens,
            error=None if sql else "Could not extract SQL from response"
        )


class ReviseTool(BaseTool):
    """
    Tool: revise
    Fixes faulty SQL queries based on execution errors.
    Takes the error description and attempts to fix the query.
    """
    
    def __init__(self, llm_client: GroqLLMClient, db: DatabaseManager = None):
        super().__init__(
            name="revise",
            description="Fix faulty SQL queries based on errors",
            llm_client=llm_client
        )
        self.db = db or db_manager
    
    def execute(
        self,
        sql: str,
        error: str,
        question: str,
        schema_context: str
    ) -> ToolResult:
        """
        Revise a faulty SQL query
        
        Args:
            sql: The faulty SQL query
            error: Error message or description
            question: Original question
            schema_context: Schema context for reference
        """
        system_prompt = """You are an expert SQL debugger for PostgreSQL.
Your task is to fix SQL queries that have errors.

Common issues and fixes:
1. Column not found → Check schema for correct column names
2. Table not found → Check schema for correct table names
3. Syntax error → Fix SQL syntax (commas, brackets, keywords)
4. Type mismatch → Ensure comparing same types, use CAST if needed
5. Ambiguous column → Add table alias prefix
6. GROUP BY error → Include all non-aggregated SELECT columns in GROUP BY
7. Empty result → Check WHERE conditions, maybe too restrictive

Return ONLY the fixed SQL query in ```sql``` code blocks."""

        user_content = f"""Fix this SQL query that has an error:

ORIGINAL QUESTION: {question}

FAULTY SQL:
```sql
{sql}
```

ERROR:
{error}

SCHEMA REFERENCE:
{schema_context}

Analyze the error and provide the corrected SQL query:"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        response = self.call_llm(
            messages,
            model=MODELS.get('sql_refiner'),
            temperature=0.1,
            max_tokens=1500
        )
        
        if not response.get('content'):
            return ToolResult(
                success=False,
                data=None,
                tool_name=self.name,
                error="Failed to revise query"
            )
        
        revised_sql = self.llm.extract_sql(response['content'])
        tokens = response['usage']['input_tokens'] + response['usage']['output_tokens']
        
        return ToolResult(
            success=revised_sql is not None,
            data={
                "revised_sql": revised_sql,
                "original_sql": sql,
                "error_fixed": error[:200]
            },
            tool_name=self.name,
            tokens_used=tokens,
            error=None if revised_sql else "Could not extract revised SQL"
        )


# ============== AGENT ==============

class CandidateGeneratorAgent(BaseAgent):
    """
    Agent 3: Candidate Generator (CG)
    
    Generates SQL query candidates and revises faulty ones:
    - Generates multiple candidates using different strategies
    - Executes candidates to check for errors
    - Revises faulty candidates
    """
    
    def __init__(
        self,
        llm_client: GroqLLMClient,
        db: DatabaseManager = None,
        **kwargs
    ):
        self.db = db or db_manager
        super().__init__(llm_client, model=MODELS.get('sql_generator'), **kwargs)
        self.name = "CandidateGenerator"
    
    def _register_tools(self):
        """Register CG agent tools"""
        self.add_tool(GenerateCandidateQueryTool(self.llm))
        self.add_tool(ReviseTool(self.llm, self.db))
    
    def get_system_prompt(self) -> str:
        return """You are a Candidate Generator agent for SQL synthesis.
Your job is to generate accurate SQL queries and fix any errors."""

    def execute(
        self,
        question: str,
        ss_result: Dict,
        ir_result: Dict,
        num_candidates: int = None,
        max_revisions: int = 2
    ) -> AgentResult:
        """
        Execute CG agent pipeline:
        1. Generate multiple SQL candidates using different strategies
        2. Execute each candidate to check for errors
        3. Revise faulty candidates
        
        Args:
            question: Original user question
            ss_result: Output from SchemaSelectorAgent
            ir_result: Output from InformationRetrieverAgent
            num_candidates: Number of candidates to generate
            max_revisions: Max revision attempts per candidate
            
        Returns:
            AgentResult with SQL candidates
        """
        start_time = time.time()
        tool_calls = []
        total_tokens = 0
        
        num_candidates = num_candidates or AGENT_CONFIG.get('top_candidates', 3)
        schema_context = ss_result.get('schema_context', '')
        entities = ir_result.get('entities', {})
        
        # Define generation strategies
        strategies = ['standard', 'cot']
        if num_candidates > 2:
            strategies.append('decomposition')
        
        candidates = []
        
        # Generate candidates with different strategies
        for i, strategy in enumerate(strategies[:num_candidates]):
            self.log(f"Generating candidate {i+1} with {strategy} strategy...")
            
            gen_result = self.call_tool(
                "generate_candidate_query",
                question=question,
                schema_context=schema_context,
                entities=entities,
                strategy=strategy
            )
            tool_calls.append(gen_result)
            total_tokens += gen_result.tokens_used
            
            if not gen_result.success or not gen_result.data.get('sql'):
                continue
            
            sql = gen_result.data['sql']
            
            # Execute to check for errors
            exec_result = self._execute_and_check(sql)
            
            candidate = {
                'sql': sql,
                'strategy': strategy,
                'is_valid': exec_result['valid'],
                'error': exec_result.get('error'),
                'result_preview': exec_result.get('preview'),
                'was_revised': False
            }
            
            # If error, try to revise
            if not exec_result['valid'] and exec_result.get('error'):
                self.log(f"Revising candidate {i+1} due to error...")
                
                for revision_attempt in range(max_revisions):
                    revise_result = self.call_tool(
                        "revise",
                        sql=candidate['sql'],
                        error=candidate['error'],
                        question=question,
                        schema_context=schema_context
                    )
                    tool_calls.append(revise_result)
                    total_tokens += revise_result.tokens_used
                    
                    if revise_result.success and revise_result.data.get('revised_sql'):
                        revised_sql = revise_result.data['revised_sql']
                        exec_result = self._execute_and_check(revised_sql)
                        
                        candidate['sql'] = revised_sql
                        candidate['is_valid'] = exec_result['valid']
                        candidate['error'] = exec_result.get('error')
                        candidate['result_preview'] = exec_result.get('preview')
                        candidate['was_revised'] = True
                        
                        if exec_result['valid']:
                            self.log(f"Candidate {i+1} fixed after revision", "success")
                            break
            
            candidates.append(candidate)
        
        # Sort candidates: valid first, then by strategy preference
        candidates.sort(key=lambda x: (not x['is_valid'], strategies.index(x['strategy']) if x['strategy'] in strategies else 99))
        
        valid_count = sum(1 for c in candidates if c['is_valid'])
        self.log(f"Generated {len(candidates)} candidates, {valid_count} valid", "success")
        
        return AgentResult(
            success=len(candidates) > 0,
            data={
                'candidates': candidates,
                'valid_count': valid_count,
                'best_candidate': candidates[0] if candidates else None
            },
            reasoning=f"Generated {len(candidates)} candidates using {strategies[:len(candidates)]}, "
                     f"{valid_count} valid",
            tokens_used=total_tokens,
            execution_time=time.time() - start_time,
            tool_calls=tool_calls
        )
    
    def _execute_and_check(self, sql: str) -> Dict:
        """Execute SQL and check for errors"""
        # First validate syntax
        validation = self.db.validate_sql(sql)
        
        if not validation['valid']:
            return {
                'valid': False,
                'error': validation.get('error', 'Syntax error'),
                'preview': None
            }
        
        # Try to execute with LIMIT for safety
        result = self.db.safe_execute(sql, timeout_seconds=15)
        
        if not result['success']:
            return {
                'valid': False,
                'error': result.get('error', 'Execution error'),
                'preview': None
            }
        
        # Check for empty results (might indicate logic error)
        row_count = result.get('row_count', 0)
        
        return {
            'valid': True,
            'error': None if row_count > 0 else 'Warning: Query returned 0 rows',
            'preview': {
                'columns': result.get('columns', []),
                'row_count': row_count,
                'sample_rows': result.get('data', [])[:3]
            }
        }

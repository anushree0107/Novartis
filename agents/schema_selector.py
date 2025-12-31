"""
Schema Selector Agent (SS)
CHESS Agent 2: Reduces schema size by selecting relevant tables and columns

Tools:
1. filter_column - Determine if a column is relevant to the query
2. select_tables - Select necessary tables from sub-schema
3. select_columns - Select necessary columns from tables
"""
from typing import Dict, Any, List, Optional, Set
import time

from agents.base_agent import BaseAgent, BaseTool, AgentResult, ToolResult
from database.schema_manager import SchemaManager, schema_manager, TableInfo
from utils.llm_client import GroqLLMClient
from utils.token_utils import token_manager
from config.settings import MODELS, TOKEN_LIMITS


# ============== TOOLS ==============

class FilterColumnTool(BaseTool):
    """
    Tool: filter_column
    Takes a column name and question, determines if column is relevant.
    Uses inexpensive LLM call for high accuracy filtering.
    """
    
    def __init__(self, llm_client: GroqLLMClient):
        super().__init__(
            name="filter_column",
            description="Determine if a column is relevant to the query",
            llm_client=llm_client
        )
    
    def execute(
        self, 
        columns: List[Dict[str, str]], 
        question: str,
        batch_size: int = 20
    ) -> ToolResult:
        """
        Filter columns based on relevance to question
        
        Args:
            columns: List of {table, column, data_type} dicts
            question: The user's question
            batch_size: Number of columns to evaluate per LLM call
        """
        relevant_columns = []
        total_tokens = 0
        
        # Process in batches for efficiency
        for i in range(0, len(columns), batch_size):
            batch = columns[i:i + batch_size]
            
            columns_text = "\n".join([
                f"- {c['table']}.{c['column']} ({c.get('data_type', 'unknown')})"
                for c in batch
            ])
            
            system_prompt = """You are a database schema expert. 
Evaluate which columns are relevant for answering the given question.
Return a JSON object with a list of relevant column identifiers."""

            user_content = f"""Question: "{question}"

Columns to evaluate:
{columns_text}

Return JSON: {{"relevant": ["table.column", "table.column", ...]}}
Only include columns that would be needed in SELECT, WHERE, JOIN, or GROUP BY clauses."""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
            
            response = self.call_llm(
                messages, 
                model=MODELS.get('evaluator'),  # Use faster model
                json_mode=True, 
                max_tokens=512
            )
            
            if response.get('content'):
                total_tokens += response['usage']['input_tokens'] + response['usage']['output_tokens']
                result = self.llm.extract_json(response['content'])
                
                if result and 'relevant' in result:
                    for col_id in result['relevant']:
                        parts = col_id.split('.')
                        if len(parts) == 2:
                            relevant_columns.append({
                                'table': parts[0],
                                'column': parts[1]
                            })
        
        return ToolResult(
            success=True,
            data={
                "relevant_columns": relevant_columns,
                "filtered_count": len(columns) - len(relevant_columns)
            },
            tool_name=self.name,
            tokens_used=total_tokens
        )


class SelectTablesTool(BaseTool):
    """
    Tool: select_tables
    Takes a sub-schema and question, returns necessary tables.
    Uses LLM prompting for accurate table selection.
    """
    
    def __init__(self, llm_client: GroqLLMClient):
        super().__init__(
            name="select_tables",
            description="Select tables necessary for answering the query",
            llm_client=llm_client
        )
    
    def execute(
        self, 
        tables_schema: str, 
        question: str,
        keywords: Dict = None
    ) -> ToolResult:
        """
        Select necessary tables from sub-schema
        
        Args:
            tables_schema: Schema description of available tables
            question: The user's question
            keywords: Extracted keywords from IR agent
        """
        system_prompt = """You are a database schema expert for clinical trial data.
Select only the tables necessary to answer the question.

Consider:
1. Which tables contain the data being asked about
2. Which tables are needed for JOINs to connect data
3. Tables for filtering conditions

Return a JSON object with selected tables and reasoning."""

        keywords_hint = ""
        if keywords:
            keywords_hint = f"""
Hints from question analysis:
- Keywords: {keywords.get('keywords', [])}
- Clinical terms: {keywords.get('clinical_terms', [])}
- Entities mentioned: {keywords.get('entities', [])}
"""

        user_content = f"""Question: "{question}"
{keywords_hint}
Available Tables Schema:
{tables_schema}

Return JSON:
{{
    "selected_tables": [
        {{"name": "table_name", "reason": "why this table is needed", "role": "primary|join|filter"}}
    ],
    "join_hints": ["table1.col = table2.col", ...]
}}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        response = self.call_llm(messages, json_mode=True, max_tokens=1024)
        
        if not response.get('content'):
            return ToolResult(
                success=False,
                data=None,
                tool_name=self.name,
                error="Failed to select tables"
            )
        
        result = self.llm.extract_json(response['content'])
        tokens = response['usage']['input_tokens'] + response['usage']['output_tokens']
        
        return ToolResult(
            success=True,
            data=result or {"selected_tables": [], "join_hints": []},
            tool_name=self.name,
            tokens_used=tokens
        )


class SelectColumnsTool(BaseTool):
    """
    Tool: select_columns
    Takes selected tables and question, returns necessary columns.
    Further narrows down schema to essential columns.
    """
    
    def __init__(self, llm_client: GroqLLMClient):
        super().__init__(
            name="select_columns",
            description="Select columns necessary for the query",
            llm_client=llm_client
        )
    
    def execute(
        self, 
        table_name: str,
        columns: List[Dict],
        question: str,
        table_role: str = "primary"
    ) -> ToolResult:
        """
        Select necessary columns from a table
        
        Args:
            table_name: Name of the table
            columns: List of column info dicts
            question: The user's question  
            table_role: Role of table (primary/join/filter)
        """
        columns_text = "\n".join([
            f"- {c['name']} ({c['data_type']}){' -- e.g., ' + str(c.get('sample_values', [])[:2]) if c.get('sample_values') else ''}"
            for c in columns
        ])
        
        system_prompt = """You are a SQL expert. Select only the columns needed for the query.

For PRIMARY tables: Select columns for SELECT and WHERE clauses
For JOIN tables: Select join keys and any needed data columns
For FILTER tables: Select columns used in WHERE conditions

Return JSON with selected columns."""

        user_content = f"""Question: "{question}"

Table: {table_name} (Role: {table_role})
Available Columns:
{columns_text}

Return JSON:
{{
    "columns": ["column1", "column2", ...],
    "usage": {{"column1": "SELECT|WHERE|JOIN|GROUP BY", ...}}
}}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        response = self.call_llm(
            messages, 
            model=MODELS.get('evaluator'),
            json_mode=True, 
            max_tokens=512
        )
        
        if not response.get('content'):
            # Fallback: return all columns
            return ToolResult(
                success=True,
                data={"columns": [c['name'] for c in columns], "usage": {}},
                tool_name=self.name,
                tokens_used=0
            )
        
        result = self.llm.extract_json(response['content'])
        tokens = response['usage']['input_tokens'] + response['usage']['output_tokens']
        
        return ToolResult(
            success=True,
            data=result or {"columns": [c['name'] for c in columns], "usage": {}},
            tool_name=self.name,
            tokens_used=tokens
        )


# ============== AGENT ==============

class SchemaSelectorAgent(BaseAgent):
    """
    Agent 2: Schema Selector (SS)
    
    Reduces schema size by selecting relevant tables and columns:
    - Filters out irrelevant columns
    - Selects necessary tables
    - Narrows down to essential columns
    """
    
    def __init__(
        self,
        llm_client: GroqLLMClient,
        schema_mgr: SchemaManager = None,
        **kwargs
    ):
        self.schema = schema_mgr or schema_manager
        super().__init__(llm_client, model=MODELS.get('schema_selector'), **kwargs)
        self.name = "SchemaSelector"
    
    def _register_tools(self):
        """Register SS agent tools"""
        self.add_tool(FilterColumnTool(self.llm))
        self.add_tool(SelectTablesTool(self.llm))
        self.add_tool(SelectColumnsTool(self.llm))
    
    def get_system_prompt(self) -> str:
        return """You are a Schema Selector agent for clinical trial databases.
Your job is to select the minimal set of tables and columns needed to answer a question."""

    def execute(
        self,
        question: str,
        ir_result: Dict,
        max_tables: int = 5
    ) -> AgentResult:
        """
        Execute SS agent pipeline:
        1. Get candidate tables from IR result
        2. Select necessary tables
        3. Select necessary columns for each table
        4. Build optimized schema context
        
        Args:
            question: Original user question
            ir_result: Output from InformationRetrieverAgent
            max_tables: Maximum tables to select
            
        Returns:
            AgentResult with selected schema
        """
        start_time = time.time()
        tool_calls = []
        total_tokens = 0
        
        # Get candidate tables
        candidate_tables = ir_result.get('relevant_tables', [])
        
        if not candidate_tables:
            # Fallback: get all tables
            candidate_tables = self.schema.get_all_tables()[:15]
        
        self.log(f"Evaluating {len(candidate_tables)} candidate tables...")
        
        # Step 1: Build schema for candidate tables
        tables_schema = self._build_tables_schema(candidate_tables)
        
        # Step 2: Select necessary tables
        self.log("Selecting necessary tables...")
        tables_result = self.call_tool(
            "select_tables",
            tables_schema=tables_schema,
            question=question,
            keywords=ir_result.get('keywords', {})
        )
        tool_calls.append(tables_result)
        total_tokens += tables_result.tokens_used
        
        if not tables_result.success:
            return self._fallback_selection(candidate_tables, question, start_time)
        
        selected_tables = tables_result.data.get('selected_tables', [])[:max_tables]
        join_hints = tables_result.data.get('join_hints', [])
        
        # Step 3: Select columns for each table
        self.log(f"Selecting columns for {len(selected_tables)} tables...")
        tables_with_columns = []
        
        for table_info in selected_tables:
            table_name = table_info.get('name')
            table_role = table_info.get('role', 'primary')
            
            schema_table = self.schema.get_table_info(table_name)
            if not schema_table:
                continue
            
            # Get column info
            columns = [
                {
                    'name': col.name,
                    'data_type': col.data_type,
                    'sample_values': col.sample_values
                }
                for col in schema_table.columns
            ]
            
            # Select relevant columns
            cols_result = self.call_tool(
                "select_columns",
                table_name=table_name,
                columns=columns,
                question=question,
                table_role=table_role
            )
            tool_calls.append(cols_result)
            total_tokens += cols_result.tokens_used
            
            selected_cols = cols_result.data.get('columns', []) if cols_result.success else [c['name'] for c in columns]
            
            tables_with_columns.append({
                'table_name': table_name,
                'columns': selected_cols,
                'role': table_role,
                'reason': table_info.get('reason', ''),
                'column_usage': cols_result.data.get('usage', {}) if cols_result.success else {}
            })
        
        # Step 4: Build optimized schema context
        schema_context = self._build_optimized_schema(tables_with_columns, join_hints)
        
        result_data = {
            'selected_tables': tables_with_columns,
            'join_hints': join_hints,
            'schema_context': schema_context,
            'primary_table': tables_with_columns[0]['table_name'] if tables_with_columns else None
        }
        
        self.log(f"Selected {len(tables_with_columns)} tables with optimized columns", "success")
        
        return AgentResult(
            success=True,
            data=result_data,
            reasoning=f"Selected {len(tables_with_columns)} tables, "
                     f"total columns: {sum(len(t['columns']) for t in tables_with_columns)}",
            tokens_used=total_tokens,
            execution_time=time.time() - start_time,
            tool_calls=tool_calls
        )
    
    def _build_tables_schema(self, table_names: List[str]) -> str:
        """Build schema description for candidate tables WITH descriptions"""
        lines = []
        
        for table_name in table_names:
            table_info = self.schema.get_table_info(table_name)
            if not table_info:
                continue
            
            # Compact representation with columns
            col_names = [f"{c.name}({c.data_type[:8]})" for c in table_info.columns[:10]]
            if len(table_info.columns) > 10:
                col_names.append(f"+{len(table_info.columns) - 10} more")
            
            lines.append(f"TABLE {table_name} [{table_info.row_count} rows]: {', '.join(col_names)}")
            
            # ADD DESCRIPTION - This is critical for table selection!
            if table_info.description:
                lines.append(f"  Description: {table_info.description}")
            
            if table_info.category:
                lines.append(f"  Category: {table_info.category}")
        
        return "\n".join(lines)
    
    def _build_optimized_schema(
        self, 
        tables: List[Dict], 
        join_hints: List[str]
    ) -> str:
        """Build token-optimized schema context for SQL generation"""
        lines = ["-- SELECTED DATABASE SCHEMA --\n"]
        
        for table_data in tables:
            table_name = table_data['table_name']
            columns = table_data['columns']
            
            table_info = self.schema.get_table_info(table_name)
            if not table_info:
                continue
            
            # Include table description as comment
            if table_info.description:
                lines.append(f"-- {table_name}: {table_info.description[:200]}")
            
            lines.append(f"CREATE TABLE {table_name} (")
            
            for col in table_info.columns:
                if col.name in columns:
                    nullable = "NULL" if col.is_nullable else "NOT NULL"
                    # Include column description and sample values
                    hints = []
                    if col.description:
                        hints.append(col.description[:50])
                    if col.sample_values:
                        samples = [str(v)[:25] for v in col.sample_values[:2]]
                        hints.append(f"e.g., {', '.join(samples)}")
                    hint_str = f"  -- {'; '.join(hints)}" if hints else ""
                    lines.append(f"    {col.name} {col.data_type} {nullable},{hint_str}")
            
            if lines[-1].endswith(','):
                lines[-1] = lines[-1][:-1]
            lines.append(f");  -- {table_info.row_count} rows, Role: {table_data.get('role', 'unknown')}\n")
        
        # Add join hints
        if join_hints:
            lines.append("-- JOIN RELATIONSHIPS:")
            for hint in join_hints:
                lines.append(f"-- {hint}")
        
        return "\n".join(lines)
    
    def _fallback_selection(
        self, 
        candidate_tables: List[str], 
        question: str,
        start_time: float
    ) -> AgentResult:
        """Fallback when tool-based selection fails"""
        tables_with_columns = []
        
        for table_name in candidate_tables[:5]:
            table_info = self.schema.get_table_info(table_name)
            if table_info:
                tables_with_columns.append({
                    'table_name': table_name,
                    'columns': [c.name for c in table_info.columns],
                    'role': 'unknown',
                    'reason': 'Fallback selection'
                })
        
        schema_context = self._build_optimized_schema(tables_with_columns, [])
        
        return AgentResult(
            success=True,
            data={
                'selected_tables': tables_with_columns,
                'join_hints': [],
                'schema_context': schema_context,
                'primary_table': tables_with_columns[0]['table_name'] if tables_with_columns else None
            },
            reasoning="Fallback selection used",
            tokens_used=0,
            execution_time=time.time() - start_time,
            tool_calls=[]
        )

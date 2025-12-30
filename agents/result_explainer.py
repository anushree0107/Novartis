"""
Result Explainer Agent (RE)
CHESS Agent 5: Explains SQL query results in natural language

Tools:
1. explain_results - Explain query results in clear natural language
2. summarize_large_results - Summarize large result sets with key insights
3. split_complex_query - Split complex joins into simpler interpretable queries
"""
from typing import Dict, Any, List, Optional, Tuple
import time
import json

from agents.base_agent import BaseAgent, BaseTool, AgentResult, ToolResult
from database.connection import DatabaseManager, db_manager
from utils.llm_client import GroqLLMClient
from config.settings import MODELS, AGENT_CONFIG


# ============== TOOLS ==============

class ExplainResultsTool(BaseTool):
    """
    Tool: explain_results
    Explains SQL query results in clear, natural language.
    """
    
    def __init__(self, llm_client: GroqLLMClient):
        super().__init__(
            name="explain_results",
            description="Explain SQL query results in natural language",
            llm_client=llm_client
        )
    
    def execute(
        self,
        question: str,
        sql: str,
        results: List[Dict],
        columns: List[str],
        row_count: int,
        max_rows_for_context: int = 20
    ) -> ToolResult:
        """
        Explain query results in natural language
        
        Args:
            question: Original natural language question
            sql: The SQL query that was executed
            results: Query results (list of dicts)
            columns: Column names
            row_count: Total number of rows
            max_rows_for_context: Max rows to include in prompt
        """
        # Sample results if too large
        sampled_results = results[:max_rows_for_context] if len(results) > max_rows_for_context else results
        is_sampled = len(results) > max_rows_for_context
        
        # Format results for display
        results_text = self._format_results(sampled_results, columns)
        
        system_prompt = """You are a helpful data analyst expert at explaining database query results.
Your job is to take SQL query results and explain them in clear, natural language that anyone can understand.

Guidelines:
1. Start with a direct answer to the user's question
2. Provide key insights from the data
3. Mention notable patterns, trends, or outliers if any
4. Use specific numbers and values from the results
5. If results are sampled, mention that there are more rows
6. Keep explanations concise but informative
7. Format numbers nicely (e.g., percentages, counts)
8. If the result is empty, explain what that means in context

Be conversational and helpful, not robotic."""

        sampling_note = f"\n\n(Note: Showing top {max_rows_for_context} of {row_count} total rows)" if is_sampled else ""
        
        user_content = f"""Please explain these query results in natural language.

ORIGINAL QUESTION: {question}

SQL QUERY EXECUTED:
```sql
{sql}
```

RESULTS ({row_count} total rows):
{results_text}{sampling_note}

Provide a clear, natural language explanation of these results that directly answers the user's question."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        response = self.call_llm(
            messages,
            model=MODELS.get('sql_generator'),
            temperature=0.3,
            max_tokens=1500
        )
        
        if not response.get('content'):
            return ToolResult(
                success=False,
                data=None,
                tool_name=self.name,
                error=response.get('error', 'Failed to generate explanation')
            )
        
        tokens = response['usage']['input_tokens'] + response['usage']['output_tokens']
        
        return ToolResult(
            success=True,
            data={
                "explanation": response['content'],
                "row_count": row_count,
                "is_sampled": is_sampled,
                "columns": columns
            },
            tool_name=self.name,
            tokens_used=tokens
        )
    
    def _format_results(self, results: List[Dict], columns: List[str]) -> str:
        """Format results as a readable table"""
        if not results:
            return "(No results)"
        
        # Build table
        lines = []
        
        # Header
        header = " | ".join(str(col)[:20] for col in columns)
        lines.append(header)
        lines.append("-" * len(header))
        
        # Rows
        for row in results:
            row_values = []
            for col in columns:
                val = row.get(col, '')
                val_str = str(val) if val is not None else 'NULL'
                # Truncate long values
                if len(val_str) > 30:
                    val_str = val_str[:27] + "..."
                row_values.append(val_str)
            lines.append(" | ".join(row_values))
        
        return "\n".join(lines)


class SummarizeLargeResultsTool(BaseTool):
    """
    Tool: summarize_large_results
    Provides statistical summary for large result sets.
    """
    
    def __init__(self, llm_client: GroqLLMClient):
        super().__init__(
            name="summarize_large_results",
            description="Summarize large result sets with statistics",
            llm_client=llm_client
        )
    
    def execute(
        self,
        question: str,
        sql: str,
        results: List[Dict],
        columns: List[str],
        row_count: int
    ) -> ToolResult:
        """
        Provide summary statistics for large results
        """
        # Compute basic statistics
        stats = self._compute_statistics(results, columns)
        
        # Get sample rows (first 10 and last 5)
        sample_rows = results[:10]
        if len(results) > 15:
            sample_rows.extend(results[-5:])
        
        system_prompt = """You are a data analyst providing insights on large datasets.
Summarize the results with key statistics and meaningful insights.
Focus on:
1. Overall summary answering the question
2. Key statistics (counts, averages, ranges)
3. Distribution patterns if visible
4. Notable values or outliers
5. Recommendations if applicable"""

        stats_text = json.dumps(stats, indent=2, default=str)
        sample_text = self._format_results_compact(sample_rows, columns)
        
        user_content = f"""Summarize these query results for the user.

QUESTION: {question}

SQL QUERY:
```sql
{sql}
```

TOTAL ROWS: {row_count}

STATISTICS:
{stats_text}

SAMPLE DATA (first and last rows):
{sample_text}

Provide a comprehensive but concise summary."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        response = self.call_llm(
            messages,
            model=MODELS.get('sql_generator'),
            temperature=0.3,
            max_tokens=1500
        )
        
        tokens = response['usage']['input_tokens'] + response['usage']['output_tokens']
        
        return ToolResult(
            success=response.get('content') is not None,
            data={
                "summary": response.get('content', ''),
                "statistics": stats,
                "row_count": row_count
            },
            tool_name=self.name,
            tokens_used=tokens,
            error=response.get('error')
        )
    
    def _compute_statistics(self, results: List[Dict], columns: List[str]) -> Dict:
        """Compute basic statistics for numeric and categorical columns"""
        stats = {"columns": {}}
        
        for col in columns:
            col_values = [r.get(col) for r in results if r.get(col) is not None]
            
            if not col_values:
                continue
            
            col_stats = {"count": len(col_values)}
            
            # Check if numeric
            numeric_values = []
            for v in col_values:
                try:
                    numeric_values.append(float(v))
                except (ValueError, TypeError):
                    break
            
            if len(numeric_values) == len(col_values) and numeric_values:
                col_stats.update({
                    "type": "numeric",
                    "min": min(numeric_values),
                    "max": max(numeric_values),
                    "avg": sum(numeric_values) / len(numeric_values)
                })
            else:
                # Categorical - show unique counts
                unique_values = set(str(v) for v in col_values)
                col_stats.update({
                    "type": "categorical",
                    "unique_count": len(unique_values),
                    "sample_values": list(unique_values)[:5]
                })
            
            stats["columns"][col] = col_stats
        
        return stats
    
    def _format_results_compact(self, results: List[Dict], columns: List[str]) -> str:
        """Format results in compact form"""
        if not results:
            return "(No results)"
        
        lines = []
        for i, row in enumerate(results):
            row_str = ", ".join(f"{col}={row.get(col, 'NULL')}" for col in columns[:5])
            if len(columns) > 5:
                row_str += f" (+{len(columns)-5} more)"
            lines.append(f"Row {i+1}: {row_str}")
        
        return "\n".join(lines)


class SplitComplexQueryTool(BaseTool):
    """
    Tool: split_complex_query
    Splits complex JOIN queries into simpler, more interpretable queries.
    """
    
    def __init__(self, llm_client: GroqLLMClient, db_manager: DatabaseManager):
        super().__init__(
            name="split_complex_query",
            description="Split complex joins into simpler queries",
            llm_client=llm_client
        )
        self.db = db_manager
    
    def execute(
        self,
        question: str,
        original_sql: str,
        schema_context: str = ""
    ) -> ToolResult:
        """
        Analyze if a query should be split into multiple simpler queries
        
        Returns multiple SQL queries if splitting makes sense
        """
        system_prompt = """You are a SQL expert analyzing query complexity.
Given a SQL query, determine if it should be split into multiple simpler queries for better interpretability.

Split the query if:
1. It has 3+ JOINs making results hard to interpret
2. It combines unrelated data that would be clearer separately
3. Results would be more meaningful as separate datasets

Keep as single query if:
1. JOINs are necessary for the answer
2. Results are coherent and interpretable
3. Splitting would lose important relationships

Output JSON with:
{
    "should_split": true/false,
    "reason": "explanation",
    "queries": [
        {
            "description": "what this query answers",
            "sql": "the SQL query"
        }
    ]
}

If should_split is false, return the original query in the queries array."""

        user_content = f"""Analyze this query and determine if it should be split:

ORIGINAL QUESTION: {question}

SQL QUERY:
```sql
{original_sql}
```

{f'SCHEMA CONTEXT: {schema_context}' if schema_context else ''}

Analyze and provide your recommendation."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        response = self.call_llm(
            messages,
            model=MODELS.get('sql_generator'),
            temperature=0.2,
            max_tokens=2000,
            json_mode=True
        )
        
        tokens = response['usage']['input_tokens'] + response['usage']['output_tokens']
        
        if not response.get('content'):
            return ToolResult(
                success=False,
                data=None,
                tool_name=self.name,
                tokens_used=tokens,
                error=response.get('error', 'Failed to analyze query')
            )
        
        try:
            result = self.llm.extract_json(response['content'])
            if result is None:
                result = {"should_split": False, "queries": [{"description": "Original query", "sql": original_sql}]}
        except:
            result = {"should_split": False, "queries": [{"description": "Original query", "sql": original_sql}]}
        
        return ToolResult(
            success=True,
            data=result,
            tool_name=self.name,
            tokens_used=tokens
        )


# ============== AGENT ==============

class ResultExplainerAgent(BaseAgent):
    """
    Result Explainer Agent
    
    Explains SQL query results in natural language for better understanding.
    Can handle large results by sampling and summarizing.
    Can split complex queries into simpler ones when needed.
    """
    
    def __init__(
        self,
        llm_client: GroqLLMClient,
        db_manager: DatabaseManager = None
    ):
        self.db = db_manager or db_manager
        super().__init__(llm_client)
    
    def _register_tools(self):
        """Register tools for this agent"""
        self.add_tool(ExplainResultsTool(self.llm))
        self.add_tool(SummarizeLargeResultsTool(self.llm))
        self.add_tool(SplitComplexQueryTool(self.llm, self.db))
    
    def get_system_prompt(self) -> str:
        return """You are a Result Explainer agent that helps users understand SQL query results.
Your job is to:
1. Explain query results in clear, natural language
2. Provide insights and key takeaways
3. Handle large result sets by summarizing effectively
4. Suggest splitting complex queries when results are hard to interpret"""
    
    def execute(
        self,
        question: str,
        sql: str,
        execution_result: Dict[str, Any],
        schema_context: str = "",
        max_rows_for_detail: int = 50,
        max_rows_for_context: int = 20
    ) -> AgentResult:
        """
        Execute the Result Explainer agent
        
        Args:
            question: Original natural language question
            sql: The SQL query that was executed
            execution_result: Result from database execution with 'data', 'columns', 'row_count'
            schema_context: Optional schema context for better explanations
            max_rows_for_detail: Threshold for detailed vs summary explanation
            max_rows_for_context: Max rows to send to LLM
            
        Returns:
            AgentResult with natural language explanation
        """
        start_time = time.time()
        total_tokens = 0
        tool_calls = []
        
        self.log("Starting result explanation...", "info")
        
        # Extract result data
        results = execution_result.get('data', [])
        columns = execution_result.get('columns', [])
        row_count = execution_result.get('row_count', len(results))
        success = execution_result.get('success', True)
        
        # Handle failed execution
        if not success:
            error_msg = execution_result.get('error', 'Query execution failed')
            return AgentResult(
                success=False,
                data={"explanation": f"The query could not be executed: {error_msg}"},
                reasoning="Query execution failed",
                tokens_used=0,
                execution_time=time.time() - start_time,
                error=error_msg
            )
        
        # Handle empty results
        if not results:
            explanation = self._explain_empty_results(question, sql)
            return AgentResult(
                success=True,
                data={
                    "explanation": explanation,
                    "row_count": 0,
                    "has_data": False
                },
                reasoning="No results found",
                tokens_used=0,
                execution_time=time.time() - start_time
            )
        
        # Check if query is complex and might need splitting
        join_count = sql.upper().count('JOIN')
        should_check_split = join_count >= 2 and row_count > 0
        
        split_result = None
        if should_check_split:
            self.log(f"Checking if complex query (with {join_count} JOINs) should be split...", "info")
            split_tool_result = self.call_tool(
                "split_complex_query",
                question=question,
                original_sql=sql,
                schema_context=schema_context
            )
            tool_calls.append(split_tool_result)
            total_tokens += split_tool_result.tokens_used
            
            if split_tool_result.success and split_tool_result.data.get('should_split'):
                split_result = split_tool_result.data
                self.log("Query will be split into simpler parts", "info")
        
        # If splitting is recommended, execute split queries and explain each
        if split_result and split_result.get('should_split'):
            explanations = []
            queries_data = []
            
            for query_info in split_result.get('queries', []):
                query_sql = query_info.get('sql', '')
                query_desc = query_info.get('description', 'Query result')
                
                # Execute split query
                query_result = self.db.safe_execute(query_sql, timeout_seconds=30)
                
                if query_result.get('success'):
                    # Explain this split result
                    explain_result = self.call_tool(
                        "explain_results",
                        question=f"{question} - Focus: {query_desc}",
                        sql=query_sql,
                        results=query_result.get('data', []),
                        columns=query_result.get('columns', []),
                        row_count=query_result.get('row_count', 0),
                        max_rows_for_context=max_rows_for_context
                    )
                    tool_calls.append(explain_result)
                    total_tokens += explain_result.tokens_used
                    
                    explanations.append({
                        "description": query_desc,
                        "sql": query_sql,
                        "explanation": explain_result.data.get('explanation', '') if explain_result.success else "Failed to explain",
                        "row_count": query_result.get('row_count', 0)
                    })
                    
                    queries_data.append({
                        "sql": query_sql,
                        "data": query_result.get('data', [])[:10],  # Sample data
                        "columns": query_result.get('columns', []),
                        "row_count": query_result.get('row_count', 0)
                    })
            
            # Combine explanations
            combined_explanation = self._combine_split_explanations(question, explanations)
            
            return AgentResult(
                success=True,
                data={
                    "explanation": combined_explanation,
                    "is_split": True,
                    "split_queries": queries_data,
                    "individual_explanations": explanations,
                    "original_sql": sql
                },
                reasoning=f"Split complex query into {len(explanations)} simpler queries",
                tokens_used=total_tokens,
                execution_time=time.time() - start_time,
                tool_calls=tool_calls
            )
        
        # Single query explanation
        if row_count > max_rows_for_detail:
            # Use summary tool for large results
            self.log(f"Large result set ({row_count} rows), using summary mode", "info")
            tool_result = self.call_tool(
                "summarize_large_results",
                question=question,
                sql=sql,
                results=results,
                columns=columns,
                row_count=row_count
            )
        else:
            # Use detailed explanation for smaller results
            self.log(f"Explaining {row_count} rows in detail", "info")
            tool_result = self.call_tool(
                "explain_results",
                question=question,
                sql=sql,
                results=results,
                columns=columns,
                row_count=row_count,
                max_rows_for_context=max_rows_for_context
            )
        
        tool_calls.append(tool_result)
        total_tokens += tool_result.tokens_used
        
        if not tool_result.success:
            return AgentResult(
                success=False,
                data=None,
                reasoning="Failed to generate explanation",
                tokens_used=total_tokens,
                execution_time=time.time() - start_time,
                error=tool_result.error,
                tool_calls=tool_calls
            )
        
        explanation = tool_result.data.get('explanation') or tool_result.data.get('summary', '')
        
        self.log("Result explanation complete", "success")
        
        return AgentResult(
            success=True,
            data={
                "explanation": explanation,
                "row_count": row_count,
                "columns": columns,
                "has_data": True,
                "is_sampled": tool_result.data.get('is_sampled', False),
                "statistics": tool_result.data.get('statistics')
            },
            reasoning=f"Explained {row_count} rows of results",
            tokens_used=total_tokens,
            execution_time=time.time() - start_time,
            tool_calls=tool_calls
        )
    
    def _explain_empty_results(self, question: str, sql: str) -> str:
        """Generate explanation for empty results"""
        return f"""Based on your question "{question}", the query was executed successfully but returned no results.

This could mean:
• No data in the database matches your criteria
• The filters in the query might be too restrictive
• The specific values or conditions you're looking for don't exist in the current dataset

You might try:
• Broadening your search criteria
• Checking if the specific values exist in the database
• Rephrasing your question with different terms"""
    
    def _combine_split_explanations(self, question: str, explanations: List[Dict]) -> str:
        """Combine multiple explanations into a coherent response"""
        parts = [f"To answer your question: \"{question}\"\n"]
        parts.append("I've broken this down into separate analyses for clarity:\n")
        
        for i, exp in enumerate(explanations, 1):
            parts.append(f"\n**Part {i}: {exp['description']}**")
            parts.append(f"({exp['row_count']} results)")
            parts.append(exp['explanation'])
            parts.append("")
        
        return "\n".join(parts)
    
    def quick_explain(
        self,
        question: str,
        sql: str,
        execution_result: Dict[str, Any]
    ) -> str:
        """
        Quick explanation - returns just the explanation string
        
        Args:
            question: Original question
            sql: SQL query
            execution_result: Database execution result
            
        Returns:
            Natural language explanation string
        """
        result = self.execute(question, sql, execution_result)
        
        if result.success and result.data:
            return result.data.get('explanation', 'Unable to generate explanation.')
        else:
            return f"Unable to explain results: {result.error or 'Unknown error'}"

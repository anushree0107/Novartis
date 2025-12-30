"""
SQL Refinement Prompts for CHASE-SQL.

Implements the self-refinement loop with execution feedback.
"""

REFINEMENT_PROMPT = """
You are a PostgreSQL expert debugging a SQL query for a clinical trials database.

## Original Question:
{question}

## Generated SQL:
```sql
{sql_query}
```

## Execution Result:
{execution_feedback}

## Database Schema (relevant parts):
{schema_context}

## Instructions:
Analyze the error or issue and fix the SQL query.

Common issues to check:
1. **Syntax errors**: Missing commas, parentheses, quotes
2. **Table/column names**: Verify they exist in the schema
3. **Join conditions**: Ensure proper join paths exist
4. **Data types**: Ensure comparisons use correct types (strings need quotes)
5. **Aggregation**: If using GROUP BY, ensure SELECT columns are aggregated or grouped
6. **NULL handling**: Use IS NULL/IS NOT NULL instead of = NULL
7. **Enum values**: Use exact case and quotes for enum values

## Output:
1. Explain what went wrong
2. Describe the fix
3. Provide the corrected SQL in ```sql blocks
"""

EMPTY_RESULT_REFINEMENT_PROMPT = """
The SQL query executed successfully but returned 0 rows.

## Original Question:
{question}

## Generated SQL:
```sql
{sql_query}
```

## Analysis Needed:
1. Are the filter conditions too restrictive?
2. Are the join conditions correct?
3. Is the data actually present in the database?

## Sample Data Context:
{sample_data}

## Instructions:
Either:
- Explain why 0 rows is the correct answer
- Or fix the SQL if the filters/joins are wrong

Provide your analysis and corrected SQL (if needed) in ```sql blocks.
"""

VALIDATION_PROMPT = """
Review this SQL query for a clinical trials database and identify any issues.

## SQL Query:
```sql
{sql_query}
```

## Database Schema:
{schema_context}

## Checklist:
- [ ] All table names exist in schema
- [ ] All column names exist in their respective tables
- [ ] JOIN conditions use correct foreign keys
- [ ] WHERE clause values are properly quoted/typed
- [ ] Aggregation functions match GROUP BY
- [ ] No ambiguous column references

## Output:
List any issues found, or confirm the query is valid.
If issues exist, provide the corrected SQL in ```sql blocks.
"""

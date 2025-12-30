"""
SQL Generation Prompts for CHASE-SQL.

Implements multiple generation strategies: Chain-of-Thought, Query Decomposition, and Direct.
"""

# Chain-of-Thought SQL Generation
COT_SQL_GENERATION_PROMPT = """
You are an expert PostgreSQL developer for clinical trials databases.
Generate a SQL query to answer the user's question using step-by-step reasoning.

## Database Schema:
{schema_context}

## Question:
{question}

## Linked Schema Elements:
Tables: {linked_tables}
Key Columns: {linked_columns}
Join Path: {join_path}

## Instructions:
Think through this step by step:

### Step 1: Identify the output columns
What data should be returned? List the SELECT columns.

### Step 2: Identify the base table
Which table contains the primary data being queried?

### Step 3: Determine required JOINs
What tables need to be joined and on which columns?

### Step 4: Define filter conditions
What WHERE conditions are needed?

### Step 5: Add aggregations/grouping if needed
Is COUNT, SUM, AVG, etc. required? What GROUP BY is needed?

### Step 6: Add ordering if needed
Should results be sorted?

### Step 7: Construct the final SQL

## Output:
Provide your reasoning for each step, then output the final SQL query wrapped in ```sql blocks.
"""

# Query Decomposition Strategy
DECOMPOSITION_SQL_PROMPT = """
You are an expert PostgreSQL developer. Generate SQL by decomposing the question into sub-queries.

## Database Schema:
{schema_context}

## Question:
{question}

## Instructions:
Break down the question into simpler sub-queries, then combine them.

### Decomposition:
1. Identify independent sub-questions
2. Write a SQL query for each sub-question
3. Combine using JOINs, subqueries, or CTEs

### Example Approach:
For "Show sites with more than 10 open queries in Study 1":
- Sub-query 1: Get site_ids from Study 1
- Sub-query 2: Count open queries per subject
- Sub-query 3: Aggregate to site level
- Combine: Filter sites with count > 10

## Output:
First show the sub-queries with explanations, then provide the final combined SQL in ```sql blocks.
"""

# Direct Generation Strategy
DIRECT_SQL_PROMPT = """
You are an expert PostgreSQL developer for clinical trials databases.
Generate a SQL query to answer the following question.

## Database Schema:
{schema_context}

## Question:
{question}

## Guidelines:
- Use proper JOIN syntax (explicit INNER JOIN, LEFT JOIN)
- Use table aliases for readability
- Include appropriate WHERE filters
- Add ORDER BY for sorted results when logical
- Use LIMIT for potentially large result sets
- Handle NULL values appropriately

## Output:
Provide only the SQL query wrapped in ```sql blocks. No explanation needed.
"""

SQL_GENERATION_PROMPTS = {
    "cot": COT_SQL_GENERATION_PROMPT,
    "decomposition": DECOMPOSITION_SQL_PROMPT,
    "direct": DIRECT_SQL_PROMPT,
}

# Helpful SQL patterns for clinical trials queries
SQL_PATTERNS = {
    "count_by_status": """
        SELECT status, COUNT(*) as count
        FROM {table}
        GROUP BY status
        ORDER BY count DESC
    """,
    "count_by_site": """
        SELECT s.site_number, COUNT(*) as count
        FROM sites s
        JOIN subjects sub ON s.site_id = sub.site_id
        JOIN {table} t ON sub.subject_id = t.subject_id
        WHERE s.study_id = (SELECT study_id FROM studies WHERE study_code = '{study}')
        GROUP BY s.site_id, s.site_number
        ORDER BY count DESC
    """,
    "filter_by_study": """
        WHERE study_id = (SELECT study_id FROM studies WHERE study_code = '{study}')
    """,
    "filter_by_site": """
        WHERE site_id = (SELECT site_id FROM sites WHERE site_number = '{site}' 
                         AND study_id = (SELECT study_id FROM studies WHERE study_code = '{study}'))
    """,
}

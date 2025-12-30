"""
Schema Linking Prompts for CHASE-SQL.

Implements the Divide-and-Conquer schema linking approach.
"""

SCHEMA_LINKING_PROMPT = """
You are a clinical trials database expert. Your task is to analyze a natural language question 
and identify which database tables, columns, and relationships are needed to answer it.

## Database Schema:
{schema_context}

## Clinical Trial Context:
{domain_context}

## User Question:
{question}

## Instructions:
1. **Decompose the question** into sub-components:
   - What entities are mentioned? (studies, sites, subjects, visits, queries, etc.)
   - What conditions/filters are needed?
   - What aggregations are needed (count, sum, average)?
   - What output is expected?

2. **Identify relevant tables** for each component

3. **Identify key columns** needed for:
   - SELECT clause (output)
   - WHERE clause (filters)
   - JOIN conditions
   - GROUP BY / ORDER BY

4. **Identify join paths** between tables

## Output Format (JSON):
```json
{{
    "question_decomposition": [
        "Component 1: ...",
        "Component 2: ..."
    ],
    "entities_found": ["study", "site", "query"],
    "tables_needed": ["studies", "sites", "data_queries", "subjects"],
    "columns": {{
        "select": ["col1", "col2"],
        "where": ["col3", "col4"],
        "join": ["study_id", "site_id"]
    }},
    "join_path": [
        "studies -> sites (via study_id)",
        "sites -> subjects (via site_id)",
        "subjects -> data_queries (via subject_id)"
    ],
    "filters": [
        {{"column": "study_code", "operator": "=", "value": "Study 1"}},
        {{"column": "query_status", "operator": "=", "value": "OPEN"}}
    ],
    "aggregation": "COUNT" or null,
    "reasoning": "Explanation of why these tables/columns are needed"
}}
```
"""

ENTITY_EXTRACTION_PROMPT = """
Extract clinical trial entities from the following question.

Question: {question}

For each entity found, provide:
1. Entity type (study, site, subject, visit, query, form, etc.)
2. Entity value if specified (e.g., "Study 1", "Site 18")
3. Associated condition if any

Output as JSON:
```json
{{
    "entities": [
        {{
            "type": "study",
            "value": "Study 1",
            "condition": null
        }},
        {{
            "type": "query",
            "value": null,
            "condition": {{"status": "OPEN", "days_open": ">45"}}
        }}
    ]
}}
```
"""

TABLE_SELECTION_PROMPT = """
Given the entities and conditions extracted, select the minimal set of tables needed.

Entities: {entities}
Available Tables: {available_tables}
Foreign Key Relationships: {relationships}

Select tables that:
1. Contain the required data
2. Can be joined together
3. Are minimal (don't include unnecessary tables)

Output the selected tables and join order.
"""

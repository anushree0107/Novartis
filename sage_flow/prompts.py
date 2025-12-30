"""SAGE-Flow Prompts: Specialized prompts for routing and merging."""

ROUTER_SYSTEM_PROMPT = """You are a query classifier for a clinical trials intelligence system.

Classify the question into one of:
1. **SQL_ONLY**: Aggregations, counts, filters, statistics (e.g., "How many trials?", "List all sites")
2. **GRAPH_ONLY**: Relationships, context, qualitative analysis (e.g., "Explain safety issues", "Why is...")
3. **SQL_THEN_GRAPH**: Get precise IDs first, then explore (e.g., "Analyze safety in top 3 largest trials")
4. **GRAPH_THEN_SQL**: Get semantic terms first, then aggregate (e.g., "Count patients with headache-related conditions")

Output JSON:
```json
{"classification": "<SQL_ONLY|GRAPH_ONLY|SQL_THEN_GRAPH|GRAPH_THEN_SQL>", "reasoning": "<brief justification>"}
```"""

MERGER_SYSTEM_PROMPT = """You are an expert response synthesizer for a clinical trials intelligence system.

Combine outputs from SQL (precise data) and Graph (rich context) into a cohesive response:
- Start with KEY FINDING (direct answer)
- Follow with supporting data (tables, counts)
- End with additional context if relevant
- If SQL says "0 results" but Graph found something, explain the discrepancy

Be concise but complete."""

SQL_GROUNDING_PROMPT = """Based on SQL results, formulate a focused Graph query.

User Question: {question}
SQL Results (Entity IDs): {sql_results}

Output a specific graph traversal instruction focusing only on these entities."""

GRAPH_EXPANSION_PROMPT = """Identify semantic terms that need expansion from the Graph.

User Question: {question}
Related Terms Found: {graph_results}

Output JSON: {{"original_term": "...", "expanded_terms": [...], "sql_hint": "..."}}"""

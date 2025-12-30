"""HopRAG Prompts for LLM-based reasoning."""

PSEUDO_QUERY_PROMPT = """Given a clinical trial knowledge graph node, generate pseudo-queries.

Node Type: {node_type}
Node ID: {node_id}
Attributes:
{attributes}

Edges:
{edges}

Generate:
1. IN-COMING: Questions this node can answer
2. OUT-COMING: Questions that need other nodes to answer

Format:
IN_COMING:
- [question]

OUT_COMING:
- [question]
"""

BATCH_EDGE_REASONING_PROMPT = """Multi-hop reasoning task. For EACH of the following source nodes, select the ONE most helpful neighbor to traverse to answer the query.

User Query: "{query}"

Tasks:
{tasks_text}

Response Format (JSON):
{{
  "source_node_id_1": "selected_neighbor_id_or_NONE",
  "source_node_id_2": "selected_neighbor_id_or_NONE"
}}
"""

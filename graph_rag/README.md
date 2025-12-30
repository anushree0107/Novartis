# Clinical Trial Graph RAG

LangChain/LangGraph agent for clinical trial data analysis.

## Structure
```
graph_rag/
├── agent.py           # Main agent
├── graph_builder.py   # CSV → Graph
├── core/
│   ├── config.py      # Configuration
│   ├── base_tool.py   # Tool base classes
│   └── prompts.py     # System prompts
└── tools/
    ├── graph_tools.py   # 7 graph query tools
    └── code_executor.py # Pandas execution
```

## Quick Start
```python
from graph_rag import create_agent

agent = create_agent()
result = agent.query("Which sites have most pending safety reviews?")
print(result["output"])
```

## Tools
| Tool | Description |
|------|-------------|
| `get_study_info` | Study metrics |
| `find_subjects_with_issues` | High-risk subjects |
| `get_safety_reviews_by_site` | Reviews by site |
| `get_site_risk_summary` | Site risk analysis |
| `query_graph_flexible` | Custom cross-entity queries |
| `execute_python_code` | Pandas on CSVs |

## Environment
- `GOOGLE_API_KEY`: Required for LLM

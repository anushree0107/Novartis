# CHASE-SQL: Clinical Trials Text-to-SQL System

A Text-to-SQL system implementing the CHASE-SQL methodology for converting natural language queries 
into SQL against clinical trials databases.

## Features

- **Divide-and-Conquer Schema Linking**: Breaks complex queries into sub-queries and maps to relevant schema elements
- **Multi-Strategy SQL Generation**: Uses Chain-of-Thought, Query Decomposition, and Direct Generation
- **Self-Refinement Loop**: Iteratively fixes SQL using execution feedback
- **Clinical Domain Awareness**: Built-in knowledge of clinical trial terminology (EDC, SDV, SAE, MedDRA, etc.)

## Installation

```bash
cd /home/anushree/Novartis
pip install -r chase_sql/requirements.txt
```

## Usage

### CLI Mode
```bash
python -m chase_sql.main "Show all open queries for Study 1"
```

### Python API
```python
from chase_sql import ChaseSQL

chase = ChaseSQL(db_config={
    "host": "localhost",
    "database": "clinical_trials",
    "user": "postgres",
    "password": "your_password"
})

sql = chase.text_to_sql("How many subjects are enrolled in Study 1?")
print(sql)
# SELECT COUNT(*) FROM subjects s 
# JOIN studies st ON s.study_id = st.study_id 
# WHERE st.study_code = 'Study 1' AND s.status = 'ENROLLED'
```

## Configuration

Set your LLM provider in `config.py`:
- OpenAI GPT-4
- Google Gemini
- Anthropic Claude
- Local LLMs (via Ollama)

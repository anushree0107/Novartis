# Novartis Clinical Intelligence Platform

> **Dual-Mode Text-to-SQL System for Clinical Trial Analytics**

A unified platform combining two specialized approaches for natural language to SQL conversion over clinical trial data:

- **🧠 SAGE-CODE**: Graph RAG with Code-Augmented Reasoning (Planning Mode)
- **⚡ TRIALS**: Multi-Agent Text-to-SQL Pipeline (Fast Response Mode)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER QUERY                                    │
│                  "Which sites have highest DQI?"                     │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
                    ┌───────────────────┐
                    │   Query Router    │
                    │  (Mode Selector)  │
                    └───────────────────┘
                         /         \
                        /           \
            Complex Query          Simple Query
            Planning Mode          Fast Response
                      /               \
                     ▼                 ▼
    ┌────────────────────────┐   ┌────────────────────────┐
    │      SAGE-CODE         │   │        TRIALS          │
    │  ┌──────────────────┐  │   │  ┌──────────────────┐  │
    │  │  Knowledge Graph │  │   │  │ Info Retriever   │  │
    │  │   (Clinical)     │  │   │  └────────┬─────────┘  │
    │  └────────┬─────────┘  │   │           ▼            │
    │           ▼            │   │  ┌──────────────────┐  │
    │  ┌──────────────────┐  │   │  │ Schema Selector  │  │
    │  │ Multi-Hop RAG    │  │   │  └────────┬─────────┘  │
    │  │  + Reasoning     │  │   │           ▼            │
    │  └────────┬─────────┘  │   │  ┌──────────────────┐  │
    │           ▼            │   │  │ Candidate Gen    │  │
    │  ┌──────────────────┐  │   │  └────────┬─────────┘  │
    │  │ Code Executor    │  │   │           ▼            │
    │  │  (Analytics)     │  │   │  ┌──────────────────┐  │
    │  └──────────────────┘  │   │  │ Unit Tester      │  │
    │                        │   │  └────────┬─────────┘  │
    └────────────────────────┘   │           ▼            │
                                 │  ┌──────────────────┐  │
                                 │  │ Result Explainer │  │
                                 │  └──────────────────┘  │
                                 └────────────────────────┘
                         \                  /
                          \                /
                           ▼              ▼
                    ┌───────────────────────────┐
                    │      Response + SQL       │
                    │   Business Intelligence   │
                    └───────────────────────────┘
```

---

## 📁 Project Structure

```
Novartis/
├── sage_code/                    # SAGE-CODE: Graph RAG (Planning Mode)
│   ├── agent.py                  # SAGEAgent - Main interface
│   ├── engine.py                 # SAGEEngine - Core retrieval engine
│   ├── graph_builder.py          # ClinicalTrialGraphBuilder
│   ├── config.py                 # Configuration management
│   ├── prompts.py                # LLM prompts
│   ├── models.py                 # Data models (HopResult)
│   └── tools/                    # Agent tools
│       ├── base_tool.py          # Tool base classes
│       ├── code_executor.py      # Python code execution
│       └── graph_tools.py        # Graph query tools
│
├── trials/                       # TRIALS: Multi-Agent (Fast Response)
│   ├── agents/                   # 5 specialized agents
│   │   ├── base_agent.py         # Agent base class
│   │   ├── information_retriever.py
│   │   ├── schema_selector.py
│   │   ├── candidate_generator.py
│   │   ├── unit_tester.py
│   │   └── result_explainer.py
│   ├── pipeline/
│   │   └── orchestrator.py       # Agent orchestration
│   ├── preprocessing/
│   │   └── indexer.py            # LSH/Vector indexing
│   └── trials_sql.py             # Main entry point
│
├── shared/                       # Common utilities
│   ├── database/                 # Database connections
│   │   ├── connection.py
│   │   └── schema_manager.py
│   ├── config/                   # Configuration
│   │   ├── settings.py
│   │   └── table_descriptions.json
│   └── utils/                    # Shared utilities
│       ├── llm_client.py
│       └── token_utils.py
│
├── docs/                         # Documentation & Reports
│   ├── SAGE_CODE_Report.pdf
│   └── TRIALS_Report.pdf
│
├── processed_data/               # Clinical trial data
├── api/                          # REST API endpoints
└── tests/                        # Unit/integration tests
```

---

## 🧠 SAGE-CODE: Planning Mode

**Best for**: Complex analytical queries, multi-step reasoning, exploratory analysis

### Key Components

| Component | Description |
|-----------|-------------|
| **SAGEEngine** | Multi-hop graph retrieval with CoT reasoning |
| **ClinicalTrialGraphBuilder** | Builds knowledge graph from clinical data |
| **CodeExecutorTool** | Executes Python for advanced analytics |
| **GraphTools** | Study, site, and patient query tools |

### Algorithm
1. **Initial Retrieval** - Keyword + semantic search on graph nodes
2. **Multi-Hop Traversal** - Explore related entities via graph edges
3. **Chain-of-Thought Reasoning** - LLM-guided exploration decisions
4. **Code Generation** - Python code for complex analytics
5. **Executive Summary** - Business-focused insights

### Usage
```python
from sage_code import SAGEAgent

agent = SAGEAgent()
response = agent.query("Which sites have the highest enrollment rates and why?")
print(response.answer)
```

---

## ⚡ TRIALS: Fast Response Mode

**Best for**: Direct SQL queries, quick lookups, operational queries

### Key Components

| Agent | Role |
|-------|------|
| **InformationRetrieverAgent** | Extracts database hints using LSH + keywords |
| **SchemaSelectorAgent** | Selects relevant tables/columns |
| **CandidateGeneratorAgent** | Generates SQL candidates with ToT reasoning |
| **UnitTesterAgent** | Validates SQL execution |
| **ResultExplainerAgent** | Formats and explains results |

### Pipeline Flow
```
Query → IR Agent → Schema Agent → Generator → Tester → Explainer → Result
         ↓            ↓              ↓           ↓
      Hints        Schema        SQL Queries   Valid SQL
```

### Usage
```python
from trials import Orchestrator

orchestrator = Orchestrator()
result = orchestrator.run("Get enrollment count by site")
print(result.sql)
print(result.explanation)
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- PostgreSQL database
- Groq API key (or OpenRouter/Ollama)

### Installation

```bash
# Clone repository
git clone https://github.com/anushree0107/Novartis.git
cd Novartis
git checkout unified-text2sql

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys and database credentials
```

### Configuration

Create `.env` file:
```env
# LLM Configuration
GROQ_API_KEY=your_groq_api_key
OPENROUTER_API_KEY=your_openrouter_key

# Database Configuration  
DB_HOST=localhost
DB_PORT=5432
DB_NAME=clinical_trials
DB_USER=postgres
DB_PASSWORD=your_password
```

---

## 📊 Mode Selection Guide

| Query Type | Recommended Mode | Example |
|------------|------------------|---------|
| Simple lookup | TRIALS | "List all active studies" |
| Count/aggregate | TRIALS | "How many patients enrolled?" |
| Multi-entity analysis | SAGE-CODE | "Compare DQI across sites by region" |
| Root cause analysis | SAGE-CODE | "Why is Site 001 underperforming?" |
| Trend analysis | SAGE-CODE | "Enrollment trends over time with predictions" |

---

## 🔧 Configuration Options

### SAGE-CODE Config
```python
from sage_code import SAGEConfig

config = SAGEConfig(
    n_hops=3,              # Max graph traversal hops
    top_k=10,              # Top K initial retrievals
    beam_width=3,          # Beam search width
    min_score_threshold=0.3
)
```

### TRIALS Config
```python
from shared.config import Settings

settings = Settings(
    max_candidates=5,      # SQL candidates to generate
    execution_timeout=30,  # SQL timeout (seconds)
    use_caching=True       # Enable result caching
)
```

---

## 📚 Documentation

- [SAGE-CODE Technical Report](docs/SAGE_CODE_Report.pdf)
- [TRIALS Technical Report](docs/TRIALS_Report.pdf)
- [API Reference](docs/api_reference.md)

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Team

- Clinical Intelligence Platform Team
- Novartis AI/ML Engineering

---

*Built with ❤️ for better clinical trial analytics*

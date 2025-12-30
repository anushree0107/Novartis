# SAGE-Flow: SQL-Augmented Graph Execution Flow

A novel framework combining **Text2SQL** and **GraphRAG** for intelligent clinical trial data analysis.

## 🎯 The Problem

| Approach | Strength | Weakness |
|----------|----------|----------|
| **SQL** | Precise aggregations, filtering, statistics | No context, relationships, or reasoning |
| **Graph RAG** | Rich relationships, multi-hop reasoning | Struggles with "top N", exact counts |

**SAGE-Flow** combines both - routing queries to the optimal path and fusing results intelligently.

---

## 🏗️ Architecture

```mermaid
flowchart TB
    subgraph Input
        Q[/"🗣️ User Query"/]
    end
    
    subgraph SAGE-Flow["🔮 SAGE-Flow Orchestrator"]
        R{"🧭 Intent Router"}
        
        subgraph Agents["Parallel Agent Execution"]
            direction LR
            SQL["📊 Text2SQL Agent<br/>(CHESS Pipeline)"]
            GRAPH["🕸️ GraphRAG Agent<br/>(HopRAG Engine)"]
        end
        
        M["🔀 Smart Merger"]
    end
    
    subgraph DataSources["Data Sources"]
        DB[(PostgreSQL<br/>Clinical Data)]
        KG[(Knowledge Graph<br/>424K nodes)]
    end
    
    subgraph Output
        A[/"📋 Unified Answer"/]
    end
    
    Q --> R
    
    R -->|SQL_ONLY| SQL
    R -->|GRAPH_ONLY| GRAPH
    R -->|SQL_THEN_GRAPH| SQL
    R -->|GRAPH_THEN_SQL| GRAPH
    
    SQL --> DB
    GRAPH --> KG
    
    SQL --> M
    GRAPH --> M
    M --> A
    
    style R fill:#ff9800,stroke:#333
    style SQL fill:#2196f3,stroke:#333
    style GRAPH fill:#4caf50,stroke:#333
    style M fill:#9c27b0,stroke:#333
```

---

## 🔄 Execution Flows

### Flow 1: SQL Only
```mermaid
sequenceDiagram
    participant U as User
    participant R as Router
    participant S as Text2SQL
    participant M as Merger
    
    U->>R: "How many trials in Phase 3?"
    R->>S: SQL_ONLY
    S->>S: Generate SQL
    S->>S: Execute Query
    S->>M: {rows: 42}
    M->>U: "There are 42 Phase 3 trials"
```

### Flow 2: Graph Only
```mermaid
sequenceDiagram
    participant U as User
    participant R as Router
    participant G as GraphRAG
    participant M as Merger
    
    U->>R: "Explain safety issues at Site 637"
    R->>G: GRAPH_ONLY
    G->>G: HopRAG Multi-hop Traversal
    G->>G: LLM Reasoning
    G->>M: {narrative: "Site 637 has..."}
    M->>U: Detailed safety analysis
```

### Flow 3: SQL → Graph (Grounded Traversal)
```mermaid
sequenceDiagram
    participant U as User
    participant R as Router
    participant S as Text2SQL
    participant G as GraphRAG
    participant M as Merger
    
    U->>R: "Analyze safety in TOP 3 largest trials"
    R->>S: Get top 3 trial IDs
    S->>S: SELECT trial_id ORDER BY size LIMIT 3
    S-->>G: [Trial_001, Trial_002, Trial_003]
    G->>G: Traverse ONLY these 3 nodes
    G->>M: Grounded analysis
    S->>M: Precise IDs
    M->>U: Combined answer (no hallucination!)
```

### Flow 4: Graph → SQL (Semantic Expansion)
```mermaid
sequenceDiagram
    participant U as User
    participant R as Router
    participant G as GraphRAG
    participant S as Text2SQL
    participant M as Merger
    
    U->>R: "Count patients with headache conditions"
    R->>G: Find related terms
    G->>G: Ontology lookup
    G-->>S: ["headache", "migraine", "cephalgia"]
    S->>S: SELECT ... WHERE condition IN (expanded terms)
    S->>M: Count: 847
    G->>M: Semantic context
    M->>U: "847 patients (including migraine, cephalgia)"
```

---

## 📦 Project Structure

```
sage_flow/               # 🔮 Main SAGE-Flow Module
├── orchestrator.py      # Entry point, parallel execution
├── router.py            # Fast heuristics + LLM classification
├── merger.py            # Trust hierarchy, conflict detection
└── prompts.py           # LLM prompts

graph_rag/               # 🕸️ GraphRAG Components
├── agent.py             # LangChain ReAct agent
├── hop_rag/             # Multi-hop reasoning engine
│   ├── engine.py        # HopRAG core
│   └── config.py        # Tunable parameters
└── tools/               # Graph query tools

pipeline/                # 📊 Text2SQL (CHESS)
└── orchestrator.py      # 5-agent SQL pipeline

agents/                  # CHESS SQL Agents
├── information_retriever.py
├── schema_selector.py
├── candidate_generator.py
├── unit_tester.py
└── result_explainer.py
```

---

## 🚀 Quick Start

```python
from sage_flow import create_sage_flow

orchestrator = create_sage_flow(verbose=True)
result = orchestrator.query("Which sites require immediate attention?")
print(result.answer)
```

```bash
cd sage_flow && python orchestrator.py
```

---

## ⚡ Performance

| Metric | Value |
|--------|-------|
| Routing | ~1s |
| SQL | ~0.5s |
| Graph | 3-8s |
| **Total** | **5-15s** |

---

## 🔧 Configuration

Edit `graph_rag/hop_rag/config.py`:
```python
@dataclass
class HopRAGConfig:
    n_hops: int = 3                    # Traversal depth
    use_llm_reasoning: bool = True     # Enable LLM for edge selection
    max_llm_calls_per_query: int = 5   # LLM call budget
    fast_mode_threshold: float = 0.9   # Skip LLM if high confidence
```

---

*SAGE-Flow: Combining the precision of SQL with the intelligence of Graphs.*

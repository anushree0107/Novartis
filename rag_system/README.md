# GEPA-Optimized RAG System for Clinical Trial Data

A **Retrieval-Augmented Generation (RAG)** system optimized using **GEPA (Generic Evolutionary Prompt Adaptation)** for analyzing NEST 2.0 anonymized clinical trial data.

## 🎯 Features

- **GEPA Prompt Optimization**: Evolutionary optimization of RAG prompts for better retrieval and generation
- **Free API Models**: Uses Groq/Together AI/HuggingFace - no local GPU needed!
- **Clinical Data Focus**: Optimized for pharmaceutical study data (EDC metrics, safety reports, coding data)
- **ChromaDB Vector Store**: Persistent local vector storage for fast retrieval
- **Web Interface**: Streamlit-based UI for easy interaction

## 🚀 Quick Start

### Prerequisites

Get a **FREE API key** from one of these providers:

| Provider | Free Tier | Speed | Sign Up |
|----------|-----------|-------|---------|
| **Groq** (Recommended) | Free, generous limits | ⚡ Very Fast | [console.groq.com](https://console.groq.com/keys) |
| **Together AI** | $25 free credits | Fast | [api.together.xyz](https://api.together.xyz/) |
| **HuggingFace** | Free tier | Moderate | [huggingface.co](https://huggingface.co/settings/tokens) |

### Installation

```bash
# Navigate to the project
cd novartis/rag_system

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Setup your API key
copy .env.example .env
# Then edit .env and add your API key
```

### Configure API Key

Edit the `.env` file:

```env
# Use Groq (recommended - fastest)
GROQ_API_KEY=your_groq_api_key_here
LLM_PROVIDER=groq

# OR use Together AI
TOGETHER_API_KEY=your_together_api_key_here
LLM_PROVIDER=together

# OR use HuggingFace
HUGGINGFACE_API_KEY=your_huggingface_api_key_here
LLM_PROVIDER=huggingface
```

### Usage

#### 1. Index the Clinical Data

```bash
# First time setup - load and index NEST 2.0 data
python main.py --index

# Force reload if needed
python main.py --index --force-reload
```

#### 2. Query the System

```bash
# Single query
python main.py --query "What is the EDC metrics data for Study 1?"

# Interactive mode
python main.py --interactive
```

#### 3. Run GEPA Optimization (Optional)

```bash
# Optimize prompts using GEPA evolutionary algorithm
python main.py --optimize
```

#### 4. Web Interface

```bash
# Launch Streamlit app
streamlit run app.py
```

## 📁 Project Structure

```
rag_system/
├── main.py                 # Main entry point
├── app.py                  # Streamlit web interface
├── requirements.txt        # Python dependencies
├── .env.example            # Environment template
├── .env                    # Your API keys (create this)
├── config/
│   ├── __init__.py
│   └── gepa_settings.py    # GEPA and RAG configuration
├── src/
│   ├── data_loader.py      # Clinical data loading utilities
│   └── gepa_rag_adapter.py # GEPA-optimized RAG adapter
├── vector_stores/          # ChromaDB persistence (auto-created)
└── logs/                   # Application logs (auto-created)
```

## ⚙️ Configuration

### Model Configuration (in `config/gepa_settings.py`)

```python
# Available FREE API providers
MODEL_CONFIG = {
    "groq": {
        "llm_model": "groq/llama-3.1-70b-versatile",
        "llm_model_fast": "groq/llama-3.1-8b-instant",
    },
    "together": {
        "llm_model": "together_ai/meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
    },
    "huggingface": {
        "llm_model": "huggingface/meta-llama/Llama-3.2-3B-Instruct",
    }
}
```

### RAG Configuration

```python
RAG_CONFIG = {
    "retrieval_strategy": "similarity",
    "top_k": 7,
    "chunk_size": 1000,
    "chunk_overlap": 200
}
```

### GEPA Optimization Settings

```python
GEPA_CONFIG = {
    "max_metric_calls": 15,
    "retrieval_weight": 0.35,
    "generation_weight": 0.65
}
```

## 🔧 GEPA Framework

GEPA (Generic Evolutionary Prompt Adaptation) optimizes four key RAG components:

1. **Query Reformulation**: Transforms user queries for better retrieval
2. **Context Synthesis**: Combines retrieved documents coherently
3. **Answer Generation**: Produces accurate, well-structured answers
4. **Document Reranking**: Improves relevance ordering of results

### How GEPA Works

```
Initial Prompts → Mutation → Evaluation → Selection → Repeat
                     ↓           ↓           ↓
               Evolved      Score on     Best prompts
               variants     train/val    survive
```

## 📊 Supported Data Types

The system handles NEST 2.0 clinical trial reports:

| Report Type | Description |
|-------------|-------------|
| EDRR | Electronic Data Review Report |
| EDC_Metrics | Electronic Data Capture metrics |
| eSAE | Safety adverse event dashboard |
| MedDRA_Coding | Medical Dictionary coding |
| WHODD_Coding | WHO Drug Dictionary coding |
| Missing_Pages | Missing data page reports |
| Lab_Ranges | Laboratory reference ranges |
| Inactivated_Forms | Inactivated records tracking |
| Visit_Tracker | Visit projection and completion |

## 🖥️ Example Queries

```bash
# EDC metrics query
"What is the EDC metrics data for Study 1?"

# Safety data query
"Show me safety adverse events from the eSAE dashboards"

# Coding query
"What MedDRA coding information is available?"

# Comparison query
"Compare data quality across Study 1 and Study 10"

# Missing data query
"What laboratory tests have missing reference ranges?"
```

## 🐛 Troubleshooting

### API Key not working
```bash
# Check your .env file has the correct key
# Make sure LLM_PROVIDER matches your API key
```

### Rate limiting
```bash
# Switch to a different provider in .env
LLM_PROVIDER=together  # or huggingface
```

### Empty vector store
```bash
# Re-index the data
python main.py --index --force-reload
```

## 📝 License

For internal use only - NEST 2.0 clinical data analysis.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Submit pull request

---

Built with ❤️ using GEPA, ChromaDB, and Free LLM APIs (Groq/Together/HuggingFace)

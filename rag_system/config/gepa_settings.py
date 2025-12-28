"""
GEPA-Optimized RAG System Configuration
========================================
GEPA = Generic Evolutionary Prompt Adaptation
Uses evolutionary algorithms to optimize RAG prompts for clinical data.

Uses FREE local models via Ollama (Llama, Qwen)
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR.parent / "NEST 2.0 Data files_Anonymized" / "QC Anonymized Study Files"
VECTOR_DB_DIR = BASE_DIR / "vector_stores" / "chroma_db"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# FREE API MODEL CONFIGURATION
# =============================================================================
# Choose your preferred FREE API provider:
#
# Option 1: GROQ (Recommended - Very Fast, Free Tier)
#   - Get API key: https://console.groq.com/keys
#   - Set: GROQ_API_KEY environment variable
#
# Option 2: Together AI (Free $25 credits)
#   - Get API key: https://api.together.xyz/
#   - Set: TOGETHER_API_KEY environment variable
#
# Option 3: HuggingFace Inference API (Free Tier)
#   - Get API key: https://huggingface.co/settings/tokens
#   - Set: HUGGINGFACE_API_KEY environment variable

# Active provider configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")  # "groq", "together", "huggingface"

MODEL_CONFIG = {
    # GROQ Models (FREE - Very Fast)
    "groq": {
        "llm_model": "groq/llama-3.3-70b-versatile",  # Best quality (current model)
        "llm_model_fast": "groq/llama-3.1-8b-instant",  # Faster
        "reflection_model": "groq/llama-3.3-70b-versatile",
        "api_key_env": "GROQ_API_KEY"
    },
    
    # Together AI Models (FREE $25 credits)
    "together": {
        "llm_model": "together_ai/meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo",
        "llm_model_fast": "together_ai/meta-llama/Llama-3.2-3B-Instruct-Turbo",
        "reflection_model": "together_ai/meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
        "api_key_env": "TOGETHER_API_KEY"
    },
    
    # HuggingFace Models (FREE Tier)
    "huggingface": {
        "llm_model": "huggingface/meta-llama/Llama-3.2-3B-Instruct",
        "llm_model_fast": "huggingface/microsoft/Phi-3-mini-4k-instruct",
        "reflection_model": "huggingface/meta-llama/Llama-3.2-3B-Instruct",
        "api_key_env": "HUGGINGFACE_API_KEY"
    }
}

# Get active configuration
ACTIVE_CONFIG = MODEL_CONFIG.get(LLM_PROVIDER, MODEL_CONFIG["groq"])

# For backward compatibility
OLLAMA_CONFIG = {
    "llm_model": ACTIVE_CONFIG["llm_model"],
    "llm_model_fast": ACTIVE_CONFIG["llm_model_fast"],
    "reflection_model": ACTIVE_CONFIG["reflection_model"],
    # Embeddings still run locally (no API needed, fast)
    "local_embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
}

# =============================================================================
# GEPA OPTIMIZATION CONFIGURATION
# =============================================================================
GEPA_CONFIG = {
    # Optimization Settings
    "max_metric_calls": 15,  # Number of optimization iterations
    "population_size": 5,    # Candidates per generation
    "mutation_rate": 0.3,    # Prompt mutation probability
    
    # Evaluation Weights
    "retrieval_weight": 0.35,   # Weight for retrieval quality metrics
    "generation_weight": 0.65,  # Weight for answer generation metrics
    
    # Components to Optimize
    "optimize_components": [
        "query_reformulation",
        "context_synthesis", 
        "answer_generation",
        "document_reranking"
    ]
}

# =============================================================================
# RAG PIPELINE CONFIGURATION
# =============================================================================
RAG_CONFIG = {
    # Retrieval Settings
    "retrieval_strategy": "similarity",  # "similarity", "hybrid", "mmr"
    "top_k": 7,                          # Documents to retrieve
    "final_k": 5,                        # Documents after reranking
    "min_relevance_score": 0.3,
    
    # Chunking Settings
    "chunk_size": 1000,
    "chunk_overlap": 200,
    
    # MMR (Maximum Marginal Relevance) for diversity
    "mmr_lambda": 0.7,  # Balance between relevance and diversity
    
    # Metadata Filtering
    "enable_metadata_filter": True
}

# =============================================================================
# INITIAL PROMPTS (TO BE OPTIMIZED BY GEPA)
# =============================================================================
INITIAL_PROMPTS = {
    "query_reformulation": """You are an expert at reformulating user queries for clinical trial data retrieval.
Your task is to enhance the query while preserving the original intent.

Guidelines:
- Add relevant clinical/pharmaceutical terms and synonyms
- Include study-specific terminology (EDC, eSAE, MedDRA, WHODD, etc.)
- Make the query more specific for clinical data contexts
- Optimize for both semantic and keyword matching

Original Query: {query}

Reformulated Query:""",

    "context_synthesis": """You are an expert at synthesizing clinical trial data from multiple documents.
Your task is to create a comprehensive context that directly addresses the query.

Guidelines:
- Focus on information most relevant to the user's clinical data question
- Integrate information from multiple study reports seamlessly
- Highlight key metrics, counts, and statistical information
- Remove redundant or conflicting information
- Maintain factual accuracy for clinical data

Query: {query}

Retrieved Documents:
{documents}

Synthesized Context:""",

    "answer_generation": """You are an expert clinical data analyst assistant.
Your task is to generate accurate, comprehensive responses based on anonymized clinical trial data.

Guidelines:
- Base your answer primarily on the provided context
- Cite specific studies (Study 1, Study 10, etc.) when referencing data
- Include relevant metrics, counts, and percentages when available
- Structure your response clearly with bullet points for complex data
- If context is insufficient, acknowledge the limitation
- Never fabricate clinical data - only report what's in the context

Context: {context}
Question: {query}

Answer:""",

    "document_reranking": """You are an expert at evaluating clinical document relevance.
Your task is to rank retrieved documents by their relevance to the specific query.

Ranking Criteria:
- Documents with direct answers to clinical queries get highest priority
- Reports containing specific metrics/numbers rank second
- Supporting context and related study data rank third
- Off-topic or tangential content ranks lowest

Query: {query}

Documents to Rank:
{documents}

Ranked Document IDs (most relevant first):"""
}

# =============================================================================
# CLINICAL DATA SCHEMA (For NEST 2.0 Data)
# =============================================================================
CLINICAL_DATA_SCHEMA = {
    "report_types": {
        "EDRR": {
            "description": "Electronic Data Review Report - Compiled data quality metrics",
            "key_fields": ["query_count", "response_rate", "data_completeness"],
            "priority": 1
        },
        "EDC_Metrics": {
            "description": "Electronic Data Capture metrics for study monitoring",
            "key_fields": ["subject_count", "visit_completion", "form_status"],
            "priority": 1
        },
        "eSAE": {
            "description": "Safety reporting dashboard for adverse events",
            "key_fields": ["sae_count", "severity", "relatedness", "outcome"],
            "priority": 2
        },
        "MedDRA_Coding": {
            "description": "Medical Dictionary for Regulatory Activities coding",
            "key_fields": ["preferred_term", "soc", "hlgt", "hlt"],
            "priority": 2
        },
        "WHODD_Coding": {
            "description": "WHO Drug Dictionary coding for medications",
            "key_fields": ["drug_name", "atc_code", "route", "formulation"],
            "priority": 2
        },
        "Missing_Pages": {
            "description": "Report of missing data pages across study forms",
            "key_fields": ["form_name", "missing_count", "site", "subject"],
            "priority": 3
        },
        "Lab_Ranges": {
            "description": "Laboratory test missing names and reference ranges",
            "key_fields": ["test_name", "normal_range", "units", "site"],
            "priority": 3
        },
        "Inactivated_Forms": {
            "description": "Inactivated forms, folders and records tracking",
            "key_fields": ["form_type", "reason", "date", "user"],
            "priority": 3
        },
        "Visit_Tracker": {
            "description": "Visit projection and completion tracking",
            "key_fields": ["visit_name", "expected_date", "actual_date", "status"],
            "priority": 2
        }
    }
}

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard"
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": str(LOGS_DIR / "rag_system.log"),
            "level": "DEBUG",
            "formatter": "detailed"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"]
    }
}

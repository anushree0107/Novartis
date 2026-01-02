"""
Configuration settings for the Text-to-SQL system
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Groq API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# LLM Models - Using Groq's currently available models
MODELS = {
    "schema_selector": "llama-3.3-70b-versatile",   # For schema selection
    "sql_generator": "llama-3.3-70b-versatile",     # For SQL generation
    "sql_refiner": "llama-3.3-70b-versatile",       # For SQL refinement
    "evaluator": "llama-3.1-8b-instant"             # For quick evaluation (faster model)
}

# Token limits for optimization
TOKEN_LIMITS = {
    "max_schema_tokens": 4000,      # Max tokens for schema context
    "max_examples_tokens": 1500,    # Max tokens for few-shot examples
    "max_query_tokens": 500,        # Max tokens for generated query
    "total_context_limit": 8000     # Total context window limit
}

# PostgreSQL Configuration
DATABASE_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "clinical_trials"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres")
}

# Data paths
DATA_ROOT_PATH = os.getenv(
    "DATA_ROOT_PATH", 
    r"C:\Users\agniv\OneDrive\Documents\Nova-text-to-sql\NEST 2.0 Data files_Anonymized\QC Anonymized Study Files"
)

# Agent configurations
AGENT_CONFIG = {
    "max_retries": 3,
    "temperature": 0.1,  # Low temperature for more deterministic outputs
    "top_candidates": 3,  # Number of SQL candidates to generate
}

# Schema cache settings
SCHEMA_CACHE_PATH = os.path.join(os.path.dirname(__file__), "..", "cache", "schema_cache.json")

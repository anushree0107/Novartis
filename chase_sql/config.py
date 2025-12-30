"""
CHASE-SQL Configuration

Configure your LLM provider and database connection settings here.
"""
import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum


class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    GOOGLE = "google"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    OLLAMA = "ollama"  # Local LLMs


@dataclass
class LLMConfig:
    """LLM provider configuration"""
    provider: LLMProvider = LLMProvider.GROQ
    model: str = "llama-3.3-70b-versatile"
    api_key: Optional[str] = None
    base_url: Optional[str] = None  # For Ollama or custom endpoints
    temperature: float = 0.0  # Low temperature for deterministic SQL generation
    max_tokens: int = 2048
    
    def __post_init__(self):
        # Try to load API key from environment
        if self.api_key is None:
            env_key_map = {
                LLMProvider.OPENAI: "OPENAI_API_KEY",
                LLMProvider.GOOGLE: "GOOGLE_API_KEY",
                LLMProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
                LLMProvider.GROQ: "GROQ_API_KEY",
            }
            if self.provider in env_key_map:
                self.api_key = os.getenv(env_key_map[self.provider])


@dataclass
class DatabaseConfig:
    """PostgreSQL database configuration"""
    host: str = "localhost"
    port: int = 5432
    database: str = "clinical_trials"
    user: str = "postgres"
    password: Optional[str] = None
    schema: str = "public"
    
    def __post_init__(self):
        if self.password is None:
            self.password = os.getenv("POSTGRES_PASSWORD", "")
    
    @property
    def connection_string(self) -> str:
        """Return psycopg2-compatible connection string"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class ChaseConfig:
    """Main CHASE-SQL configuration"""
    llm: LLMConfig = field(default_factory=LLMConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    
    # Schema linking settings
    max_tables_in_context: int = 15  # Max tables to include in prompt
    include_sample_data: bool = True
    sample_rows_per_table: int = 3
    
    # SQL generation settings
    generation_strategies: list = field(default_factory=lambda: ["cot", "decomposition", "direct"])
    num_candidates_per_strategy: int = 1
    
    # Refinement settings
    max_refinement_iterations: int = 3
    execute_for_validation: bool = True
    
    # Paths
    schema_path: str = "/home/anushree/Novartis/database/schema.sql"
    data_path: str = "/home/anushree/Novartis/Data/NEST 2.0 data"
    
    # Debug settings
    verbose: bool = False
    log_prompts: bool = False


# Default configuration instance
default_config = ChaseConfig()


def load_config_from_env() -> ChaseConfig:
    """Load configuration from environment variables"""
    return ChaseConfig(
        llm=LLMConfig(
            provider=LLMProvider(os.getenv("CHASE_LLM_PROVIDER", "groq")),
            model=os.getenv("CHASE_LLM_MODEL", "llama-3.3-70b-versatile"),
            api_key=os.getenv("CHASE_LLM_API_KEY"),
            temperature=float(os.getenv("CHASE_LLM_TEMPERATURE", "0.0")),
        ),
        database=DatabaseConfig(
            host=os.getenv("CHASE_DB_HOST", "localhost"),
            port=int(os.getenv("CHASE_DB_PORT", "5432")),
            database=os.getenv("CHASE_DB_NAME", "clinical_trials"),
            user=os.getenv("CHASE_DB_USER", "postgres"),
            password=os.getenv("CHASE_DB_PASSWORD", ""),
        ),
        verbose=os.getenv("CHASE_VERBOSE", "false").lower() == "true",
    )

"""
NEXUS Text-to-SQL System
========================
Natural language EXecution and Understanding System
A multi-agent framework for clinical trial data querying.

Usage:
    from nexus_sql import NexusPipeline, create_pipeline
    
    pipeline = create_pipeline()
    result = pipeline.run("How many patients are in Study 1?")
    print(result.sql)
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline.orchestrator import NexusPipeline, PipelineResult, create_pipeline
from agents import (
    InformationRetrieverAgent,
    SchemaSelectorAgent,
    CandidateGeneratorAgent,
    UnitTesterAgent
)
from database.connection import DatabaseManager, db_manager
from database.schema_manager import SchemaManager, schema_manager
from preprocessing.indexer import DatabasePreprocessor, preprocessor

__version__ = "1.0.0"
__all__ = [
    'NexusPipeline',
    'PipelineResult', 
    'create_pipeline',
    'InformationRetrieverAgent',
    'SchemaSelectorAgent',
    'CandidateGeneratorAgent',
    'UnitTesterAgent',
    'DatabaseManager',
    'db_manager',
    'SchemaManager',
    'schema_manager',
    'DatabasePreprocessor',
    'preprocessor'
]


def main():
    """Main entry point for CLI"""
    from cli.main import app
    app()


if __name__ == "__main__":
    main()


import sys
import os
import logging
from typing import List, Tuple, Dict

# Setup path
sys.path.insert(0, os.getcwd())

from graph_rag.tools.code_executor import create_code_executor_tool

# Setup logging
logging.basicConfig(level=logging.INFO)

def test_schema_context():
    print("Testing Rich Schema Context Extraction...")
    
    # Initialize Tool
    data_dir = os.path.join(os.getcwd(), "processed_data")
    tool = create_code_executor_tool(data_dir=data_dir)
    
    # Extract Context
    context = tool.get_schema_context()
    
    print("\n=== GENERATED SCHEMA CONTEXT ===")
    print(context)
    print("================================")
    
    # Validation
    if "DataFrame:" in context and "e.g.," in context:
        print("\n✅ SUCCESS: Context contains DataFrames and Sample Values.")
    else:
        print("\n❌ FAILURE: Context missing expected details.")

if __name__ == "__main__":
    test_schema_context()

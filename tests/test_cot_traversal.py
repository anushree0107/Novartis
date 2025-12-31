
import sys
import os
import logging

# Ensure we can import the module
sys.path.insert(0, os.getcwd())

from graph_rag.agent import create_agent

# Configure logging to see our custom logs
logging.basicConfig(level=logging.INFO)

def test_cot():
    print("Initializing Agent...")
    agent = create_agent(auto_load=True)
    
    # Check config
    print(f"CoT Enabled: {agent._get_hop_engine().config.use_cot_guided_traversal}")
    
    # Increase hops to cover Site -> Subject -> Visit -> Form -> MissingPage (Just in case it traverses)
    agent.config.hop_rag.n_hops = 4
    
    # This query SHOULD trigger the Graph Traversal Path (Relationship)
    query = "What study is Site 637 associated with?"
    print(f"\nRunning Query: {query}")
    
    result = agent.query(query)
    
    print("\n=== RESULT ===")
    print(result.get('output'))
    print(f"Context Length: {len(result.get('context', ''))}")
    
    if result.get('error'):
        print(f"ERROR: {result.get('output')}")

if __name__ == "__main__":
    test_cot()

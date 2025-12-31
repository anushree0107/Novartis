
import sys
import os
import logging
from typing import List, Tuple, Dict

# Setup path
sys.path.insert(0, os.getcwd())

from graph_rag.agent import create_agent
from graph_rag.hop_rag.engine import CodeAugmentedGraphEngine

# Mock Graph for testing
import networkx as nx
G = nx.DiGraph()
G.add_node("Site:101", node_type="Site", description="Clinical Site 101")
G.add_node("Random:XYZ", node_type="Equipment", description="A random medical device")
G.add_node("Study:S1", node_type="Study", description="Oncology Study")

logging.basicConfig(level=logging.INFO)

def test_pruning():
    print("Testing Data-Aware Pruning...")
    
    # Initialize Engine manually to test selection logic directly
    engine = CodeAugmentedGraphEngine(graph=G)
    engine.config.use_llm_selection = True
    
    query = "Count the missing pages for all sites."
    
    # Candidates: One High Value (Site), One Low Value (Random)
    candidates = [
        ("Site:101", {"edge_type": "LINK"}), 
        ("Random:XYZ", {"edge_type": "LINK"}),
        ("Study:S1", {"edge_type": "LINK"})
    ]
    
    print(f"\nQuery: {query}")
    print("Candidates: Site:101 vs Random:XYZ")
    
    scored = engine.select_candidates_llm_batched(query, candidates)
    
    print("\nSearch Results (Scores 0-1):")
    for nid, _, score in scored:
        print(f"- {nid}: {score}")
        
    # Validation
    site_score = next((s for n, _, s in scored if n == "Site:101"), 0)
    rand_score = next((s for n, _, s in scored if n == "Random:XYZ"), 0)
    
    if site_score > rand_score:
        print("\n✅ SUCCESS: Data-Aware Pruning worked! Site scored higher than Random.")
    else:
        print("\n❌ FAILURE: Pruning logic failed.")

if __name__ == "__main__":
    test_pruning()

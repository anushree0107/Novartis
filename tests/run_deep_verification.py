
import sys
import os
import logging
import time

# Ensure we can import the module
sys.path.insert(0, os.getcwd())

from graph_rag.agent import create_agent

# Configure logging to show our specific "Novelty" logs
logging.basicConfig(level=logging.INFO, format='%(name)s: %(message)s')
logger = logging.getLogger("hop_rag")
logger.setLevel(logging.INFO)

def run_test(name, query, expected_behavior_desc):
    print(f"\n{'='*60}")
    print(f"🧪 TEST: {name}")
    print(f"❓ Query: {query}")
    print(f"🎯 Expectation: {expected_behavior_desc}")
    print(f"{'='*60}\n")
    
    # Re-create agent for fresh state
    agent = create_agent(auto_load=True)
    
    # Ensure "Deep Reasoner" config is active
    hop_engine = agent._get_hop_engine()
    hop_engine.config.max_llm_calls_per_query = 15
    hop_engine.config.selection_batch_size = 20
    hop_engine.config.top_k = 15
    
    start_time = time.time()
    result = agent.query(query)
    duration = time.time() - start_time
    
    print(f"\n✅ Result ({duration:.2f}s):")
    if isinstance(result, dict) and 'output' in result:
         print(f"{result['output']}")
         print(f"\n[Meta] Hop Results: {result.get('hop_results')}")
    else:
         print(result)
    print("\n")

def main():
    print("🚀 Starting Deep Reasoner Verification Suite 🚀\n")
    
    # 1. Analytical Test (Code Augmentation)
    run_test(
        name="Analytical Query (Code Augmentation)",
        query="List eSAE events by study",
        expected_behavior_desc="Agent should Write Code -> Execute Code -> Return exact counts (Site 2: 160...)"
    )
    
    # 2. Relational Test (Intelligent Fallback)
    run_test(
        name="Relational Query (Fallback Logic)",
        query="What study is Site 637 associated with?",
        expected_behavior_desc="Agent may try Code -> Get Empty Result -> REASON 'Code failed' -> TRAVERSE Graph -> Find Answer."
    )
    
    print("\n🎉 Verification Suite Complete! check the logs above to see 'Action Verified' and 'Data-Aware Tagging' in action.")

if __name__ == "__main__":
    main()

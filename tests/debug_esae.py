
import sys
import os
import logging
from graph_rag.agent import create_agent

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hop_rag")
logger.setLevel(logging.INFO)

def debug_esae():
    print("🐞 Debugging 'List eSAE events by study'...")
    
    agent = create_agent(auto_load=True)
    hop_engine = agent._get_hop_engine()
    
    # Use "Optimized" Config
    hop_engine.config.max_llm_calls_per_query = 15
    hop_engine.config.selection_batch_size = 20
    hop_engine.config.top_k = 15
    
    query = "List eSAE events by study"
    print(f"\nQuery: {query}")
    
    try:
        result = agent.query(query)
        print("\n✅ Result:")
        print(result.get('output'))
    except Exception as e:
        print(f"\n❌ CRITICAL FAILURE: {e}")

if __name__ == "__main__":
    debug_esae()

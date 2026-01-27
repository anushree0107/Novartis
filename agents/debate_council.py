import os
from typing import TypedDict, List, Annotated, Dict, Any
import operator
import networkx as nx
import pandas as pd
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

load_dotenv()

# Config
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = "llama-3.3-70b-versatile"

class DebateState(TypedDict):
    site_id: str
    messages: Annotated[List[BaseMessage], operator.add]
    current_speaker: str
    round_count: int
    verdict: str
    site_data: str  # Pre-fetched data for the site

class DebateCouncil:
    def __init__(self, processing_dir="processed_data", graph_path="graph_rag/clinical_trial_graph.graphml"):
        self.llm = ChatGroq(model=MODEL_NAME, api_key=GROQ_API_KEY)
        self.processing_dir = processing_dir
        self.graph_path = graph_path
        
        # Load Data
        self.graph = self._load_graph()
        self.data = self._load_csv_data()
        
        self.workflow = self._build_workflow()

    def _load_graph(self):
        try:
            # Resolve path relative to project root (parent of agents/)
            if not os.path.isabs(self.graph_path):
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                full_path = os.path.join(project_root, self.graph_path)
            else:
                full_path = self.graph_path
                
            if os.path.exists(full_path):
                print(f"Loading graph from {full_path}...")
                return nx.read_graphml(full_path)
            print(f"Graph file not found at {full_path}, using empty graph")
            return nx.DiGraph()
        except Exception as e:
            print(f"Error loading graph: {e}")
            return nx.DiGraph()

    def _load_csv_data(self):
        data = {}
        try:
            # Resolve path relative to project root
            if not os.path.isabs(self.processing_dir):
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                processing_dir = os.path.join(project_root, self.processing_dir)
            else:
                processing_dir = self.processing_dir
                
            missing_pages_path = os.path.join(processing_dir, "missing_pages_processed.csv")
            if os.path.exists(missing_pages_path):
                data["missing_pages"] = pd.read_csv(missing_pages_path)
            
            visit_proj_path = os.path.join(processing_dir, "visit_projection_processed.csv")
            if os.path.exists(visit_proj_path):
                data["visit_projection"] = pd.read_csv(visit_proj_path)
        except Exception as e:
            print(f"Error loading CSV data: {e}")
        return data

    def _get_site_data(self, site_id: str) -> str:
        """Pre-fetch all relevant data for a site"""
        results = []
        
        # Query missing pages
        if "missing_pages" in self.data:
            df = self.data["missing_pages"]
            site_data = df[df['sitenumber'] == site_id]
            if not site_data.empty:
                total_missing = site_data['no___days_page_missing'].sum()
                avg_missing = site_data['no___days_page_missing'].mean()
                results.append(f"Missing Pages: {len(site_data)} records, Total Missing Days: {total_missing:.0f}, Avg: {avg_missing:.2f} days")
            else:
                results.append(f"Missing Pages: No records found for {site_id}")
        
        # Query visit projection
        if "visit_projection" in self.data:
            df = self.data["visit_projection"]
            site_data = df[df['site'] == site_id]
            if not site_data.empty:
                total_outstanding = site_data['__days_outstanding'].sum()
                results.append(f"Visit Projection: {len(site_data)} visits, Total Days Outstanding: {total_outstanding:.0f}")
            else:
                results.append(f"Visit Projection: No records found for {site_id}")
        
        # Query graph neighbors
        if self.graph.number_of_nodes() > 0:
            target_node = None
            possible_keys = [site_id, f"Site:{site_id}", site_id.replace("Site ", "Site:")]
            for k in possible_keys:
                if self.graph.has_node(k):
                    target_node = k
                    break
            
            if target_node:
                neighbors = list(self.graph.neighbors(target_node))[:20]  # Limit to 20
                results.append(f"Graph Connections: {len(neighbors)} linked entities including: {neighbors[:10]}")
            else:
                results.append(f"Graph Connections: Node '{site_id}' not found in graph")
        else:
            results.append("Graph Connections: Graph not loaded")
        
        return "\n".join(results)

    # --- WORKFLOW NODES ---

    async def hawk_node(self, state: DebateState):
        """Invoke Hawk with pre-fetched data"""
        site_data = state.get("site_data", "No data available")
        
        prompt = f"""You are THE HAWK 🦅. You are a paranoid, data-driven Clinical Safety Officer.

GOAL: Prove that {state['site_id']} is RISKY, FAILING, or DANGEROUS.

SITE DATA:
{site_data}

INSTRUCTIONS:
1. Use the data above to find evidence of problems (missing pages, days outstanding).
2. Construct a sharp, aggressive argument (max 100 words) citing specific numbers from the data.
3. Be dramatic but factual - use the actual numbers provided.
"""
        
        input_messages = list(state["messages"])
        if not input_messages:
            input_messages = [HumanMessage(content=f"Investigate {state['site_id']}")]
             
        context_messages = [SystemMessage(content=prompt)] + input_messages
        
        response = await self.llm.ainvoke(context_messages)
        
        return {
            "messages": [AIMessage(content=response.content, name="Hawk")],
            "current_speaker": "Dove",
            "round_count": state.get("round_count", 0) + 1
        }

    async def dove_node(self, state: DebateState):
        """Invoke Dove with pre-fetched data"""
        site_data = state.get("site_data", "No data available")
        
        prompt = f"""You are THE DOVE 🕊️. You are an optimistic, big-picture Clinical Growth Lead.

GOAL: Defend {state['site_id']} against the Hawk's attacks.

SITE DATA:
{site_data}

INSTRUCTIONS:
1. Use the data above to find mitigating factors (connections to studies, context for the numbers).
2. Construct a polite, persuasive counter-argument (max 100 words).
3. Acknowledge issues but provide perspective - put the numbers in context.
"""
        
        input_messages = list(state["messages"])
        context_messages = [SystemMessage(content=prompt)] + input_messages
        
        response = await self.llm.ainvoke(context_messages)
        
        return {
            "messages": [AIMessage(content=response.content, name="Dove")],
            "current_speaker": "Owl",
            "round_count": state.get("round_count", 0)
        }

    def owl_node(self, state: DebateState):
        """The Owl: Judge"""
        if state["round_count"] < 3:
            return {"current_speaker": "Hawk"}
        
        site_data = state.get("site_data", "No data available")
            
        prompt = f"""You are THE OWL 🦉. Chief Medical Judge.

SITE DATA:
{site_data}

Review the debate above and provide:

**Verdict**: [KEEP / WATCH / CLOSE]

**Reasoning**: Summarize the key evidence from both sides (2-3 sentences).

**Recommendation**: One specific action item.
"""
        response = self.llm.invoke([SystemMessage(content=prompt)] + state["messages"])
        return {
            "messages": [AIMessage(content=response.content, name="Owl")],
            "current_speaker": "End",
            "verdict": response.content
        }

    def _build_workflow(self):
        workflow = StateGraph(DebateState)
        
        workflow.add_node("hawk", self.hawk_node)
        workflow.add_node("dove", self.dove_node)
        workflow.add_node("owl", self.owl_node)
        
        workflow.set_entry_point("hawk")
        
        workflow.add_edge("hawk", "dove")
        
        def dove_router(state):
            if state["round_count"] >= 3:
                return "owl"
            return "hawk"
            
        workflow.add_conditional_edges("dove", dove_router)
        workflow.add_edge("owl", END)
        
        return workflow.compile()

    async def run_debate(self, site_id: str):
        """Run the debate and yield messages"""
        # Pre-fetch all data for this site
        site_data = self._get_site_data(site_id)
        print(f"\n📊 Pre-fetched data for {site_id}:\n{site_data}\n")
        
        initial_state = {
            "site_id": site_id,
            "messages": [HumanMessage(content=f"Analyze performance and risk for {site_id}.")],
            "current_speaker": "Hawk",
            "round_count": 0,
            "verdict": "",
            "site_data": site_data
        }
        
        async for event in self.workflow.astream(initial_state):
            for node, updates in event.items():
                if "messages" in updates:
                    latest_msg = updates["messages"][-1]
                    yield {
                        "speaker": latest_msg.name,
                        "content": latest_msg.content,
                        "node": node
                    }
                if "verdict" in updates:
                    yield {
                        "speaker": "System",
                        "content": updates["verdict"],
                        "type": "verdict"
                    }

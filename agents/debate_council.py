import os
from typing import TypedDict, List, Annotated, Dict, Any
import operator
import networkx as nx
import pandas as pd
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
from agents.tools_factory import DebateTools

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

class DebateCouncil:
    def __init__(self, processing_dir="processed_data", graph_path="graph_rag/clinical_trial_graph.graphml"):
        self.llm = ChatGroq(model=MODEL_NAME, api_key=GROQ_API_KEY)
        self.processing_dir = processing_dir
        self.graph_path = graph_path
        
        # Load Data
        self.graph = self._load_graph()
        self.data = self._load_csv_data()
        
        # Initialize Tools
        self.tool_factory = DebateTools(self.graph, self.data)
        self.tools = self.tool_factory.get_tools()
        
        # Build Agents
        self.hawk_agent = self._build_hawk_agent()
        self.dove_agent = self._build_dove_agent()
        
        self.workflow = self._build_workflow()

    def _load_graph(self):
        try:
            if os.path.exists(self.graph_path):
                return nx.read_graphml(self.graph_path)
            return nx.DiGraph()
        except Exception as e:
            print(f"Error loading graph: {e}")
            return nx.DiGraph()

    def _load_csv_data(self):
        data = {}
        try:
            missing_pages_path = os.path.join(self.processing_dir, "missing_pages_processed.csv")
            if os.path.exists(missing_pages_path):
                data["missing_pages"] = pd.read_csv(missing_pages_path)
            
            visit_proj_path = os.path.join(self.processing_dir, "visit_projection_processed.csv")
            if os.path.exists(visit_proj_path):
                data["visit_projection"] = pd.read_csv(visit_proj_path)
        except Exception as e:
            print(f"Error loading CSV data: {e}")
        return data

    def _build_hawk_agent(self):
        # We will inject the prompt at runtime
        return create_react_agent(self.llm, self.tools)

    def _build_dove_agent(self):
        # We will inject the prompt at runtime
        return create_react_agent(self.llm, self.tools)

    # --- WORKFLOW NODES ---

    async def hawk_node(self, state: DebateState):
        """Invoke Hawk Agent with current conversation"""
        prompt = f"""
        You are THE HAWK 🦅. You are a paranoid, data-driven Clinical Safety Officer.
        
        GOAL: Prove that {state['site_id']} is RISKY, FAILING, or DANGEROUS.
        
        INSTRUCTIONS:
        1. Use your tools (`query_site_data`, `query_graph_neighbors`) to gather concrete evidence (missing pages, days outstanding).
        2. Construct a sharp, aggressive argument (max 75 words) citing these specific numbers.
        3. Do not make up data. If you don't have it, fetch it.
        """
        
        # Inject context and system prompt
        input_messages = list(state["messages"])
        if not input_messages:
             input_messages = [HumanMessage(content=f"Investigate {state['site_id']}")]
             
        # Prepend System Prompt
        context_messages = [SystemMessage(content=prompt)] + input_messages
        
        result = await self.hawk_agent.ainvoke({"messages": context_messages})
        
        # Find the last message that is from AI and has content
        last_message_content = "I have no further arguments."
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage) and msg.content and str(msg.content).strip():
                last_message_content = msg.content
                break
        
        return {
            "messages": [AIMessage(content=last_message_content, name="Hawk")],
            "current_speaker": "Dove",
            "round_count": state.get("round_count", 0) + 1
        }

    async def dove_node(self, state: DebateState):
        """Invoke Dove Agent"""
        prompt = f"""
        You are THE DOVE 🕊️. You are an optimistic, big-picture Clinical Growth Lead.
        
        GOAL: Defend {state['site_id']} against the Hawk's attacks.
        
        INSTRUCTIONS:
        1. Use your tools to find mitigating factors (e.g. connections to major studies, huge patient volume vs small errors).
        2. Construct a polite, persuasive defense (max 75 words).
        3. Use data to support your optimism.
        """
        
        input_messages = list(state["messages"])
        context_messages = [SystemMessage(content=prompt)] + input_messages
        
        result = await self.dove_agent.ainvoke({"messages": context_messages})
        
        last_message_content = "I rest my case."
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage) and msg.content and str(msg.content).strip():
                last_message_content = msg.content
                break
        
        return {
            "messages": [AIMessage(content=last_message_content, name="Dove")],
            "current_speaker": "Owl",
            "round_count": state.get("round_count", 0)
        }

    def owl_node(self, state: DebateState):
        """The Owl: Judge"""
        if state["round_count"] < 3:
            return {"current_speaker": "Hawk"}
            
        prompt = f"""
        You are THE OWL 🦉. Chief Medical Judge.
        Review the debate:
        {state['messages']}
        
        Verdict: [Keep/Watch/Close]
        Reasoning: Summarize the evidence found (or lack thereof).
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
        initial_state = {
            "site_id": site_id,
            "messages": [HumanMessage(content=f"Analyze performance and risk for {site_id}. Use your tools to find data!")],
            "current_speaker": "Hawk",
            "round_count": 0,
            "verdict": ""
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

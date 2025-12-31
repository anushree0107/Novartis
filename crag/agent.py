import os
from typing import Optional, List, Dict, Any
import networkx as nx
from dotenv import load_dotenv

from .config import AgentConfig, get_default_config, CRAGConfig
from .tools import create_graph_tools, create_code_executor_tool, ToolRegistry
from .graph_builder import ClinicalTrialGraphBuilder
from .prompts import CRAG_AGENT_PROMPT
from .engine import CRAGEngine

load_dotenv()


class CRAGAgent:
    def __init__(self, config: AgentConfig = None):
        self.config = config or get_default_config()
        self.graph: Optional[nx.DiGraph] = None
        self.tools = ToolRegistry()
        self._agent = None
        self._llm = None
    
    def load_graph(self, path: str = None) -> None:
        path = path or self.config.graph.graph_path
        if os.path.exists(path):
            self.graph = nx.read_graphml(path)
            print(f"✓ Graph: {self.graph.number_of_nodes():,} nodes, {self.graph.number_of_edges():,} edges")
            self._register_tools()
        else:
            raise FileNotFoundError(f"Graph not found: {path}")
    
    def build_graph(self, save: bool = True) -> None:
        print("Building graph...")
        builder = ClinicalTrialGraphBuilder(self.config.graph.data_dir)
        self.graph = builder.build_graph()
        if save:
            builder.save_graph(os.path.basename(self.config.graph.graph_path))
        self._register_tools()
    
    def load_or_build_graph(self) -> None:
        if os.path.exists(self.config.graph.graph_path):
            self.load_graph()
        elif self.config.graph.auto_build:
            self.build_graph()
        else:
            raise FileNotFoundError(f"Graph not found: {self.config.graph.graph_path}")
    
    def _register_tools(self) -> None:
        if not self.graph:
            return
        
        # Initialize LLM for HopRAG if enabled
        hop_engine = None
        if self.config.crag.enabled:
            self._init_llm()
            hop_engine = CRAGEngine(
                graph=self.graph, 
                llm=self._llm,
                config=self.config.crag
            )

        for tool in create_graph_tools(self.graph, hop_engine=hop_engine):
            self.tools.register(tool)
        self.tools.register(create_code_executor_tool(self.config.graph.data_dir))
        print(f"✓ {len(self.tools.list_tools())} tools registered")
    
    def list_tools(self) -> List[str]:
        return self.tools.list_tools()
    
    def _init_llm(self):
        if self._llm:
            return
        if self.config.llm.provider == "groq":
            from langchain_groq import ChatGroq
            self._llm = ChatGroq(
                model=self.config.llm.model_name,
                temperature=self.config.llm.temperature,
                groq_api_key=self.config.llm.api_key,
            )
        elif self.config.llm.provider == "google":
            from langchain_google_genai import ChatGoogleGenerativeAI
            self._llm = ChatGoogleGenerativeAI(
                model=self.config.llm.model_name,
                temperature=self.config.llm.temperature,
                google_api_key=self.config.llm.api_key,
            )
        elif self.config.llm.provider == "openai":
            from langchain_openai import ChatOpenAI
            self._llm = ChatOpenAI(
                model=self.config.llm.model_name,
                temperature=self.config.llm.temperature,
                api_key=self.config.llm.api_key,
            )
    
    def _get_hop_engine(self):
        """Get or create HopRAG engine."""
        if not hasattr(self, '_hop_engine') or self._hop_engine is None:
            self._init_llm()
            self._hop_engine = CRAGEngine(
                graph=self.graph,
                llm=self._llm,
                config=self.config.crag
            )
        return self._hop_engine
    
    def query(self, question: str) -> Dict[str, Any]:
        """Query the graph using HopRAG + direct LLM synthesis (no ReAct overhead)."""
        self._init_llm()
        
        try:
            # 1. Run HopRAG to get relevant graph context
            hop_engine = self._get_hop_engine()
            hop_results = hop_engine.retrieve_reason_prune(question, top_k=self.config.crag.top_k)
            context = hop_engine.format_results_for_context(hop_results)
            
            # 2. Single LLM call to synthesize answer
            from langchain_core.messages import SystemMessage, HumanMessage
            
            synthesis_prompt = f"""You are a clinical trial data analyst. Answer the question using ONLY the provided graph context.

GRAPH CONTEXT:
{context}

QUESTION: {question}

Provide a clear, concise answer with specific data from the context. If the context doesn't contain relevant information, say so."""

            response = self._llm.invoke([
                SystemMessage(content=CRAG_AGENT_PROMPT),
                HumanMessage(content=synthesis_prompt)
            ])
            
            return {"output": response.content, "context": context, "hop_results": len(hop_results)}
        except Exception as e:
            return {"output": f"Error: {e}", "error": True}
    
    def run_tool(self, name: str, **kwargs) -> str:
        tool = self.tools.get(name)
        return tool.run(**kwargs) if tool else f"Tool '{name}' not found"


def create_agent(api_key: str = None, auto_load: bool = True) -> CRAGAgent:
    try:
        from .config import AgentConfig, LLMConfig, GraphConfig
    except ImportError:
        from core import AgentConfig, LLMConfig, GraphConfig
    config = AgentConfig(llm=LLMConfig(api_key=api_key), graph=GraphConfig(auto_build=True))
    agent = CRAGAgent(config)
    if auto_load:
        agent.load_or_build_graph()
    return agent


if __name__ == "__main__":
    agent = create_agent()
    print(f"\nTools: {agent.list_tools()}")
    result = agent.query("Is the current data snapshot clean enough for interim analysis or submission?")
    output = result['output']
    if isinstance(output, list):
        text = "\n".join(block.get('text', '') for block in output if block.get('type') == 'text')
        print(f"\n{text}")
    else:
        print(f"\n{output}")

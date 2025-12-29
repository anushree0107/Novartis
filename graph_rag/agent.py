import os
from typing import Optional, List, Dict, Any
import networkx as nx
from dotenv import load_dotenv

# Handle both direct execution and package import
try:
    from .core import AgentConfig, get_default_config, BaseTool, ToolRegistry, CLINICAL_TRIAL_AGENT_PROMPT
    from .tools import create_graph_tools, create_code_executor_tool
    from .graph_builder import ClinicalTrialGraphBuilder
except ImportError:
    from core import AgentConfig, get_default_config, BaseTool, ToolRegistry, CLINICAL_TRIAL_AGENT_PROMPT
    from tools import create_graph_tools, create_code_executor_tool
    from graph_builder import ClinicalTrialGraphBuilder

load_dotenv()


class ClinicalTrialAgent:
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
        for tool in create_graph_tools(self.graph):
            self.tools.register(tool)
        self.tools.register(create_code_executor_tool(self.config.graph.data_dir))
        print(f"✓ {len(self.tools.list_tools())} tools registered")
    
    def list_tools(self) -> List[str]:
        return self.tools.list_tools()
    
    def _init_llm(self):
        if self._llm:
            return
        if self.config.llm.provider == "google":
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
    
    def _build_agent(self):
        if self._agent:
            return
        self._init_llm()
        from langgraph.prebuilt import create_react_agent
        from langchain_core.messages import SystemMessage
        tools = self.tools.to_langchain_tools()
        self._agent = create_react_agent(self._llm, tools, prompt=SystemMessage(content=CLINICAL_TRIAL_AGENT_PROMPT))
    
    def query(self, question: str) -> Dict[str, Any]:
        self._build_agent()
        try:
            from langchain_core.messages import HumanMessage
            result = self._agent.invoke({"messages": [HumanMessage(content=question)]})
            msgs = result.get("messages", [])
            return {"output": msgs[-1].content if msgs else "No response", "messages": msgs}
        except Exception as e:
            return {"output": f"Error: {e}", "error": True}
    
    def run_tool(self, name: str, **kwargs) -> str:
        tool = self.tools.get(name)
        return tool.run(**kwargs) if tool else f"Tool '{name}' not found"


def create_agent(api_key: str = None, auto_load: bool = True) -> ClinicalTrialAgent:
    try:
        from .core import AgentConfig, LLMConfig, GraphConfig
    except ImportError:
        from core import AgentConfig, LLMConfig, GraphConfig
    config = AgentConfig(llm=LLMConfig(api_key=api_key), graph=GraphConfig(auto_build=True))
    agent = ClinicalTrialAgent(config)
    if auto_load:
        agent.load_or_build_graph()
    return agent


if __name__ == "__main__":
    agent = create_agent()
    print(f"\nTools: {agent.list_tools()}")
    result = agent.query("Where are the most open issues in lab reconciliation or coding?")
    output = result['output']
    if isinstance(output, list):
        text = "\n".join(block.get('text', '') for block in output if block.get('type') == 'text')
        print(f"\n{text}")
    else:
        print(f"\n{output}")

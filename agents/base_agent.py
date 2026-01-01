"""
Base Agent class for the Text-to-SQL pipeline
Following NEXUS architecture pattern with Tools
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
import time

from utils.llm_client import GroqLLMClient
from utils.token_utils import token_manager
from config.settings import MODELS, AGENT_CONFIG


@dataclass
class ToolResult:
    """Result from a tool execution"""
    success: bool
    data: Any
    tool_name: str
    tokens_used: int = 0
    error: str = None


@dataclass
class AgentResult:
    """Standard result from an agent"""
    success: bool
    data: Any
    reasoning: str = ""
    tokens_used: int = 0
    execution_time: float = 0.0
    error: str = None
    tool_calls: List[ToolResult] = field(default_factory=list)


class BaseTool(ABC):
    """Base class for agent tools"""
    
    def __init__(self, name: str, description: str, llm_client: GroqLLMClient = None):
        self.name = name
        self.description = description
        self.llm = llm_client
    
    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool"""
        pass
    
    def call_llm(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 0.1,
        max_tokens: int = 1024,
        json_mode: bool = False
    ) -> Dict[str, Any]:
        """Call LLM for tool operations"""
        if not self.llm:
            raise ValueError("LLM client not set for this tool")
        
        return self.llm.chat_completion(
            messages=messages,
            model=model or MODELS.get('evaluator', 'llama-3.1-8b-instant'),
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=json_mode
        )


class BaseAgent(ABC):
    """Base class for all agents in the pipeline"""
    
    def __init__(
        self,
        llm_client: GroqLLMClient,
        model: str = None,
        temperature: float = None,
        max_retries: int = None
    ):
        self.llm = llm_client
        self.model = model or MODELS['sql_generator']
        self.temperature = temperature if temperature is not None else AGENT_CONFIG['temperature']
        self.max_retries = max_retries or AGENT_CONFIG['max_retries']
        self.name = self.__class__.__name__
        self.tools: Dict[str, BaseTool] = {}
        self._register_tools()
    
    def _register_tools(self):
        """Override to register tools for this agent"""
        pass
    
    def add_tool(self, tool: BaseTool):
        """Add a tool to this agent"""
        self.tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name"""
        return self.tools.get(name)
    
    def call_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """Call a tool by name"""
        tool = self.get_tool(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                data=None,
                tool_name=tool_name,
                error=f"Tool '{tool_name}' not found"
            )
        return tool.execute(**kwargs)
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent"""
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> AgentResult:
        """Execute the agent's main task"""
        pass
    
    def build_messages(
        self,
        user_content: str,
        system_content: str = None
    ) -> List[Dict[str, str]]:
        """Build message list for LLM"""
        messages = []
        
        if system_content or self.get_system_prompt():
            messages.append({
                "role": "system",
                "content": system_content or self.get_system_prompt()
            })
        
        messages.append({
            "role": "user",
            "content": user_content
        })
        
        return messages
    
    def call_llm(
        self,
        messages: List[Dict[str, str]],
        json_mode: bool = False,
        max_tokens: int = 2048
    ) -> Dict[str, Any]:
        """Call LLM with retry logic"""
        last_error = None
        
        for attempt in range(self.max_retries):
            result = self.llm.chat_completion(
                messages=messages,
                model=self.model,
                temperature=self.temperature,
                max_tokens=max_tokens,
                json_mode=json_mode
            )
            
            if result.get('content'):
                return result
            
            last_error = result.get('error', 'Unknown error')
            time.sleep(1 * (attempt + 1))  # Exponential backoff
        
        return {'content': None, 'error': last_error, 'usage': {'input_tokens': 0, 'output_tokens': 0}}
    
    def log(self, message: str, level: str = "info"):
        """Log agent activity"""
        prefix = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌"}.get(level, "")
        print(f"{prefix} [{self.name}] {message}")

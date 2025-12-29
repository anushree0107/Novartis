"""Base classes for agent tools."""

from abc import ABC, abstractmethod
from typing import Type, Dict, List, Optional
from pydantic import BaseModel


class BaseTool(ABC):
    name: str = "base_tool"
    description: str = ""
    
    def __init__(self, **kwargs):
        pass
    
    @property
    @abstractmethod
    def args_schema(self) -> Type[BaseModel]:
        pass
    
    @abstractmethod
    def _run(self, **kwargs) -> str:
        pass
    
    def run(self, **kwargs) -> str:
        try:
            return self._run(**kwargs)
        except Exception as e:
            return f"Error in {self.name}: {e}"
    
    def to_langchain_tool(self):
        from langchain_core.tools import StructuredTool
        return StructuredTool(name=self.name, description=self.description, func=self.run, args_schema=self.args_schema)


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
    
    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)
    
    def list_tools(self) -> List[str]:
        return list(self._tools.keys())
    
    def to_langchain_tools(self) -> list:
        return [t.to_langchain_tool() for t in self._tools.values()]

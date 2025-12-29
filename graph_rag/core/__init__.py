"""Core package."""

try:
    from config import AgentConfig, LLMConfig, GraphConfig, HopRAGConfig, get_default_config
    from base_tool import BaseTool, ToolRegistry
    from prompts import CLINICAL_TRIAL_AGENT_PROMPT
except ImportError:
    from .config import AgentConfig, LLMConfig, GraphConfig, HopRAGConfig, get_default_config
    from .base_tool import BaseTool, ToolRegistry
    from .prompts import CLINICAL_TRIAL_AGENT_PROMPT

__all__ = ["AgentConfig", "LLMConfig", "GraphConfig", "HopRAGConfig", "get_default_config", "BaseTool", "ToolRegistry", "CLINICAL_TRIAL_AGENT_PROMPT"]

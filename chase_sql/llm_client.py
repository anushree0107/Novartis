"""
LLM Client for CHASE-SQL.

Provides unified interface for different LLM providers (OpenAI, Google, Anthropic, Ollama).
"""
import json
import re
import logging
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod

from .config import LLMConfig, LLMProvider, default_config

logger = logging.getLogger(__name__)


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
    
    @abstractmethod
    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate completion for the given prompt"""
        pass
    
    def extract_sql(self, response: str) -> Optional[str]:
        """Extract SQL query from LLM response"""
        # Try to find SQL in code blocks
        sql_pattern = r"```sql\s*([\s\S]*?)\s*```"
        matches = re.findall(sql_pattern, response, re.IGNORECASE)
        if matches:
            return matches[-1].strip()  # Return last SQL block
        
        # Try generic code blocks
        code_pattern = r"```\s*(SELECT[\s\S]*?)\s*```"
        matches = re.findall(code_pattern, response, re.IGNORECASE)
        if matches:
            return matches[-1].strip()
        
        # Try to find raw SELECT statement
        select_pattern = r"(SELECT\s+[\s\S]+?(?:;|$))"
        matches = re.findall(select_pattern, response, re.IGNORECASE)
        if matches:
            return matches[-1].strip().rstrip(';') + ';'
        
        return None
    
    def extract_json(self, response: str) -> Optional[Dict[str, Any]]:
        """Extract JSON object from LLM response"""
        # Try to find JSON in code blocks
        json_pattern = r"```json\s*([\s\S]*?)\s*```"
        matches = re.findall(json_pattern, response, re.IGNORECASE)
        if matches:
            try:
                return json.loads(matches[-1])
            except json.JSONDecodeError:
                pass
        
        # Try to find raw JSON
        try:
            # Find first { and last }
            start = response.find('{')
            end = response.rfind('}')
            if start != -1 and end != -1:
                return json.loads(response[start:end+1])
        except json.JSONDecodeError:
            pass
        
        return None


class OpenAIClient(BaseLLMClient):
    """OpenAI GPT client"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=config.api_key,
                base_url=config.base_url
            )
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
    
    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        return response.choices[0].message.content


class GoogleClient(BaseLLMClient):
    """Google Gemini client using new google.genai library"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        try:
            import os
            from google import genai
            # Get API key from config or environment
            api_key = config.api_key or os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not found. Set it via environment variable or config.")
            self.client = genai.Client(api_key=api_key)
            self.model_name = config.model
        except ImportError:
            raise ImportError("google-genai package not installed. Run: pip install google-genai")
    
    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=full_prompt
        )
        return response.text


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude client"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=config.api_key)
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
    
    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        response = self.client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            system=system_prompt or "You are a helpful assistant.",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text


class OllamaClient(BaseLLMClient):
    """Ollama local LLM client"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.base_url = config.base_url or "http://localhost:11434"
    
    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        import requests
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.config.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": self.config.temperature,
                }
            }
        )
        response.raise_for_status()
        return response.json()["response"]


class GroqClient(BaseLLMClient):
    """Groq client for fast LLM inference"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        try:
            import os
            from groq import Groq
            # Get API key from config or environment
            api_key = config.api_key or os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not found. Set it via environment variable or config.")
            self.client = Groq(api_key=api_key)
        except ImportError:
            raise ImportError("groq package not installed. Run: pip install groq")
    
    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        return response.choices[0].message.content


def create_llm_client(config: Optional[LLMConfig] = None) -> BaseLLMClient:
    """Factory function to create the appropriate LLM client"""
    config = config or default_config.llm
    
    client_map = {
        LLMProvider.OPENAI: OpenAIClient,
        LLMProvider.GOOGLE: GoogleClient,
        LLMProvider.ANTHROPIC: AnthropicClient,
        LLMProvider.GROQ: GroqClient,
        LLMProvider.OLLAMA: OllamaClient,
    }
    
    client_class = client_map.get(config.provider)
    if not client_class:
        raise ValueError(f"Unsupported LLM provider: {config.provider}")
    
    return client_class(config)


# Singleton client
_default_client: Optional[BaseLLMClient] = None


def get_llm_client() -> BaseLLMClient:
    """Get or create default LLM client"""
    global _default_client
    if _default_client is None:
        _default_client = create_llm_client()
    return _default_client

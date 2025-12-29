"""
Groq LLM Client for the Text-to-SQL agents
"""
import os
from typing import List, Dict, Any, Optional
from groq import Groq
import json
import re

from config.settings import GROQ_API_KEY, MODELS, AGENT_CONFIG
from utils.token_utils import token_manager


class GroqLLMClient:
    """Client for interacting with Groq API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or GROQ_API_KEY
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not set. Please set it in .env file")
        
        self.client = Groq(api_key=self.api_key)
        self.usage_stats = {
            'total_input_tokens': 0,
            'total_output_tokens': 0,
            'total_requests': 0
        }
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = None,
        max_tokens: int = 2048,
        json_mode: bool = False,
        stop: List[str] = None
    ) -> Dict[str, Any]:
        """
        Send a chat completion request to Groq
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (defaults to sql_generator model)
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            json_mode: Whether to request JSON output
            stop: Stop sequences
            
        Returns:
            Dict with 'content', 'usage', and 'model' keys
        """
        model = model or MODELS['sql_generator']
        temperature = temperature if temperature is not None else AGENT_CONFIG['temperature']
        
        try:
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            
            if stop:
                kwargs["stop"] = stop
            
            response = self.client.chat.completions.create(**kwargs)
            
            # Update usage stats
            if response.usage:
                self.usage_stats['total_input_tokens'] += response.usage.prompt_tokens
                self.usage_stats['total_output_tokens'] += response.usage.completion_tokens
                self.usage_stats['total_requests'] += 1
            
            return {
                'content': response.choices[0].message.content,
                'usage': {
                    'input_tokens': response.usage.prompt_tokens if response.usage else 0,
                    'output_tokens': response.usage.completion_tokens if response.usage else 0
                },
                'model': model,
                'finish_reason': response.choices[0].finish_reason
            }
            
        except Exception as e:
            return {
                'content': None,
                'error': str(e),
                'usage': {'input_tokens': 0, 'output_tokens': 0},
                'model': model
            }
    
    def extract_json(self, text: str) -> Optional[Dict]:
        """Extract JSON from text response"""
        if not text:
            return None
            
        # Try direct parse first
        try:
            return json.loads(text)
        except:
            pass
        
        # Try to find JSON in markdown code blocks
        json_patterns = [
            r'```json\s*([\s\S]*?)\s*```',
            r'```\s*([\s\S]*?)\s*```',
            r'\{[\s\S]*\}'
        ]
        
        for pattern in json_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    json_str = match.group(1) if '```' in pattern else match.group(0)
                    return json.loads(json_str)
                except:
                    continue
        
        return None
    
    def extract_sql(self, text: str) -> Optional[str]:
        """Extract SQL from text response"""
        if not text:
            return None
        
        # Try to find SQL in code blocks
        sql_patterns = [
            r'```sql\s*([\s\S]*?)\s*```',
            r'```\s*(SELECT[\s\S]*?)\s*```',
            r'(SELECT\s+[\s\S]+?;)',
            r'(SELECT\s+[\s\S]+?)(?:\n\n|$)'
        ]
        
        for pattern in sql_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                sql = match.group(1).strip()
                # Clean up
                sql = sql.rstrip(';') + ';'
                return sql
        
        # If text starts with SELECT, assume it's SQL
        if text.strip().upper().startswith('SELECT'):
            return text.strip().rstrip(';') + ';'
        
        return None
    
    def get_usage_stats(self) -> Dict[str, int]:
        """Get cumulative usage statistics"""
        return self.usage_stats.copy()
    
    def reset_usage_stats(self):
        """Reset usage statistics"""
        self.usage_stats = {
            'total_input_tokens': 0,
            'total_output_tokens': 0,
            'total_requests': 0
        }


# Singleton instance
llm_client = GroqLLMClient() if GROQ_API_KEY else None

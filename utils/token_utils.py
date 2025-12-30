"""
Token utilities for optimization in Text-to-SQL pipeline
"""
import tiktoken
from typing import List, Dict, Any


class TokenManager:
    """Manages token counting and optimization"""
    
    def __init__(self, encoding_name: str = "cl100k_base"):
        self.encoding = tiktoken.get_encoding(encoding_name)
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in a string"""
        if not text:
            return 0
        return len(self.encoding.encode(text))
    
    def count_messages_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Count tokens in a list of messages"""
        total = 0
        for msg in messages:
            total += self.count_tokens(msg.get('content', ''))
            total += 4  # Overhead for message structure
        return total
    
    def truncate_to_token_limit(self, text: str, max_tokens: int) -> str:
        """Truncate text to fit within token limit"""
        tokens = self.encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text
        truncated_tokens = tokens[:max_tokens]
        return self.encoding.decode(truncated_tokens)
    
    def split_into_chunks(self, text: str, chunk_size: int) -> List[str]:
        """Split text into chunks of specified token size"""
        tokens = self.encoding.encode(text)
        chunks = []
        
        for i in range(0, len(tokens), chunk_size):
            chunk_tokens = tokens[i:i + chunk_size]
            chunks.append(self.encoding.decode(chunk_tokens))
        
        return chunks
    
    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str = "llama-3.3-70b-versatile") -> float:
        """Estimate cost for Groq API (currently free tier)"""
        # Groq has generous free tier - this is for tracking
        return 0.0  # Groq free tier


# Singleton instance
token_manager = TokenManager()

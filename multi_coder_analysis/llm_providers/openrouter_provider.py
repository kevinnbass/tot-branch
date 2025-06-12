import os
from typing import Optional
import openai
from .base import LLMProvider

_BASE_URL = "https://openrouter.ai/api/v1"

class OpenRouterProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, base_url: str = _BASE_URL):
        key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not key:
            raise ValueError("OPENROUTER_API_KEY not set")
        
        # Initialize OpenAI client with OpenRouter configuration
        self._client = openai.OpenAI(
            api_key=key,
            base_url=base_url
        )

    def generate(self, system_prompt: str, user_prompt: str, model: str, temperature: float = 0.0) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        resp = self._client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            top_p=0.1,
        )
        
        # OpenRouter doesn't provide thinking traces
        self._last_thoughts = ""
        self._last_usage = {'prompt_tokens': 0, 'response_tokens': 0, 'thought_tokens': 0, 'total_tokens': 0}
        
        return resp.choices[0].message.content.strip()
    
    def get_last_thoughts(self) -> str:
        """Retrieve thinking traces from the last generate() call (empty for OpenRouter)."""
        return getattr(self, '_last_thoughts', '') 

    def get_last_usage(self) -> dict:
        return getattr(self, '_last_usage', {'prompt_tokens': 0, 'response_tokens': 0, 'thought_tokens': 0, 'total_tokens': 0}) 
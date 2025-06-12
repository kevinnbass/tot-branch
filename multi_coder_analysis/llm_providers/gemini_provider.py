import os
import logging
from typing import Optional
from google import genai
from google.genai import types
from .base import LLMProvider

class GeminiProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None):
        key = api_key or os.getenv("GOOGLE_API_KEY")
        if not key:
            raise ValueError("GOOGLE_API_KEY not set")
        # Initialize client directly with the API key (newer SDK style)
        self._client = genai.Client(api_key=key)

    def generate(self, system_prompt: str, user_prompt: str, model: str, temperature: float = 0.0) -> str:
        cfg = {"temperature": temperature}
        # Enforce deterministic nucleus + top-k
        cfg["top_p"] = 0.1
        cfg["top_k"] = 1
        cfg["system_instruction"] = system_prompt

        if "2.5" in model:
            cfg["thinking_config"] = types.ThinkingConfig(include_thoughts=True)
        
        resp = self._client.models.generate_content(
            model=model,
            contents=user_prompt,
            config=types.GenerateContentConfig(**cfg)
        )
        
        # Capture usage metadata if available
        usage_meta = getattr(resp, 'usage_metadata', None)
        if usage_meta:
            prompt_toks = int(getattr(usage_meta, 'prompt_token_count', 0))
            # SDK renamed field from response_token_count → candidates_token_count
            resp_toks = int(
                getattr(usage_meta, 'response_token_count', getattr(usage_meta, 'candidates_token_count', 0))
            )
            thought_toks = int(getattr(usage_meta, 'thoughts_token_count', 0))
            total_toks = int(getattr(usage_meta, 'total_token_count', 0))
            self._last_usage = {
                'prompt_tokens': prompt_toks,
                'response_tokens': resp_toks,
                'thought_tokens': thought_toks,
                'total_tokens': total_toks or (prompt_toks + resp_toks + thought_toks)
            }
        else:
            self._last_usage = {'prompt_tokens': 0, 'response_tokens': 0, 'thought_tokens': 0, 'total_tokens': 0}
        
        # Stitch together parts (Gemini returns list‑of‑parts)
        thoughts = ""
        content = ""
        
        for part in resp.candidates[0].content.parts:
            if not part.text:
                continue
            if hasattr(part, 'thought') and part.thought:
                thoughts += part.text
            else:
                content += part.text
        
        # Store thoughts for potential retrieval
        self._last_thoughts = thoughts
        
        return content.strip()
    
    def get_last_thoughts(self) -> str:
        """Retrieve thinking traces from the last generate() call."""
        return getattr(self, '_last_thoughts', '')

    def get_last_usage(self) -> dict:
        return getattr(self, '_last_usage', {'prompt_tokens': 0, 'response_tokens': 0, 'total_tokens': 0}) 
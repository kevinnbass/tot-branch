# Optional dependency: OpenAI SDK (used for OpenRouter compatibility). To avoid
# import-time failures in environments where the package is unavailable (e.g.,
# CI test runners), we import it lazily within the constructor.
import os
from typing import Optional, TYPE_CHECKING
from .base import LLMProvider

if TYPE_CHECKING:
    import openai as _openai  # pragma: no cover

openai = None  # will attempt lazy import

_BASE_URL = "https://openrouter.ai/api/v1"

class OpenRouterProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, base_url: str = _BASE_URL):
        global openai  # noqa: PLW0603

        if openai is None:
            try:
                import openai as _openai  # type: ignore
                openai = _openai
            except ImportError as e:
                raise ImportError(
                    "The openai package is required for OpenRouterProvider."
                    "\n   ➜  pip install openai"
                ) from e

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
        
        self._acc_usage = {
            'prompt_tokens': 0,
            'response_tokens': 0,
            'thought_tokens': 0,
            'total_tokens': 0,
            'cached_tokens': 0,
        }
        
        return resp.choices[0].message.content.strip()
    
    def get_last_thoughts(self) -> str:
        """Retrieve thinking traces from the last generate() call (empty for OpenRouter)."""
        return getattr(self, '_last_thoughts', '') 

    def get_last_usage(self) -> dict:
        return getattr(self, '_last_usage', {'prompt_tokens': 0, 'response_tokens': 0, 'thought_tokens': 0, 'total_tokens': 0}) 

    def reset_usage(self) -> None:  # noqa: D401
        self._acc_usage = {k: 0 for k in self._acc_usage}

    def get_acc_usage(self) -> dict:  # noqa: D401
        return dict(self._acc_usage) 
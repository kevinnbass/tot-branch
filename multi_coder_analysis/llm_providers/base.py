from abc import ABC, abstractmethod

class LLMProvider(ABC):
    """Uniform interface for all LLM back‑ends."""

    @abstractmethod
    def generate(self, prompt: str, model: str, temperature: float = 0.0) -> str:
        """Return the raw assistant message text."""
        ...
    
    @abstractmethod
    def get_last_thoughts(self) -> str:
        """Retrieve thinking traces from the last generate() call."""
        ...

    @abstractmethod
    def get_last_usage(self) -> dict:
        """Return token usage metadata from last call (keys: prompt_tokens, response_tokens, total_tokens)."""
        ... 
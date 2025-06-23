from __future__ import annotations

from typing import Protocol, runtime_checkable, Callable, Dict
import threading

__all__ = ["ProviderProtocol"]


@runtime_checkable
class ProviderProtocol(Protocol):
    """Protocol defining the interface for LLM providers.
    
    This uses PEP 544 structural subtyping, allowing any class with the
    required methods to be used as a provider without explicit inheritance.
    """
    
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
        temperature: float = 0.0,
        *,
        top_k: int | None = None,
        top_p: float | None = None,
    ) -> str:
        """Generate a response from the LLM.
        
        The **public** Tree-of-Thought API passes two separate prompt strings –
        a high-level *system/developer* instruction and the actual *user*
        content.  Providers must therefore accept both arguments explicitly so
        the call-site ordering is unambiguous.
        
        Args:
            system_prompt: Instruction that sets assistant behaviour.
            user_prompt: The user-visible prompt or question.
            model: Model identifier (provider-specific).
            temperature: Sampling temperature (``0.0`` = deterministic).
            
        Returns:
            The generated response text.
        """
        ...
    
    def get_last_thoughts(self) -> str:
        """Get thinking/reasoning traces from the last generate() call.
        
        Returns:
            Thinking traces as a string, or empty string if not available.
        """
        ...
    
    def get_last_usage(self) -> dict:
        """Get token usage statistics from the last generate() call.
        
        Returns:
            Dictionary with keys like 'prompt_tokens', 'response_tokens', 
            'total_tokens', etc. Empty dict if not available.
        """
        ... 

# ---------------------------------------------------------------------------
# Global usage accumulator – lightweight telemetry across providers and threads
# ---------------------------------------------------------------------------

_USAGE_ACCUMULATOR: Dict[str, float] = {
    "prompt_tokens": 0,
    "response_tokens": 0,
    "thought_tokens": 0,
    "total_tokens": 0,
    "llm_calls": 0,
    "regex_yes": 0,
    "regex_hit_shadow": 0,
    "total_hops": 0,
    # running USD cost across the whole process
    "cost_usd": 0.0,
}

_USAGE_LOCK = threading.Lock()

def get_usage_accumulator() -> Dict[str, int]:  # noqa: D401
    """Return the live, process-wide token usage counter (mutable)."""

    with _USAGE_LOCK:
        return dict(_USAGE_ACCUMULATOR)


def track_usage(fn: Callable):  # type: ignore[type-arg]
    """Decorator: after *fn* executes, merge provider.get_last_usage() into global counter."""

    def _wrap(self, *args, **kwargs):  # type: ignore[no-self-use]
        out = fn(self, *args, **kwargs)
        if hasattr(self, "get_last_usage"):
            usage = self.get_last_usage() or {}
            def _safe_int(val):
                try:
                    return int(val or 0)
                except Exception:
                    return 0

            with _USAGE_LOCK:
                _USAGE_ACCUMULATOR["prompt_tokens"] += _safe_int(usage.get("prompt_tokens"))
                _USAGE_ACCUMULATOR["response_tokens"] += _safe_int(usage.get("response_tokens"))
                _USAGE_ACCUMULATOR["thought_tokens"] += _safe_int(usage.get("thought_tokens"))
                _USAGE_ACCUMULATOR["total_tokens"] += _safe_int(usage.get("total_tokens"))
                _USAGE_ACCUMULATOR["llm_calls"] += 1

                # ---------- per-call cost ----------
                try:
                    from multi_coder_analysis.pricing import estimate_cost

                    provider_name = self.__class__.__name__.replace("Provider", "").lower()
                    # model positional arg index 2 in generate(system, user, model, ...)
                    model_name = kwargs.get("model") if "model" in kwargs else (
                        args[2] if len(args) > 2 else ""
                    )

                    cost_info = estimate_cost(
                        provider=provider_name,
                        model=model_name,
                        prompt_tokens=_safe_int(usage.get("prompt_tokens")),
                        response_tokens=_safe_int(usage.get("response_tokens")),
                        cached_tokens=_safe_int(usage.get("cached_tokens", 0)),
                    )

                    _USAGE_ACCUMULATOR["cost_usd"] += cost_info["cost_total_usd"]

                    # store cost back on usage dict for provider-level inspection
                    usage["cost_usd"] = cost_info["cost_total_usd"]
                except Exception:  # pragma: no cover – cost calc must never crash run
                    pass
        return out

    return _wrap 

# ------------------------------------------------------------
# Convenience helper for callers interested only in the dollars
# ------------------------------------------------------------

def get_cost_accumulator() -> float:  # noqa: D401
    """Return the running USD cost for the current Python process."""
    with _USAGE_LOCK:
        return float(_USAGE_ACCUMULATOR.get("cost_usd", 0.0)) 
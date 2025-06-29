"""
Canonical price tables and helpers for cost estimation.

All monetary amounts are stored as **USD per single token** (not per-million)
so callers can multiply directly by token counts.
"""

from __future__ import annotations

from typing import Dict, TypedDict
import os, json

# ---------------------------------------------------------------------------
# Raw Gemini price table  (extend for other providers / models as needed)
# ---------------------------------------------------------------------------

_GEMINI_PRICES: Dict[str, Dict[str, float]] = {
    # GA endpoint – 17 Jun 2025 announcement
    "gemini-2.5-flash": {
        "input":   0.30 / 1_000_000,
        "output":  2.50 / 1_000_000,
        "cached":  0.30 / 1_000_000 * 0.25,   # 75 % discount for cached tokens
    },
    # Preview endpoint – removed mid-July 2025 but some users still hit it
    "gemini-2.5-flash-preview-04-17": {
        "input":   0.15 / 1_000_000,
        "output":  0.60 / 1_000_000,
        "cached":  0.15 / 1_000_000 * 0.25,
    },
}


# OpenRouter price table
_OPENROUTER_PRICES: Dict[str, Dict[str, float]] = {
    "openai/gpt-4o": {
        "input": 2.50 / 1_000_000,
        "output": 10.00 / 1_000_000,
    },
    "openai/gpt-4o-mini": {
        "input": 0.15 / 1_000_000,
        "output": 0.60 / 1_000_000,
    },
    "anthropic/claude-3-5-sonnet": {
        "input": 3.00 / 1_000_000,
        "output": 15.00 / 1_000_000,
    },
    "anthropic/claude-3-haiku": {
        "input": 0.25 / 1_000_000,
        "output": 1.25 / 1_000_000,
    },
    "google/gemini-pro-1.5": {
        "input": 2.50 / 1_000_000,
        "output": 7.50 / 1_000_000,
    },
}

# Allow runtime override via env-var JSON
_override = os.getenv("MCA_PRICE_OVERRIDE_JSON")
if _override:
    try:
        _GEMINI_PRICES.update(json.loads(_override))
    except Exception:  # pragma: no cover – never fail hard on malformed override
        pass

# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

class CostBreakdown(TypedDict):
    input_tokens: int
    output_tokens: int
    cached_tokens: int
    cost_input_usd: float
    cost_cached_usd: float
    cost_output_usd: float
    cost_total_usd: float


def _match_price_row(model: str) -> Dict[str, float]:
    model_lc = model.lower()
    for pattern, row in _GEMINI_PRICES.items():
        if pattern in model_lc:
            return row
    raise KeyError(f"No price entry for model '{model}'.")


def estimate_gemini_cost(*, model: str, prompt_tokens: int, response_tokens: int, cached_tokens: int = 0) -> CostBreakdown:
    """Return a  detailed cost breakdown for a single Gemini call."""
    prices = _match_price_row(model)

    billed_input = max(prompt_tokens - cached_tokens, 0)

    cost_input  = billed_input   * prices["input"]
    cost_cache  = cached_tokens  * prices["cached"]
    cost_output = response_tokens * prices["output"]

    total = cost_input + cost_cache + cost_output

    return {
        "input_tokens":   prompt_tokens,
        "output_tokens":  response_tokens,
        "cached_tokens":  cached_tokens,
        "cost_input_usd":  round(cost_input,  6),
        "cost_cached_usd": round(cost_cache, 6),
        "cost_output_usd": round(cost_output,6),
        "cost_total_usd":  round(total, 6),
    }




def estimate_openrouter_cost(*, model: str, prompt_tokens: int, response_tokens: int, **kwargs) -> CostBreakdown:
    """Return a detailed cost breakdown for an OpenRouter call."""
    model_lc = model.lower()
    
    # Try to find matching price entry
    prices = None
    for pattern, row in _OPENROUTER_PRICES.items():
        if pattern in model_lc or model_lc in pattern:
            prices = row
            break
    
    if not prices:
        # Default pricing for unknown models
        prices = {"input": 1.00 / 1_000_000, "output": 2.00 / 1_000_000}
    
    cost_input = prompt_tokens * prices["input"]
    cost_output = response_tokens * prices["output"]
    total = cost_input + cost_output
    
    return {
        "input_tokens": prompt_tokens,
        "output_tokens": response_tokens,
        "cached_tokens": 0,  # OpenRouter doesn't report cached tokens
        "cost_input_usd": round(cost_input, 6),
        "cost_cached_usd": 0.0,
        "cost_output_usd": round(cost_output, 6),
        "cost_total_usd": round(total, 6),
    }


def estimate_cost(provider: str, **kwargs):
    """Generic dispatcher so callers don't care about provider-specific helper."""
    provider_lc = provider.lower()
    if provider_lc == "gemini":
        return estimate_gemini_cost(**kwargs)
    elif provider_lc == "openrouter":
        return estimate_openrouter_cost(**kwargs)
    else:
        # Default fallback for unknown providers
        return {
            "input_tokens": kwargs.get("prompt_tokens", 0),
            "output_tokens": kwargs.get("response_tokens", 0),
            "cached_tokens": 0,
            "cost_input_usd": 0.0,
            "cost_cached_usd": 0.0,
            "cost_output_usd": 0.0,
            "cost_total_usd": 0.0,
        } 
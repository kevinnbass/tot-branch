"""HTTP-level OpenRouter provider.

Eliminates the hard dependency on the *openai* Python package so the CLI works
out-of-the-box in minimal environments (CI, Docker).  The implementation
conforms to ``ProviderProtocol`` via duck-typing only – no inheritance needed.
"""

from __future__ import annotations

import os
import logging
from typing import Optional

import requests

from .base import ProviderProtocol
from .base import track_usage

_LOGGER = logging.getLogger(__name__)

__all__ = ["OpenRouterProvider"]


class OpenRouterProvider:
    """Lightweight provider that talks to https://openrouter.ai via REST."""

    _ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self._api_key:
            raise ValueError("OPENROUTER_API_KEY not set")

        self._last_usage: dict = {}
        self._last_thoughts: str = ""
        self._acc_usage: dict[str, int] = {
            'prompt_tokens': 0,
            'response_tokens': 0,
            'thought_tokens': 0,
            'cached_tokens': 0,
            'total_tokens': 0,
        }

    # ------------------------------------------------------------------
    # ProviderProtocol interface
    # ------------------------------------------------------------------
    @track_usage
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
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "temperature": temperature,
            **({"top_p": float(top_p)} if top_p is not None else {}),
            **({"top_k": int(top_k)} if top_k is not None else {}),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        resp = requests.post(self._ENDPOINT, json=payload, headers=headers, timeout=30)
        try:
            resp.raise_for_status()
        except Exception as exc:  # pragma: no cover
            _LOGGER.error("OpenRouter request failed: %s", exc)
            raise

        data = resp.json()

        # Save usage metadata if available (OpenAI style)
        self._last_usage = data.get("usage", {}) if isinstance(data, dict) else {}
        # Provide schema-complete defaults
        self._last_usage.setdefault("thought_tokens", 0)

        # ---- accumulate per-instance usage ----
        for k in ('prompt_tokens', 'response_tokens', 'thought_tokens', 'total_tokens'):
            self._acc_usage[k] += int(self._last_usage.get(k, 0))

        choice = data["choices"][0]
        self._last_thoughts = choice.get("thoughts", "")  # rarely provided

        return choice["message"]["content"].strip()

    # ------------------------------------------------------------------
    # Introspection helpers
    # ------------------------------------------------------------------
    def get_last_thoughts(self) -> str:
        return self._last_thoughts

    def get_last_usage(self) -> dict:  # noqa: D401 – simple struct
        # Ensure numeric fields are ints for downstream math
        return {k: int(v) for k, v in self._last_usage.items()} if self._last_usage else {
            "prompt_tokens": 0,
            "response_tokens": 0,
            "total_tokens": 0,
        }

    # ------------------------------------------------------------------
    # Incremental usage helpers (ProviderProtocol)
    # ------------------------------------------------------------------

    def reset_usage(self) -> None:  # noqa: D401
        for k in self._acc_usage:
            self._acc_usage[k] = 0

    def get_acc_usage(self) -> dict:  # noqa: D401
        return dict(self._acc_usage) 
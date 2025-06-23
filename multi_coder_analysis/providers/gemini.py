from __future__ import annotations
import os
# NOTE: Google Gemini SDK is optional in many test environments. We therefore
# *attempt* to import it lazily and only raise a helpful error message at
# instantiation time, not at module import time (which would break unrelated
# unit-tests that merely import the parent package).
import logging
from typing import Optional, TYPE_CHECKING

# Defer heavy / optional dependency import – set sentinels instead.  We rely
# on run-time checks within `__init__` to raise when the SDK is truly needed.
if TYPE_CHECKING:
    # Type-hints only (ignored at run-time when type checkers are disabled)
    from google import genai as _genai  # pragma: no cover
    from google.genai import types as _types  # pragma: no cover

genai = None  # will attempt to import lazily in __init__
types = None
# Import typing protocol *only* for static type-checkers – we do **not** need to
# subclass it at runtime.
from .base import ProviderProtocol
from .base import track_usage

class GeminiProvider:  # implements ProviderProtocol via duck-typing
    def __init__(self, api_key: Optional[str] = None):
        global genai, types  # noqa: PLW0603 – we intentionally mutate module globals

        # Lazy-load the Google SDK only when the provider is actually
        # instantiated (i.e. during *production* runs, not unit-tests that
        # only touch auxiliary helpers like _assemble_prompt).
        if genai is None or types is None:
            try:
                from google import genai as _genai  # type: ignore
                from google.genai import types as _types  # type: ignore

                genai = _genai  # promote to module-level for reuse
                types = _types
            except ImportError as e:
                # Surface a clear, actionable message **only** when the class
                # is actually used.  This keeps import-time side effects
                # minimal and avoids breaking unrelated tests.
                raise ImportError(
                    "The google-genai SDK is required to use GeminiProvider."
                    "\n   ➜  pip install google-genai"
                ) from e

        key = api_key or os.getenv("GOOGLE_API_KEY")
        if not key:
            raise ValueError("GOOGLE_API_KEY not set")

        # Initialize client directly with the API key (newer SDK style)
        self._client = genai.Client(api_key=key)

    @track_usage
    def generate(self, system_prompt: str, user_prompt: str, model: str, temperature: float = 0.0, *, top_k: int | None = None, top_p: float | None = None) -> str:
        cfg = {"temperature": temperature}
        # Use provided sampling params falling back to defaults
        if top_p is not None:
            cfg["top_p"] = float(top_p)
        else:
            cfg["top_p"] = 0.1
        if top_k is not None:
            cfg["top_k"] = int(top_k)
        else:
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
            def _safe_int(val):
                try:
                    return int(val or 0)
                except Exception:
                    return 0

            prompt_toks = _safe_int(getattr(usage_meta, 'prompt_token_count', 0))
            # SDK renamed field from response_token_count → candidates_token_count
            resp_toks = _safe_int(getattr(usage_meta, 'response_token_count', getattr(usage_meta, 'candidates_token_count', 0)))
            thought_toks = _safe_int(getattr(usage_meta, 'thoughts_token_count', 0))
            total_toks = _safe_int(getattr(usage_meta, 'total_token_count', 0))
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
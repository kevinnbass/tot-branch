from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

from .base import ProviderProtocol

if TYPE_CHECKING:
    # Avoid circular imports during type checking
    from .gemini import GeminiProvider
    from .openrouter import OpenRouterProvider

__all__ = ["ProviderProtocol", "get_provider", "GeminiProvider", "OpenRouterProvider"]


def get_provider(name: str, **kwargs) -> ProviderProtocol:
    """Factory function to create provider instances.
    
    Args:
        name: Provider name ('gemini' or 'openrouter').
        **kwargs: Additional arguments passed to provider constructor.
        
    Returns:
        Provider instance implementing ProviderProtocol.
        
    Raises:
        ValueError: If provider name is not recognized.
        ImportError: If provider module cannot be imported.
    """
    provider_map = {
        "gemini": "multi_coder_analysis.providers.gemini",
        "openrouter": "multi_coder_analysis.providers.openrouter",
    }
    
    if name not in provider_map:
        raise ValueError(f"Unknown provider: {name}. Available: {list(provider_map.keys())}")
    
    try:
        module = import_module(provider_map[name])

        from inspect import isclass

        # Collect *all* candidate classes that look like providers.
        candidates = [
            getattr(module, attr_name)
            for attr_name in dir(module)
            if attr_name.endswith("Provider") and isclass(getattr(module, attr_name))
        ]

        # Return the first class that satisfies the minimal interface.
        for cls in candidates:
            if all(hasattr(cls, m) for m in ("generate", "get_last_thoughts", "get_last_usage")):
                return cls(**kwargs)

        raise ImportError(f"No provider class found in {provider_map[name]}")
        
    except ImportError as e:
        raise ImportError(f"Could not import provider {name}: {e}") from e


# Re-export provider classes for direct import
def __getattr__(name: str):
    """Lazy import of provider classes."""
    if name == "GeminiProvider":
        from .gemini import GeminiProvider
        return GeminiProvider
    elif name == "OpenRouterProvider":
        from .openrouter import OpenRouterProvider
        return OpenRouterProvider
    else:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") 
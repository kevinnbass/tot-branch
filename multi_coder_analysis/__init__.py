"""multi_coder_analysis package

Light-weight namespace placeholder.  No heavy imports at module load time.
"""

from importlib import import_module as _import_module

# Re-export commonly used domain models at the package root for convenience
HopContext = _import_module("multi_coder_analysis.models.hop").HopContext  # type: ignore[attr-defined]
BatchHopContext = _import_module("multi_coder_analysis.models.hop").BatchHopContext  # type: ignore[attr-defined]

__all__ = [
    "HopContext",
    "BatchHopContext",
    "__version__",
]

# Semantic version for package consumers
__version__ = "0.5.2.dev0" 
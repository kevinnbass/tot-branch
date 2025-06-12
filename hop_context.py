"""
Top-level compatibility shim so that `import hop_context` works even if
`multi_coder_analysis` has not yet been imported.
"""

from importlib import import_module as _imp

_real = _imp("multi_coder_analysis.hop_context")

HopContext = _real.HopContext
BatchHopContext = _real.BatchHopContext

__all__ = [
    "HopContext",
    "BatchHopContext",
] 
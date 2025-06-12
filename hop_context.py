"""Compatibility shim – legacy modules import `hop_context` from project root.

This stub simply re-exports HopContext and BatchHopContext from
multi_coder_analysis.hop_context so that existing code/tests can continue to
`import hop_context` without modification.
"""

from multi_coder_analysis.hop_context import HopContext, BatchHopContext  # noqa: F401

__all__ = [
    "HopContext",
    "BatchHopContext",
] 
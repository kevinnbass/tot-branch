from importlib import import_module as _imp

# ---------------------------------------------------------------------------
# Backward-compat shim: early notebooks did
#   from multi_coder_analysis.core import Engine
# After the package re-org that path vanished.  Re-export the default
# implementation so existing user code keeps working without edits.
# ---------------------------------------------------------------------------

Engine = _imp("multi_coder_analysis.core.regex").Engine  # type: ignore[attr-defined]

__all__: list[str] = ["Engine"]

# Export consensus utilities for external reuse
from .consensus import ConsensusStep  # type: ignore[E402,F401]
__all__.append("ConsensusStep") 
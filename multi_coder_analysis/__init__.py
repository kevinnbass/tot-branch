"""multi_coder_analysis package

This file enables `import multi_coder_analysis.*` across the repo and in
test suites. It purposefully keeps the namespace light to avoid heavy
imports at module-load time.

# ---------------------------------------------------------------------------
# Compatibility shim: some old test suites import `hop_context` directly from
# the project root.  Expose it under that name so `import hop_context` works
# regardless of the package layout.
# ---------------------------------------------------------------------------

import sys as _sys
from importlib import import_module as _import_module

if "hop_context" not in _sys.modules:
    _sys.modules["hop_context"] = _import_module(".hop_context", __name__)
""" 
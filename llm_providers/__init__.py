"""Top-level alias that forwards `import llm_providers` to the real package
inside `multi_coder_analysis.llm_providers`.

This allows third-party or legacy code to write

    from llm_providers.gemini_provider import GeminiProvider

regardless of the current working directory.
"""

import sys as _sys
from importlib import import_module as _import_module
import warnings as _warnings

_pkg = _import_module("multi_coder_analysis.llm_providers")
_sys.modules[__name__] = _pkg

# Re-export names for `from llm_providers import X` convenience
from multi_coder_analysis.llm_providers import *  # noqa: F401,F403

_warnings.warn(
    "`llm_providers.*` is deprecated; use `multi_coder_analysis.providers.*`",
    DeprecationWarning,
    stacklevel=2,
) 
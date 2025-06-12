"""Alias so `import utils.xxx` resolves in test environment.

We forward the import to `multi_coder_analysis.utils`.
"""

import sys as _sys
from importlib import import_module as _import_module

_pkg = _import_module("multi_coder_analysis.utils")
_sys.modules[__name__] = _pkg

from multi_coder_analysis.utils import *  # noqa: F401,F403 
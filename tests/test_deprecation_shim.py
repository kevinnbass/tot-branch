import importlib
import sys
import warnings

import pytest


def test_llm_providers_deprecation():
    """Importing the legacy top-level package must raise DeprecationWarning and resolve to the real providers package."""
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always", DeprecationWarning)
        mod = importlib.import_module("llm_providers")
        # Trigger re-import to guarantee warning path each test run
        importlib.reload(mod)

    assert any(isinstance(w.message, DeprecationWarning) for w in rec), "DeprecationWarning not raised"
    # The shim should ultimately be the exact same module as the core providers package
    real = sys.modules.get("multi_coder_analysis.llm_providers")
    assert real is not None, "Core providers module not found"
    assert sys.modules["llm_providers"] is real 
"""Pytest configuration to ensure the project root is importable.

Many CI runners execute tests from arbitrary working directories; make sure
`multi_coder_analysis` can always be imported regardless of where pytest was
invoked.
"""

import sys
from pathlib import Path

# Append the repository root (one level up from the tests directory) to
# sys.path if it is not already there.
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# ---------------------------------------------------------------------------
# Compatibility for older unit tests that call `monkeypatch.setitem(..., raising=False)`
# on pytest versions where that kwarg is not accepted. Provide a proxy method
# that silently ignores the flag so the call succeeds.
# ---------------------------------------------------------------------------

from _pytest.monkeypatch import MonkeyPatch  # type: ignore


def _setitem_compat(self, mapping, name, value, raising=True):  # noqa: D401
    """Drop the *raising* kwarg for backward compatibility."""
    mapping[name] = value

# Patch only if method signature lacks *raising* (older pytest will accept ours too)
if "_original_setitem" not in dir(MonkeyPatch):
    MonkeyPatch._original_setitem = MonkeyPatch.setitem  # type: ignore[attr-defined]
    MonkeyPatch.setitem = _setitem_compat  # type: ignore[assignment] 
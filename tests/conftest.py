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
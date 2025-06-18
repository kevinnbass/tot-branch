from __future__ import annotations

"""Text normalisation helpers for the Avian-Flu framing pipeline.

Currently provides:
    • normalise_unicode – replace curly quotes and various dash types with
      their ASCII equivalents so that regex patterns do not miss matches.

The helper is intentionally lightweight and stateless so it can be called
at the very start of any preprocessing pipeline without extra deps.
"""

from typing import Iterable

__all__ = ["normalise_unicode", "NORMALISE_TRANS_TABLE"]

NORMALISE_TRANS_TABLE = str.maketrans({
    "“": '"', "”": '"',
    "‘": "'", "’": "'",
    "—": "-", "–": "-", "―": "-",
})


def normalise_unicode(text: str | Iterable[str]) -> str | list[str]:
    """Return *text* with smart-quotes and em/en-dashes replaced.

    If *text* is an iterable of strings (e.g. list of segments) the function
    returns a **new list** with each element normalised.
    """
    if isinstance(text, str):
        return text.translate(NORMALISE_TRANS_TABLE)
    return [t.translate(NORMALISE_TRANS_TABLE) for t in text] 
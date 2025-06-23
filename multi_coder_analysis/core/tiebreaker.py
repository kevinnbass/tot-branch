from __future__ import annotations

"""Generic tie-breaking utilities used by consensus layers."""

from collections import Counter
from typing import List, Optional, Tuple

__all__ = ["conservative_tiebreak"]


def conservative_tiebreak(votes: List[str]) -> Tuple[bool, Optional[str]]:
    """Return (has_consensus, winning_value).

    The function implements a conservative rule: a value only wins if it
    secures *strict* (>50 %) majority.  Otherwise, it reports no consensus.
    """
    ctr = Counter(votes)
    if not ctr:
        return False, None
    winner, n = ctr.most_common(1)[0]
    if n > len(votes) / 2:
        return True, winner
    return False, None 
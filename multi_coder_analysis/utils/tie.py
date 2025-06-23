from __future__ import annotations

"""Utility helpers for voting distributions."""

from typing import Dict

__all__ = ["is_perfect_tie"]


def is_perfect_tie(dist: Dict[str, int]) -> bool:
    """Return True when *dist* has an exact 50-50 split.

    Works for any number of labels (2-way, 3-way …) as long as the most
    frequent label accounts for exactly half of the votes.
    """
    if not dist:
        return False
    votes = list(dist.values())
    return max(votes) * 2 == sum(votes) 
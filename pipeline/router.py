"""router.py
Early-exit / precedence-aware router for framing pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, List, Sequence, Tuple, Optional, Union

__all__ = ["RouteOutcome", "route_segment"]


class RouteOutcome:
    """Simple namespace holding outcome labels for the router."""

    LABEL = "label"
    TO_HOP = "to_hop"
    TO_HOP1 = "to_hop_1"

    @classmethod
    def all(cls) -> Tuple[str, str, str]:  # pragma: no cover – utility
        return (cls.LABEL, cls.TO_HOP, cls.TO_HOP1)


# ---------------------------------------------------------------------------
# Duck-typed helper: in tests we often create ad-hoc objects (e.g. Match) with
# the required attributes.  However, when such a structure is missing we offer
# a minimal dataclass to simplify usage in REPLs / notebooks.
# ---------------------------------------------------------------------------
@dataclass
class _MatchProto:  # noqa: D401 – internal helper, not part of public API
    hop_id: int
    frame: str
    cue: str
    rule_name: Optional[str] = None


MatchLike = Any


def _ensure_matches_iterable(matches: Any) -> List[MatchLike]:  # type: ignore[override]
    """Return *matches* as a list; raise TypeError if unusable."""

    if matches is None:
        return []
    if isinstance(matches, (list, tuple, set)):
        return list(matches)

    # Single object – wrap it
    return [matches]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def route_segment(
    segment_id: str,
    matches: Union[Sequence[MatchLike], MatchLike, None],
) -> Tuple[str, Any, Any]:
    """Determine the next action for a given text segment.

    The router implements a 4-step precedence-aware early-exit strategy:

    1. **Single hit** – If exactly one rule fires at the top hop precedence, we
       deterministically label the segment and stop.
    2. **Unanimous frame** – If multiple top-precedence rules fire but they all
       agree on the frame, we still label (cues concatenated with `;`).
    3. **Conflict** – If top-precedence rules disagree, we fall back to the
       corresponding hop (start ring-processing there) but prune the rule set to
       *only* the conflicting rules.
    4. **No match** – If no rule fires, fall through to the default hop-1
       processing.

    Parameters
    ----------
    segment_id:
        Opaque identifier for logging / debugging.  Unused in the logic but
        included for signature parity with the legacy pipeline.
    matches:
        Iterable of objects each exposing at least the attributes:
        `hop_id` (int), `frame` (str), `cue` (str) and *optionally*
        `rule_name` (str).

    Returns
    -------
    tuple
        A 3-tuple whose first element indicates the outcome (`RouteOutcome.*`).
        The meaning of the remaining elements depends on the outcome:

        • LABEL   → (frame, cue)
        • TO_HOP  → (hop_id, pruned_rule_names)
        • TO_HOP1 → (None, None)
    """

    # ----------------------------------------------------
    # Defensive normalisation of the *matches* input
    # ----------------------------------------------------
    matches_list: List[MatchLike] = _ensure_matches_iterable(matches)

    if not matches_list:  # Step 4 – no hits at all
        return RouteOutcome.TO_HOP1, None, None

    # Group by precedence (lower hop_id == higher precedence)
    try:
        matches_list.sort(key=lambda m: m.hop_id)
    except AttributeError as e:  # pragma: no cover – will surface in tests
        raise AttributeError(
            "Each match object must expose a `hop_id` attribute"
        ) from e

    top_prec = matches_list[0].hop_id  # hop with highest precedence

    # Collect all matches that share the same precedence tier
    top_hits = [m for m in matches_list if m.hop_id == top_prec]

    # ----------------------------------------------
    # Step-1: single hit at this precedence tier
    # ----------------------------------------------
    if len(top_hits) == 1:
        m = top_hits[0]
        return RouteOutcome.LABEL, getattr(m, "frame", None), getattr(m, "cue", "")

    # ----------------------------------------------
    # Step-2: unanimous frame agreement
    # ----------------------------------------------
    frames = {getattr(m, "frame", None) for m in top_hits}

    if len(frames) == 1:
        frame = frames.pop()
        cues = [getattr(m, "cue", "") for m in top_hits]
        cue_joined = "; ".join(cues)
        return RouteOutcome.LABEL, frame, cue_joined

    # ----------------------------------------------
    # Step-3: conflicts remain → defer to hop runner
    # ----------------------------------------------
    pruned = [getattr(m, "rule_name", None) for m in top_hits]
    return RouteOutcome.TO_HOP, top_prec, pruned 
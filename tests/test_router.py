from dataclasses import dataclass
from typing import Optional

from pipeline.router import route_segment, RouteOutcome


@dataclass
class Match:
    hop_id: int
    frame: str
    cue: str
    rule_name: Optional[str] = None


def test_router_single_hit():
    m = [Match(hop_id=2, frame="Alarmist", cue="jumped 27%")]
    outcome, arg1, _ = route_segment("seg1", m)
    assert outcome == RouteOutcome.LABEL
    assert arg1 == "Alarmist"


def test_router_unanimous_multiple_hits():
    m = [
        Match(hop_id=1, frame="Neutral", cue="surged"),
        Match(hop_id=1, frame="Neutral", cue="jumped"),
    ]
    outcome, frame, cue = route_segment("seg2", m)
    assert outcome == RouteOutcome.LABEL
    assert frame == "Neutral"
    assert cue == "surged; jumped"


def test_router_conflict():
    m = [
        Match(hop_id=1, frame="Alarmist", cue="soared", rule_name="R1"),
        Match(hop_id=1, frame="Reassuring", cue="dropped", rule_name="R2"),
    ]
    outcome, hop, pruned = route_segment("seg3", m)
    assert outcome == RouteOutcome.TO_HOP
    assert hop == 1
    assert pruned == ["R1", "R2"]


def test_router_no_hits():
    outcome, arg1, arg2 = route_segment("seg4", [])
    assert outcome == RouteOutcome.TO_HOP1
    assert arg1 is None and arg2 is None 
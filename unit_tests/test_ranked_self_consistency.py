import pytest

from multi_coder_analysis.core.self_consistency import aggregate
from multi_coder_analysis.run_multi_coder_tot import _extract_frame_and_ranking


def test_extract_ranking():
    txt = "{""answer"": ""yes"", ""rationale"": ""ok""}\nRanking: Alarmist > Neutral > Reassuring"
    top, lst = _extract_frame_and_ranking(txt)
    assert top == "Alarmist"
    assert lst == ["Alarmist", "Neutral", "Reassuring"]


def test_extract_ranking_multiline():
    txt = "Ranking:\n1. Alarmist\n2. Neutral\n3. Reassuring"
    top, lst = _extract_frame_and_ranking(txt)
    assert top == "Alarmist"
    assert lst == ["Alarmist", "Neutral", "Reassuring"]


def test_irv_rule():
    pairs = [(["Alarmist", "Neutral"], 3), (["Neutral", "Alarmist"], 2)]
    ans, conf = aggregate(pairs, rule="irv")
    assert ans in ("Alarmist", "Neutral")
    assert 0 <= conf <= 1


def test_ranked_rule_normalised():
    pairs = [(["A", "B", "C"], 5), (["A", "C", "B"], 4)]
    ans, conf = aggregate(pairs, rule="ranked")
    assert ans == "A"
    assert 0 <= conf <= 1


def test_ranked_cost_tiebreak():
    """Weights tie, lower average cost should decide winner."""
    pairs = [
        (["A", "B"], 5),
        (["A"], 5),
        (["B"], 10),
        (["B", "A"], 10),
    ]
    ans, _ = aggregate(pairs, rule="ranked")
    assert ans == "A"


def test_irv_cost_tiebreak():
    pairs = [(["A", "B"], 5), (["B", "A"], 5)]  # tie in first round
    ans, _ = aggregate(pairs, rule="irv")
    # Both have same cost; alphabetical tie broken by average cost (equal) -> whichever strategy; ensure result in set
    assert ans in ("A", "B")


def test_ranked_weighted_borda_and_cost():
    """Borda-weighted counts tie; lower average cost should win."""
    pairs = [
        (["A", "B", "C"], 2),  # A top, low cost
        (["B", "A", "C"], 5),  # B top, higher cost
    ]
    ans, _ = aggregate(pairs, rule="ranked")
    assert ans == "A"  # votes tie (5-5); A cheaper → should win


def test_borda_cost_tiebreak():
    """Verify _borda uses cost to resolve score ties."""
    pairs = [
        (["A", "B"], 5),
        (["B", "A"], 2),
    ]
    ans, _ = aggregate(pairs, rule="borda")
    assert ans == "B"  # scores tie; B cheaper so must win


def test_mrr_cost_tiebreak():
    """Verify _mrr uses cost to resolve score ties."""
    pairs = [
        (["A", "B"], 5),
        (["B", "A"], 2),
    ]
    ans, _ = aggregate(pairs, rule="mrr")
    assert ans == "B"


def test_ranked_normalisation_invariant():
    """Length normalisation should **not** change the winner when votes differ significantly."""
    pairs = [
        (["A"], 4),
        (["B", "A"], 6),
    ]
    ans_raw, _ = aggregate(pairs, rule="ranked-raw")
    ans_norm, _ = aggregate(pairs, rule="ranked")
    assert ans_raw == ans_norm == "A"


# ---------------------------------------------------------------------------
# NEW TESTS FOR ROBUSTNESS IMPROVEMENTS (v2.32)
# ---------------------------------------------------------------------------


def test_case_insensitive_majority():
    pairs = [("alarmist", 3), ("Alarmist", 4), ("Alarmist", 2)]
    ans, _ = aggregate(pairs, rule="majority")
    assert ans.lower() == "alarmist"


def test_extract_ranking_no_keyword():
    txt = "Alarmist > Neutral > Reassuring"
    top, lst = _extract_frame_and_ranking(txt)
    assert top == "Alarmist"
    assert lst == ["Alarmist", "Neutral", "Reassuring"]


def test_extract_ranking_bullet_parentheses():
    txt = "Ranking:\n1) Alarmist\n2) Neutral\n3) Reassuring"
    top, lst = _extract_frame_and_ranking(txt)
    assert lst == ["Alarmist", "Neutral", "Reassuring"]
    assert top == "Alarmist" 
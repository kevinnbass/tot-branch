#  Auto-generated / hand-curated regex rules for deterministic hops.
#  Only absolutely unambiguous YES cues should live here.
#  If a rule matches, we answer "yes"; otherwise we defer to the LLM.
#  Initially we seed with a handful of high-precision patterns — extend via
#  the audit script.

#  NOTE: Multiple incremental patches merged – see CHANGELOG for details.

from __future__ import annotations

# Prefer the third-party "regex" engine. It is now *mandatory* because many
# upstream patterns rely on features (e.g. variable-width look-behind) that the
# built-in `re` module cannot provide.  Fail loudly if the dependency is
# missing so the developer notices immediately.
try:
    import regex as re  # type: ignore
except ImportError as e:  # pragma: no cover – test env expects regex to be installed
    raise RuntimeError(
        "✖ The regex rule extractor now requires the 'regex' package.\n"
        "   ➜  pip install regex"
    ) from e

import logging
import json  # legacy: some prompts may still embed JSON blobs
import textwrap
import yaml  # YAML front-matter parser (PATCH 6)
from dataclasses import dataclass, replace
from typing import List, Dict, Pattern, Optional
from pathlib import Path

__all__ = [
    "PatternInfo",
    "RAW_RULES",
    "COMPILED_RULES",
]

@dataclass(frozen=True)
class PatternInfo:
    """Metadata + raw patterns for a single hop-specific rule.

    Attributes
    ----------
    hop: int
        Hop/question index (1-12).
    name: str
        Descriptive identifier (CamelCase).
    yes_frame: str | None
        Frame name to override when rule fires (e.g. "Alarmist").
    yes_regex: str
        Raw regex that, when **present**, guarantees the answer is "yes".
    veto_regex: str | None
        Optional regex that, when present, *cancels* an otherwise positive
        match — useful for conservative disambiguation.
    mode: str
        "live"  – rule is active and may short-circuit the LLM.
        "shadow" – rule only logs and will *not* short-circuit.
    """

    hop: int
    name: str
    yes_frame: Optional[str]
    yes_regex: str
    veto_regex: Optional[str] = None
    mode: str = "live"


# ----------------------------------------------------------------------------
# Raw rule list – intentionally left EMPTY.
# All regex patterns now come from the auto-extracted shadow rules in the prompt files.
# (Live rules removed per latest design decision.)
# ----------------------------------------------------------------------------
RAW_RULES: List[PatternInfo] = []


# ----------------------------------------------------------------------------
# Compile rules per hop for fast lookup
# ----------------------------------------------------------------------------
COMPILED_RULES: Dict[int, List[PatternInfo]] = {}


# ----------------------------------------------------------------------------
# Helper: compile a rule to a runtime-ready PatternInfo with compiled regexes.
# Includes graceful downgrade to shadow mode on variable-width look-behind
# failures. Returns None when compilation is impossible.
# ----------------------------------------------------------------------------

def _compile_rule(rule: PatternInfo) -> Optional[PatternInfo]:
    try:
        compiled_yes = re.compile(rule.yes_regex, flags=re.I | re.UNICODE | re.VERBOSE)
        compiled_veto = (
            re.compile(rule.veto_regex, flags=re.I | re.UNICODE | re.VERBOSE)
            if rule.veto_regex
            else None
        )
    except re.error as e:
        msg = str(e)
        # Detect variable-width look-behind errors from stdlib `re` as a cue
        # to silently force the rule into shadow mode while still retaining it
        # for coverage metrics.
        if "(?<" in msg:
            logging.warning(
                f"Variable-width look-behind in rule {rule.name}; forcing shadow mode"
            )
            try:
                rule_shadow = replace(rule, mode="shadow")  # dataclasses.replace
                compiled_yes = re.compile(rule_shadow.yes_regex, flags=re.I | re.UNICODE | re.VERBOSE)
                compiled_veto = (
                    re.compile(rule_shadow.veto_regex, flags=re.I | re.UNICODE | re.VERBOSE)
                    if rule_shadow.veto_regex
                    else None
                )
                rule = rule_shadow
            except Exception as e2:  # still fails → give up
                logging.warning(f"Skipping rule {rule.name}: {e2}")
                return None
        else:
            logging.warning(f"Skipping invalid regex in rule {rule.name}: {e}")
            return None

    return PatternInfo(
        hop=rule.hop,
        name=rule.name,
        yes_frame=rule.yes_frame,
        yes_regex=compiled_yes,  # type: ignore[arg-type]
        veto_regex=compiled_veto,  # type: ignore[arg-type]
        mode=rule.mode,
    )


# ----------------------------------------------------------------------------
# Auto-extract additional patterns from the hop prompt files (optional).
# This scans multi_coder_analysis/prompts/hop_Q*.txt for ```regex ... ``` blocks
# and turns them into conservative PatternInfo objects (mode="shadow" by default)
# so they won't short-circuit unless promoted to live.
# ----------------------------------------------------------------------------

_DEFAULT_PROMPTS_DIR = Path(__file__).parent / "prompts"
# Allow external tests to monkeypatch `PROMPTS_DIR` to point at a temporary
# directory.  When this happens, we *also* want to keep the original project
# prompts available so that downstream logic (and other unit-tests) can still
# access the full rule set.  Therefore we scan **both** directories whenever
# they differ.
PROMPTS_DIR = globals().get("PROMPTS_DIR", _DEFAULT_PROMPTS_DIR)

_HOP_FILE_RE = re.compile(r"hop_Q(\d{2})\.txt")

def _infer_frame_from_hop(hop: int) -> str | None:
    if hop in {1, 2, 3, 4}:
        return "Alarmist"
    if hop in {5, 6}:
        return "Reassuring"
    return None  # leave to downstream logic


def _extract_patterns_from_prompts() -> list[PatternInfo]:
    """Extract shadow/live regex patterns from prompt files.

    If a test suite temporarily overrides ``PROMPTS_DIR`` (via monkeypatch) to
    point at an *isolated* directory, we automatically ALSO search the
    project's canonical prompt folder so that the full rule set remains
    available.  This dual-directory scan ensures that highly focused unit-
    tests (e.g. verifying YAML extraction) do not inadvertently starve later
    tests of the production patterns required for behavioural checks.
    """

    patterns: list[PatternInfo] = []

    def _gather_from_dir(dir_path: Path) -> None:
        if not dir_path.exists():
            return
        for path in dir_path.glob("hop_Q*.txt"):
            m = _HOP_FILE_RE.match(path.name)
            if not m:
                continue
            hop_idx = int(m.group(1))

            try:
                txt = path.read_text(encoding="utf-8")
            except Exception:
                continue

            # ── PATCH 7: parse optional YAML front-matter (--- ... ---) ----------
            meta_obj: dict | None = None
            FM_RE = re.compile(r"^\s*---[^\n]*\n(.*?)\n---\s*", re.DOTALL)
            fm_match = FM_RE.match(txt)
            if fm_match:
                try:
                    meta_obj = yaml.safe_load(fm_match.group(1)) or {}
                    hop_idx = int(meta_obj.get("hop", hop_idx))
                except Exception:
                    meta_obj = None

            # ── PATCH 1: robust fenced-block extractor ---------------------------
            FENCED_RE = re.compile(r"```regex\s+([\s\S]*?)```", re.IGNORECASE | re.DOTALL)

            for idx, m_block in enumerate(FENCED_RE.finditer(txt)):
                raw = (
                    textwrap.dedent(m_block.group(1))
                    .replace("\r\n", "\n")
                    .strip()
                )
                # super-conservative: skip if pattern seems empty or has lookbehinds (?<-)
                if not raw or "?<-" in raw:
                    continue

                # ── PATCH 2 cont. : use meta for name / mode / frame ------------
                name = (
                    (meta_obj and meta_obj.get("name"))
                    or f"Q{hop_idx:02}.Prompt#{idx+1}"
                )

                mode = meta_obj.get("mode", "shadow") if meta_obj else "shadow"
                frame = meta_obj.get("frame") if meta_obj else _infer_frame_from_hop(hop_idx)

                patterns.append(
                    PatternInfo(
                        hop=hop_idx,
                        name=name,
                        yes_frame=frame,
                        yes_regex=raw,
                        mode=mode,
                    )
                )

    # Scan the caller-specified prompt directory first (tests may monkeypatch).
    _gather_from_dir(PROMPTS_DIR)

    # Avoid duplicate rule objects when both paths are the *same* physical
    # location (common in production/CI).  Re-scanning identical folders
    # would yield two PatternInfo instances per fenced block which in turn
    # causes regex_engine.match() to deem results ambiguous (>1 live rule
    # fires) and return ``None``.
    try:
        if _DEFAULT_PROMPTS_DIR.resolve() != PROMPTS_DIR.resolve():
            _gather_from_dir(_DEFAULT_PROMPTS_DIR)
    except Exception:
        # Fallback: conservative behaviour—if path resolution fails for some
        # reason, perform the second scan (maintains previous semantics).
        _gather_from_dir(_DEFAULT_PROMPTS_DIR)

    return patterns


# Integrate extracted patterns (shadow / live) ------------------------------
RAW_RULES.extend(_extract_patterns_from_prompts())

# ---------------------------------------------------------------------------
# Compile all rules once
# ---------------------------------------------------------------------------

for idx, r in enumerate(RAW_RULES):
    compiled = _compile_rule(r)
    if compiled is None:
        continue

    # Skip if an *identical* pattern for the same hop is already registered (prevents
    # ambiguity when prompt files are scanned/reloaded multiple times)
    if any(getattr(e.yes_regex, "pattern", None) == getattr(compiled.yes_regex, "pattern", None)
           for e in COMPILED_RULES.get(compiled.hop, [])):
        continue

    # Persist the *compiled* version back into RAW_RULES so downstream
    # callers (including unit-tests) can introspect attributes like
    # ``yes_regex.pattern`` without having to replicate the compilation
    # logic.  Keeping the list in-sync avoids a common gotcha where tests
    # accidentally work with the uncompiled objects (plain strings) and then
    # fail when they access `.pattern`.
    RAW_RULES[idx] = compiled

    # Build fast lookup map used at runtime by the regex engine.
    COMPILED_RULES.setdefault(compiled.hop, []).append(compiled) 
from __future__ import annotations

from pathlib import Path
from pydantic import BaseModel, Field, validator, root_validator

__all__ = ["RunConfig"]


class RunConfig(BaseModel):
    """Central runtime configuration for ToT execution."""

    phase: str = Field(
        "pipeline",
        pattern="^(legacy|pipeline)$",
        description="Execution mode: 'legacy' = old monolithic runner, 'pipeline' = new modular ToT stack",
    )
    dimension: str | None = Field(
        None,
        description="(deprecated) reserved for backward compatibility; ignored by pipeline",
    )
    input_csv: Path = Field(..., description="Path to input CSV of statements")
    output_dir: Path = Field(..., description="Directory to write outputs")
    provider: str = Field("gemini", pattern="^(gemini|openrouter)$", description="LLM provider to use")
    model: str = Field("models/gemini-2.5-flash-preview-04-17", description="Model identifier")
    batch_size: int = Field(1, ge=1, description="Batch size for LLM calls")

    # Worker-local file suffix for archive (permutation tag, etc.)
    archive_tag: str | None = Field(
        None,
        description="Optional tag appended to run_id for per-worker archive files",
    )

    concurrency: int = Field(1, ge=1, description="Thread pool size for batch mode")
    regex_mode: str = Field("live", pattern="^(live|shadow|off)$", description="Regex layer mode")
    shuffle_batches: bool = Field(False, description="Randomise batch order for load spreading")
    shuffle_segments: bool = Field(False, description="Randomise segments within each batch for maximum stochasticity")
    consensus_mode: str = Field(
        "final",
        pattern="^(hop|final)$",
        description="Consensus strategy: 'hop' = per-hop majority, 'final' = legacy end-of-tree vote",
    )

    # ---------------- Self-consistency decoding ----------------
    decode_mode: str = Field(
        "normal",
        pattern="^(normal|self-consistency)$",
        description="Decoding mode: normal = single path, self-consistency = multi-path sampling + voting",
    )

    sc_votes: int = Field(1, ge=1, le=200, description="Number of sampled paths for self-consistency")
    sc_rule: str = Field(
        "majority",
        pattern=(
            r"^(majority|"                     # legacy
            r"ranked|ranked-raw|"              # legacy weighted
            r"irv|borda|mrr|"                  # new ranked-list rules
            r"confidence-weighted|confidence)$" # confidence-enhanced rules
        ),
        description=(
            "Aggregation rule:\n"
            "  • majority        – single-answer hard vote\n"
            "  • ranked          – single-answer length-norm\n"
            "  • ranked-raw      – single-answer raw score\n"
            "  • irv|borda|mrr   – ranked-list self-consistency\n"
            "  • confidence-weighted – uses confidence scores and frame likelihoods",
        ),
    )
    sc_top_k: int = Field(40, ge=0, description="top-k sampling cutoff (0 disables)")
    sc_top_p: float = Field(0.95, ge=0.0, le=1.0, description="nucleus sampling p-value")
    sc_temperature: float = Field(0.7, ge=0.0, description="Sampling temperature for self-consistency")

    # housekeeping – whether tot_runner should copy & concatenate the prompts
    copy_prompts: bool = Field(True, description="Copy prompt folder into output_dir and concatenate prompts.txt")

    # ───────── Ranked-list decoding ─────────
    ranked_list: bool = Field(
        False,
        description=(
            "If true, prompts instruct model to emit an ordered list "
            "of candidate answers instead of a single value.",
        ),
    )
    max_candidates: int = Field(
        5,
        ge=1,
        le=10,
        description="Max candidates to keep from the ranked list. "
                    "Ignored when ranked_list == False.",
    )

    # ───────── Confidence-enhanced RLSC ─────────
    confidence_scores: bool = Field(
        False,
        description=(
            "If true, prompts request confidence scores (0-100%) for binary decisions "
            "and frame likelihood scores for RLSC. Enables enhanced self-consistency aggregation."
        ),
    )

    # ─────────────────────────────────────────────────────────────
    # Root-level validator – field order requires this approach.
    # ─────────────────────────────────────────────────────────────
    @root_validator(skip_on_failure=True)
    def _validate_ranked_combo(cls, values):  # noqa: D401
        ranked = values.get("ranked_list", False)
        rule = values.get("sc_rule")
        decode_mode = values.get("decode_mode")
        confidence_scores = values.get("confidence_scores", False)
        
        if ranked:
            if decode_mode != "self-consistency":
                raise ValueError("ranked_list=True requires decode_mode='self-consistency'")
            if rule not in {"irv", "borda", "mrr"}:
                raise ValueError(
                    "When ranked_list=True, sc_rule must be one of {'irv', 'borda', 'mrr'}"
                )
        
        # Validate confidence-weighted aggregation
        if rule in {"confidence-weighted", "confidence"}:
            if not confidence_scores:
                raise ValueError("confidence-weighted aggregation requires confidence_scores=True")
            if decode_mode != "self-consistency":
                raise ValueError("confidence-weighted aggregation requires decode_mode='self-consistency'")
        
        return values

    @validator("output_dir", pre=True)
    def _expand_output_dir(cls, v):  # noqa: D401
        return Path(v).expanduser().absolute()

    @validator("input_csv", pre=True)
    def _expand_input_csv(cls, v):  # noqa: D401
        return Path(v).expanduser().absolute()

    # ----- deprecations -----
    @validator("decode_mode", pre=True)
    def _alias_perm(cls, v):  # noqa: D401
        if v == "permute":
            import warnings
            warnings.warn(
                "decode_mode='permute' is deprecated and treated as 'normal'.",
                DeprecationWarning,
                stacklevel=2,
            )
            return "normal"
        return v 
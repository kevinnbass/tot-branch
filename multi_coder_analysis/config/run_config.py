from __future__ import annotations

from pathlib import Path
from pydantic import BaseModel, Field, validator

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
        pattern="^(majority|ranked|ranked-raw)$",
        description="Voting aggregation rule for self-consistency",
    )
    sc_top_k: int = Field(40, ge=0, description="top-k sampling cutoff (0 disables)")
    sc_top_p: float = Field(0.95, ge=0.0, le=1.0, description="nucleus sampling p-value")
    sc_temperature: float = Field(0.7, ge=0.0, description="Sampling temperature for self-consistency")

    # housekeeping – whether tot_runner should copy & concatenate the prompts
    copy_prompts: bool = Field(True, description="Copy prompt folder into output_dir and concatenate prompts.txt")

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
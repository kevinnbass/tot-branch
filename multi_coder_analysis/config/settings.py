from __future__ import annotations

"""Pydantic Settings model for configuration (Phase 6)."""

from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict
from typing import Optional
from pathlib import Path

__all__ = ["Settings"]


class Settings(BaseSettings):
    """Application settings with environment variable overrides.
    
    Environment variables are prefixed with MCA_ (e.g., MCA_PROVIDER=openrouter).
    """
    
    # Core execution settings
    phase: str = Field("pipeline", description="Pipeline phase label")
    provider: str = Field("gemini", description="LLM provider name")
    model: str = Field("models/gemini-2.5-flash-preview-04-17", description="Model identifier")
    
    # Performance settings
    batch_size: int = Field(10, ge=1, description="Batch size for LLM calls")
    concurrency: int = Field(1, ge=1, description="Thread pool size")
    
    # Feature flags
    enable_regex: bool = Field(True, description="Enable regex short-circuiting")
    regex_mode: str = Field("live", description="Regex mode: live|shadow|off")
    shuffle_batches: bool = Field(False, description="Randomise batch order")
    shuffle_segments: bool = Field(False, description="Randomise segments within batches")
    
    # API keys (optional - can be set via environment)
    google_api_key: Optional[str] = Field(None, description="Google Gemini API key")
    openrouter_api_key: Optional[str] = Field(None, description="OpenRouter API key")
    
    # Observability
    log_level: str = Field("INFO", description="Log level")
    json_logs: bool = Field(False, description="Emit JSON-formatted logs")
    
    # ---------------- Lazy materialisation ----------------
    archive_enable: bool = Field(
        True,
        description="Enable on-disk archiving of concluded segments",
    )
    archive_dir: Path = Field(
        default=Path("output/archive"),
        description="Directory for JSONL archives (auto-created)",
    )
    
    model_config = ConfigDict(
        env_prefix="MCA_",
        env_file=".env",
        case_sensitive=False,
        # Accept legacy keys that are no longer explicitly modelled so that
        # users can keep an old config.yaml without breaking validation.
        extra="allow"
    ) 
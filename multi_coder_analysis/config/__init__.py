from __future__ import annotations

"""Configuration loading utilities (Phase 6)."""

import warnings
from functools import lru_cache
from pathlib import Path
import yaml

# ---------------------------------------------------------------------------
# Optional dependency guard – ``Settings`` relies on *pydantic-settings* which
# may be absent in minimal runtime environments.  We fall back to a dummy class
# that behaves like an empty mapping so that modules which only import
# ``multi_coder_analysis.config`` for its *side effects* (i.e. our permutation
# workers) do not crash.  Full-feature runs that *need* Settings should add the
# dependency as usual:  pip install pydantic-settings
# ---------------------------------------------------------------------------

try:
    from .settings import Settings  # noqa: F401
except ModuleNotFoundError as _e:
    if _e.name == "pydantic_settings":
        warnings.warn(
            "pydantic_settings not installed – falling back to minimal Settings stub.",
            RuntimeWarning,
            stacklevel=2,
        )

        class Settings(dict):  # type: ignore
            """Minimal stub that accepts **kwargs and stores them."""

            def __init__(self, **kwargs):
                super().__init__(**kwargs)

            # maintain attribute access semantics used elsewhere
            def __getattr__(self, item):
                return self.get(item)

            def dict(self):  # mimic Pydantic API subset
                return dict(self)

    else:
        raise

_CFG_PATH = Path.cwd() / "config.yaml"


@lru_cache(maxsize=1)
def load_settings(path: Path | None = None) -> Settings:  # noqa: D401
    """Load settings from *path* or environment overrides.
    
    If *config.yaml* is detected, it is parsed and **deprecated** – values are
    fed into the new Pydantic Settings model and a warning is issued.
    """
    cfg_path = Path(path) if path else _CFG_PATH

    if cfg_path.exists():
        warnings.warn(
            "Reading legacy config.yaml is deprecated; migrate to environment variables or TOML config.",
            DeprecationWarning,
            stacklevel=2,
        )
        try:
            data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        except Exception as e:
            warnings.warn(f"Could not parse {cfg_path}: {e}")
            data = {}
    else:
        data = {}

    return Settings(**data) 
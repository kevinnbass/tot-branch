from __future__ import annotations

"""Structured logging and tracing utilities (Phase 8)."""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import structlog  # type: ignore
except ModuleNotFoundError:  # pragma: no cover – optional dependency
    import types, sys, logging

    class _StructlogStubModule(types.ModuleType):
        """Very small stub covering only attributes we use in this file."""

        def get_logger(self, *_args, **_kwargs):  # noqa: D401 – stub
            class _Dummy:
                def bind(self, **_kw):
                    return self

                def __getattr__(self, _name):
                    def _noop(*_a, **_kw):
                        pass

                    return _noop

            return _Dummy()

        # Factories used in setup_logging(); they just return pass-through callables
        def make_filtering_bound_logger(self, *_a, **_kw):  # noqa: ANN002
            def _wrapper(logger):
                return logger

            return _wrapper

        class processors:  # noqa: D401
            class TimeStamper:  # noqa: D401
                def __init__(self, *_, **__):
                    pass

            @staticmethod
            def add_log_level(*_a, **_kw):
                pass

            class StackInfoRenderer:  # noqa: D401
                def __call__(self, *_, **__):
                    pass

            @staticmethod
            def JSONRenderer(*_a, **_kw):
                def _json_proc(event_dict):
                    return str(event_dict)

                return _json_proc

        class dev:  # noqa: D401
            @staticmethod
            def ConsoleRenderer(*_a, **_kw):
                def _console_proc(event_dict):
                    return str(event_dict)

                return _console_proc

        def configure(self, *_, **__):
            pass

        class WriteLoggerFactory:  # noqa: D401
            def __call__(self, *a, **kw):  # noqa: ANN001
                return logging.getLogger("structlog_stub")

    structlog = _StructlogStubModule("structlog_stub")  # type: ignore
    sys.modules["structlog"] = structlog

__all__ = ["setup_logging", "get_logger", "TraceWriter"]

# Global run ID for this process
_RUN_ID = str(uuid.uuid4())


def setup_logging(level: str = "INFO", json_logs: bool = False) -> None:
    """Configure structured logging for the application.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        json_logs: If True, emit JSON-formatted logs
    """
    
    # Configure standard library logging
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s" if not json_logs else None,
    )
    
    # Configure structlog
    processors = [
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
    ]
    
    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.extend([
            structlog.dev.ConsoleRenderer(),
        ])
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper())
        ),
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name).bind(run_id=_RUN_ID)


class TraceWriter:
    """NDJSON trace writer with envelope metadata."""
    
    def __init__(self, trace_dir: Path):
        self.trace_dir = Path(trace_dir)
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        self._run_id = _RUN_ID
        
    def write_trace(self, statement_id: str, trace_data: Dict[str, Any]) -> None:
        """Write a single trace entry.
        
        Args:
            statement_id: Unique identifier for the statement
            trace_data: Trace payload data
        """
        envelope = {
            "run_id": self._run_id,
            "statement_id": statement_id,
            "timestamp": datetime.now().isoformat(),
            "trace_data": trace_data,
        }
        
        trace_file = self.trace_dir / f"{statement_id}.ndjson"
        with trace_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(envelope, ensure_ascii=False) + "\n")
    
    def write_batch_trace(self, batch_id: str, hop_idx: int, batch_data: Dict[str, Any]) -> None:
        """Write a batch trace entry.
        
        Args:
            batch_id: Unique identifier for the batch
            hop_idx: Hop number (1-12)
            batch_data: Batch processing data
        """
        envelope = {
            "run_id": self._run_id,
            "batch_id": batch_id,
            "hop_idx": hop_idx,
            "timestamp": datetime.now().isoformat(),
            "batch_data": batch_data,
        }
        
        batch_dir = self.trace_dir / "batches"
        batch_dir.mkdir(exist_ok=True)
        batch_file = batch_dir / f"{batch_id}_Q{hop_idx:02d}.ndjson"
        
        with batch_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(envelope, ensure_ascii=False) + "\n")
    
    def write_run_summary(self, summary_data: Dict[str, Any]) -> None:
        """Write a run-level summary.
        
        Args:
            summary_data: Summary statistics and metadata
        """
        envelope = {
            "run_id": self._run_id,
            "timestamp": datetime.now().isoformat(),
            "summary_data": summary_data,
        }
        
        summary_file = self.trace_dir / f"run_summary_{self._run_id}.ndjson"
        with summary_file.open("w", encoding="utf-8") as f:
            f.write(json.dumps(envelope, ensure_ascii=False) + "\n")


# Legacy compatibility adapters
def write_trace_log(trace_dir: Path, statement_id: str, trace_entry: Dict[str, Any]) -> None:
    """Legacy adapter for existing trace writing code."""
    writer = TraceWriter(trace_dir)
    writer.write_trace(statement_id, trace_entry)


def write_batch_trace(trace_dir: Path, batch_id: str, hop_idx: int, batch_payload: Dict[str, Any]) -> None:
    """Legacy adapter for existing batch trace writing code."""
    writer = TraceWriter(trace_dir)
    writer.write_batch_trace(batch_id, hop_idx, batch_payload) 
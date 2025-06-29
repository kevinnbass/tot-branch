"""Custom exceptions and error handling utilities for the Multi-Coder Analysis system."""

from __future__ import annotations

import logging
import traceback
from functools import wraps
from typing import Any, Callable, Optional, Type, Union, TypeVar, Dict
from enum import Enum

__all__ = [
    "AnalysisError", "ConfigurationError", "LLMProviderError", "RegexEngineError",
    "PipelineError", "ValidationError", "RetryableError", "ErrorSeverity",
    "error_handler", "retry_on_failure"
]

T = TypeVar('T')


class ErrorSeverity(Enum):
    """Error severity levels for categorizing exceptions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnalysisError(Exception):
    """Base exception for all analysis-related errors."""
    
    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.severity = severity
        self.error_code = error_code
        self.details = details or {}
    
    def __str__(self) -> str:
        parts = [self.message]
        if self.error_code:
            parts.append(f"(Code: {self.error_code})")
        if self.details:
            parts.append(f"Details: {self.details}")
        return " ".join(parts)


class ConfigurationError(AnalysisError):
    """Raised when configuration is invalid or missing."""
    
    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        super().__init__(message, severity=ErrorSeverity.HIGH, **kwargs)
        self.config_key = config_key


class LLMProviderError(AnalysisError):
    """Raised when LLM provider operations fail."""
    
    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        retry_after: Optional[int] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.provider = provider
        self.model = model
        self.retry_after = retry_after


class RegexEngineError(AnalysisError):
    """Raised when regex engine operations fail."""
    
    def __init__(
        self,
        message: str,
        pattern: Optional[str] = None,
        rule_name: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.pattern = pattern
        self.rule_name = rule_name


class PipelineError(AnalysisError):
    """Raised when pipeline execution fails."""
    
    def __init__(
        self,
        message: str,
        step: Optional[str] = None,
        hop: Optional[int] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.step = step
        self.hop = hop


class ValidationError(AnalysisError):
    """Raised when data validation fails."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs
    ):
        super().__init__(message, severity=ErrorSeverity.MEDIUM, **kwargs)
        self.field = field
        self.value = value


class RetryableError(AnalysisError):
    """Raised when an operation can be retried."""
    
    def __init__(
        self,
        message: str,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor


def error_handler(
    logger: Optional[logging.Logger] = None,
    reraise: bool = True,
    default_return: Any = None,
    handled_exceptions: tuple[Type[Exception], ...] = (Exception,)
) -> Callable[[Callable[..., T]], Callable[..., Union[T, Any]]]:
    """Decorator for consistent error handling."""
    def decorator(func: Callable[..., T]) -> Callable[..., Union[T, Any]]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Union[T, Any]:
            try:
                return func(*args, **kwargs)
            except handled_exceptions as e:
                error_logger = logger or logging.getLogger(func.__module__)
                
                # Log the error with context
                error_logger.error(
                    f"Error in {func.__name__}: {e}",
                    exc_info=True,
                    extra={
                        'function': func.__name__,
                        'args': str(args)[:200],  # Truncate for logging
                        'kwargs': str(kwargs)[:200],
                        'error_type': type(e).__name__
                    }
                )
                
                if reraise:
                    raise
                else:
                    return default_return
        
        return wrapper
    return decorator


def retry_on_failure(
    max_retries: int = 3,
    backoff_factor: float = 1.0,
    exceptions: tuple[Type[Exception], ...] = (Exception,),
    logger: Optional[logging.Logger] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for retrying failed operations."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            retry_logger = logger or logging.getLogger(func.__module__)
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        retry_logger.error(
                            f"Function {func.__name__} failed after {max_retries} retries: {e}"
                        )
                        raise
                    
                    # Calculate backoff delay
                    delay = backoff_factor * (2 ** attempt)
                    retry_logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}), "
                        f"retrying in {delay:.1f}s: {e}"
                    )
                    
                    import time
                    time.sleep(delay)
            
            # This should never be reached, but satisfies type checker
            raise RuntimeError("Unexpected exit from retry loop")
        
        return wrapper
    return decorator


def format_error_details(error: Exception) -> Dict[str, Any]:
    """Format error details for structured logging."""
    details = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'traceback': traceback.format_exc()
    }
    
    # Add custom error attributes if available
    if isinstance(error, AnalysisError):
        details.update({
            'severity': error.severity.value,
            'error_code': error.error_code,
            'details': error.details
        })
    
    return details


class ErrorReporter:
    """Centralized error reporting and tracking."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.error_counts: Dict[str, int] = {}
    
    def report_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        count: bool = True
    ) -> None:
        """Report an error with context."""
        error_details = format_error_details(error)
        
        if context:
            error_details.update(context)
        
        self.logger.error(
            f"Error reported: {error}",
            extra=error_details
        )
        
        if count:
            error_type = type(error).__name__
            self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
    
    def get_error_stats(self) -> Dict[str, int]:
        """Get error statistics."""
        return self.error_counts.copy()
    
    def reset_stats(self) -> None:
        """Reset error statistics."""
        self.error_counts.clear()

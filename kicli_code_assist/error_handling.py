"""Error handling and recovery for LLM operations.

Provides user-friendly error messages, retry logic with exponential backoff,
and structured error information for better diagnostics.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional, TypeVar, Union

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ErrorSeverity(Enum):
    """Error severity levels for UX presentation."""
    INFO = "ℹ️"           # Non-error, just info
    WARNING = "⚠️"        # Something unexpected, but recoverable
    ERROR = "❌"          # User action needed
    CRITICAL = "🔴"       # System failure, need ops


class LLMError(Exception):
    """Base exception for LLM-related errors."""

    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        suggestion: Optional[str] = None,
        provider: Optional[str] = None,
        retryable: bool = False,
    ):
        self.message = message
        self.severity = severity
        self.suggestion = suggestion
        self.provider = provider
        self.retryable = retryable
        super().__init__(message)

    def user_message(self) -> str:
        """Format error for display in UI."""
        msg = f"{self.severity.value} {self.message}"
        if self.suggestion:
            msg += f"\n💡 {self.suggestion}"
        if self.retryable:
            msg += "\n🔄 This error is recoverable. Retrying automatically..."
        return msg


@dataclass
class RetryConfig:
    """Configuration for exponential backoff retry logic."""
    max_attempts: int = 3
    initial_delay: float = 1.0  # seconds
    max_delay: float = 10.0
    backoff_factor: float = 2.0
    jitter: bool = True


async def retry_with_backoff(
    coro_fn: Callable[[], Any],
    config: RetryConfig = RetryConfig(),
    on_retry: Optional[Callable[[int, Exception], None]] = None,
) -> Any:
    """Execute async function with exponential backoff retry.

    Args:
        coro_fn: Async function to retry (no arguments)
        config: Retry configuration
        on_retry: Callback when retry happens: (attempt_num, exception)

    Returns:
        Result from coro_fn

    Raises:
        LLMError: If all retries exhausted
    """
    delay = config.initial_delay
    last_error: Optional[Exception] = None

    for attempt in range(config.max_attempts):
        try:
            return await coro_fn()
        except (asyncio.TimeoutError, ConnectionError) as e:
            # Transient errors, retry
            last_error = e
            if attempt < config.max_attempts - 1:
                if on_retry:
                    on_retry(attempt + 1, e)
                
                # Add jitter to avoid thundering herd
                actual_delay = delay
                if config.jitter:
                    import random
                    actual_delay *= (0.5 + random.random())
                
                logger.warning(
                    f"Retryable error on attempt {attempt + 1}/{config.max_attempts}: {e}. "
                    f"Waiting {actual_delay:.1f}s..."
                )
                await asyncio.sleep(actual_delay)
                delay = min(delay * config.backoff_factor, config.max_delay)
            else:
                raise
        except Exception as e:
            # Non-retryable error, fail immediately
            raise

    # This shouldn't happen, but handle it
    if last_error:
        raise LLMError(
            f"Failed after {config.max_attempts} attempts: {last_error}",
            severity=ErrorSeverity.ERROR,
            retryable=False,
        )


def handle_provider_error(
    error: Exception,
    provider: str,
    context: Optional[str] = None,
) -> LLMError:
    """Convert provider-specific error to user-friendly LLMError.

    Args:
        error: The raw exception from provider
        provider: Provider name (openai, ollama, ki, etc)
        context: Additional context (prompt size, model, etc)

    Returns:
        LLMError with user-friendly message and suggestions
    """
    error_str = str(error)
    logger.error(f"Provider error ({provider}): {error_str} | Context: {context}")

    # OpenAI-specific errors
    if provider == "openai":
        if "401" in error_str or "Unauthorized" in error_str or "invalid_api_key" in error_str:
            return LLMError(
                "OpenAI API key is invalid or expired",
                severity=ErrorSeverity.ERROR,
                suggestion="Check your OpenAI API key in ki.yaml or creds.yaml",
                provider=provider,
                retryable=False,
            )
        elif "429" in error_str or "RateLimitError" in error_str:
            return LLMError(
                "OpenAI API rate limit exceeded",
                severity=ErrorSeverity.WARNING,
                suggestion="Wait a moment and try again",
                provider=provider,
                retryable=True,
            )
        elif "503" in error_str or "overloaded" in error_str.lower():
            return LLMError(
                "OpenAI service temporarily unavailable",
                severity=ErrorSeverity.WARNING,
                suggestion="The service will recover shortly",
                provider=provider,
                retryable=True,
            )
        elif "context_length_exceeded" in error_str or "token" in error_str.lower():
            return LLMError(
                "Prompt is too long for the model",
                severity=ErrorSeverity.ERROR,
                suggestion="Reduce file context or use a longer-context model",
                provider=provider,
                retryable=False,
            )

    # Ollama-specific errors
    elif provider == "ollama":
        if "Connection refused" in error_str or "Failed to connect" in error_str:
            return LLMError(
                f"Cannot connect to Ollama at {context or 'localhost:11434'}",
                severity=ErrorSeverity.ERROR,
                suggestion="Is Ollama running? Start with: ollama serve",
                provider=provider,
                retryable=True,
            )
        elif "model" in error_str.lower() and "not found" in error_str.lower():
            return LLMError(
                f"Ollama model not found: {context or '(unknown)'}",
                severity=ErrorSeverity.ERROR,
                suggestion="Pull the model with: ollama pull <model>",
                provider=provider,
                retryable=False,
            )

    # Generic network errors
    if "Connection" in str(type(error)) or "Timeout" in str(type(error)):
        return LLMError(
            "Network error connecting to LLM provider",
            severity=ErrorSeverity.WARNING,
            suggestion="Check your internet connection and provider status",
            provider=provider,
            retryable=True,
        )

    # Fallback: generic error
    return LLMError(
        f"{provider} error: {error_str[:100]}",
        severity=ErrorSeverity.ERROR,
        suggestion="Check logs for details",
        provider=provider,
        retryable=False,
    )


def handle_validation_error(
    error: Exception,
    context: Optional[str] = None,
) -> LLMError:
    """Convert validation error to user-friendly message."""
    error_str = str(error)

    if "token" in error_str.lower() or "length" in error_str.lower():
        return LLMError(
            "Input is too long to process",
            severity=ErrorSeverity.WARNING,
            suggestion="Try with fewer files or shorter context",
            retryable=False,
        )

    if "path" in error_str.lower() or "traversal" in error_str.lower():
        return LLMError(
            "Invalid file path",
            severity=ErrorSeverity.ERROR,
            suggestion="Use relative paths within your project",
            retryable=False,
        )

    return LLMError(
        f"Validation failed: {error_str}",
        severity=ErrorSeverity.ERROR,
        retryable=False,
    )


class ErrorBoundary:
    """Context manager for catching and formatting LLM errors."""

    def __init__(
        self,
        provider: Optional[str] = None,
        operation: Optional[str] = None,
        on_error: Optional[Callable[[LLMError], None]] = None,
    ):
        self.provider = provider
        self.operation = operation or "LLM operation"
        self.on_error = on_error
        self.caught_error: Optional[LLMError] = None

    def __enter__(self) -> ErrorBoundary:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val is None:
            return False  # No error

        if isinstance(exc_val, LLMError):
            self.caught_error = exc_val
        else:
            # Convert generic exception to LLMError
            if self.provider:
                self.caught_error = handle_provider_error(
                    exc_val, self.provider
                )
            else:
                self.caught_error = LLMError(
                    f"{self.operation} failed: {exc_val}",
                    severity=ErrorSeverity.ERROR,
                )

        logger.error(f"[{self.operation}] {self.caught_error.user_message()}")

        if self.on_error:
            self.on_error(self.caught_error)

        # Don't suppress the exception (log it, then let caller handle)
        return False

    async def __aenter__(self) -> ErrorBoundary:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return self.__exit__(exc_type, exc_val, exc_tb)

"""
Error Handling for Streaming

Robust error recovery during WebSocket streaming.
Auto-reconnection and graceful degradation.
"""

import logging
import asyncio
from typing import Callable, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    INFO = "info"          # Recoverable, continue
    WARNING = "warning"    # Might need retry
    ERROR = "error"        # Needs retry
    CRITICAL = "critical"  # Cannot recover


class StreamingError(Exception):
    """Base streaming error."""
    
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.ERROR):
        self.message = message
        self.severity = severity
        super().__init__(message)


class ConnectionError(StreamingError):
    """WebSocket connection error."""
    
    def __init__(self, message: str):
        super().__init__(f"Connection error: {message}", ErrorSeverity.WARNING)


class TimeoutError(StreamingError):
    """Request timeout."""
    
    def __init__(self, message: str = "Request timeout"):
        super().__init__(message, ErrorSeverity.WARNING)


class InvalidResponseError(StreamingError):
    """Invalid response format."""
    
    def __init__(self, message: str):
        super().__init__(f"Invalid response: {message}", ErrorSeverity.ERROR)


class ErrorRecoveryStrategy:
    """Handles error recovery and retry logic."""
    
    def __init__(
        self,
        max_retries: int = 3,
        retry_delay_ms: int = 1000,
        backoff_multiplier: float = 1.5,
        fallback_to_http: bool = True,
    ):
        """Initialize recovery strategy.
        
        Args:
            max_retries: Maximum retry attempts
            retry_delay_ms: Initial retry delay
            backoff_multiplier: Exponential backoff multiplier
            fallback_to_http: Fallback to HTTP if WebSocket fails
        """
        self.max_retries = max_retries
        self.retry_delay_ms = retry_delay_ms
        self.backoff_multiplier = backoff_multiplier
        self.fallback_to_http = fallback_to_http
        
        self.retry_count = 0
        self.last_error: Optional[StreamingError] = None
    
    async def retry_with_backoff(self, func: Callable, *args, **kwargs):
        """Execute function with exponential backoff retry.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result if successful
            
        Raises:
            StreamingError: If all retries failed
        """
        self.retry_count = 0
        delay_ms = self.retry_delay_ms
        
        while self.retry_count <= self.max_retries:
            try:
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                logger.info(f"Operation succeeded (retry {self.retry_count})")
                return result
            
            except StreamingError as e:
                self.last_error = e
                
                # Don't retry on CRITICAL errors
                if e.severity == ErrorSeverity.CRITICAL:
                    logger.error(f"Critical error - cannot recover: {e}")
                    raise
                
                # Check retry limit
                if self.retry_count >= self.max_retries:
                    logger.error(f"Max retries ({self.max_retries}) exceeded: {e}")
                    raise
                
                # Exponential backoff
                self.retry_count += 1
                logger.warning(f"Retry {self.retry_count}/{self.max_retries} after {delay_ms}ms: {e}")
                await asyncio.sleep(delay_ms / 1000)
                delay_ms = int(delay_ms * self.backoff_multiplier)
            
            except Exception as e:
                # Wrap unexpected errors
                self.last_error = StreamingError(str(e), ErrorSeverity.ERROR)
                
                if self.retry_count >= self.max_retries:
                    logger.error(f"Unexpected error after {self.max_retries} retries: {e}")
                    raise self.last_error
                
                self.retry_count += 1
                logger.warning(f"Retry {self.retry_count}/{self.max_retries} after error: {e}")
                await asyncio.sleep(delay_ms / 1000)
                delay_ms = int(delay_ms * self.backoff_multiplier)
    
    def should_fallback_to_http(self) -> bool:
        """Check if should fallback to HTTP.
        
        Returns:
            True if WebSocket failed and HTTP fallback enabled
        """
        return (
            self.fallback_to_http and
            self.last_error and
            isinstance(self.last_error, ConnectionError)
        )
    
    def reset(self) -> None:
        """Reset retry counter."""
        self.retry_count = 0
        self.last_error = None


class ResponseValidator:
    """Validates streaming responses."""
    
    @staticmethod
    def validate_token_event(event_data: dict) -> tuple[bool, str]:
        """Validate token event format.
        
        Args:
            event_data: Event data dict
            
        Returns:
            (is_valid, error_message)
        """
        required_fields = ["type", "content"]
        
        for field in required_fields:
            if field not in event_data:
                return False, f"Missing field: {field}"
        
        if event_data["type"] != "token":
            return False, f"Invalid event type: {event_data['type']}"
        
        if not isinstance(event_data["content"], str):
            return False, "Content must be string"
        
        return True, ""
    
    @staticmethod
    def validate_complete_event(event_data: dict) -> tuple[bool, str]:
        """Validate completion event format.
        
        Args:
            event_data: Event data dict
            
        Returns:
            (is_valid, error_message)
        """
        if event_data.get("type") != "complete":
            return False, "Invalid event type for complete"
        
        return True, ""
    
    @staticmethod
    def validate_error_event(event_data: dict) -> tuple[bool, str]:
        """Validate error event format.
        
        Args:
            event_data: Event data dict
            
        Returns:
            (is_valid, error_message)
        """
        if event_data.get("type") != "error":
            return False, "Invalid event type for error"
        
        if "message" not in event_data:
            return False, "Error must have message field"
        
        return True, ""

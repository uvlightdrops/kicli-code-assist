"""Response streaming and cancellation support for LLM operations.

Enables token-by-token streaming with user cancellation support.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import AsyncIterator, Callable, Optional

logger = logging.getLogger(__name__)


class StreamStatus(Enum):
    """Status of streaming response."""
    RUNNING = "running"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class StreamEvent:
    """Single event in token stream."""
    type: str  # "token", "status", "metric"
    content: str  # Token text or status message
    token_count: int = 0  # Cumulative token count
    timestamp: Optional[float] = None


class StreamCancellation:
    """Manages stream cancellation with grace period."""

    def __init__(self, grace_period_s: float = 2.0):
        """Initialize cancellation manager.

        Args:
            grace_period_s: Seconds to wait after cancel request before force-stop
        """
        self.cancelled = False
        self.grace_period = grace_period_s
        self._cancel_requested = asyncio.Event()
        self._force_stop = False

    def request_cancel(self) -> None:
        """Request stream cancellation (graceful)."""
        logger.info("Stream cancellation requested (graceful)")
        self.cancelled = True
        self._cancel_requested.set()

    async def should_stop(self) -> bool:
        """Check if stream should stop (either graceful or forced)."""
        if self._force_stop:
            return True

        # Check if cancel was requested and grace period passed
        if self.cancelled:
            # Give time for current token to finish
            try:
                await asyncio.wait_for(
                    asyncio.sleep(0),  # Yield immediately
                    timeout=0.1
                )
            except asyncio.TimeoutError:
                pass
            return True

        return False

    async def wait_for_cancel(self) -> None:
        """Wait until cancellation is requested."""
        await self._cancel_requested.wait()

    def force_stop(self) -> None:
        """Force immediate stop (no grace period)."""
        logger.warning("Stream force-stop")
        self._force_stop = True
        self._cancel_requested.set()


class StreamBuffer:
    """Buffers tokens and provides batched output."""

    def __init__(self, batch_size: int = 5):
        """Initialize buffer.

        Args:
            batch_size: How many tokens to buffer before flushing
        """
        self.batch_size = batch_size
        self.buffer: list[str] = []

    def add(self, token: str) -> Optional[str]:
        """Add token to buffer.

        Returns:
            Flushed tokens if buffer reaches batch size, else None
        """
        self.buffer.append(token)
        if len(self.buffer) >= self.batch_size:
            return self.flush()
        return None

    def flush(self) -> str:
        """Flush all buffered tokens."""
        result = "".join(self.buffer)
        self.buffer.clear()
        return result

    def has_buffered(self) -> bool:
        """Check if buffer has tokens."""
        return len(self.buffer) > 0


class TokenCounter:
    """Tracks token counts and estimates."""

    CHARS_PER_TOKEN = 4  # Rough estimate

    def __init__(self):
        self.actual_count = 0  # From API if available
        self.estimated_count = 0  # From character count
        self.total_chars = 0

    def add_token(self, token: str) -> None:
        """Register a token from stream."""
        self.actual_count += 1
        self.total_chars += len(token)
        self.estimated_count = self.total_chars / self.CHARS_PER_TOKEN

    def get_count(self) -> int:
        """Get current token count (prefer actual if available)."""
        return self.actual_count if self.actual_count > 0 else int(self.estimated_count)


async def stream_with_cancellation(
    stream_coro: AsyncIterator[str],
    on_token: Callable[[str], None],
    on_chunk: Optional[Callable[[str], None]] = None,
    on_status: Optional[Callable[[str], None]] = None,
) -> tuple[str, StreamStatus]:
    """Stream response tokens with cancellation support.

    Args:
        stream_coro: Async generator yielding response tokens
        on_token: Callback when single token received
        on_chunk: Callback when chunk (buffer) flushed
        on_status: Callback for status messages

    Returns:
        (full_response, final_status)
    """
    cancellation = StreamCancellation()
    buffer = StreamBuffer(batch_size=5)
    counter = TokenCounter()
    full_response = ""

    try:
        async for token in stream_coro:
            # Check for cancellation
            if await cancellation.should_stop():
                if on_status:
                    on_status("⏹️ Stream cancelled")
                logger.info("Stream cancelled by user")
                return full_response, StreamStatus.CANCELLED

            # Process token
            full_response += token
            counter.add_token(token)

            # Callback for individual token
            if on_token:
                on_token(token)

            # Check if buffer should flush
            buffered = buffer.add(token)
            if buffered and on_chunk:
                on_chunk(buffered)

            # Yield to event loop (allow cancellation to work)
            await asyncio.sleep(0)

    except asyncio.CancelledError:
        if on_status:
            on_status("❌ Stream interrupted")
        logger.error("Stream interrupted by system")
        return full_response, StreamStatus.ERROR
    except Exception as e:
        if on_status:
            on_status(f"❌ Stream error: {e}")
        logger.exception(f"Error during streaming: {e}")
        return full_response, StreamStatus.ERROR

    # Flush remaining buffered tokens
    if buffer.has_buffered():
        final_chunk = buffer.flush()
        if on_chunk:
            on_chunk(final_chunk)

    if on_status:
        token_count = counter.get_count()
        on_status(f"✓ Complete ({token_count} tokens)")

    logger.info(f"Stream completed: {len(full_response)} chars, {counter.get_count()} tokens")
    return full_response, StreamStatus.COMPLETED


class StreamDisplayFormatter:
    """Formats streamed tokens for UI display."""

    # Tokens that indicate thinking/processing
    THINKING_MARKERS = ["<think", "<reasoning", "```", "---"]

    def __init__(self):
        self.in_code_block = False
        self.code_language = ""

    def format_token(self, token: str) -> str:
        """Format token for display.

        Handles code blocks, markdown, etc.
        """
        # Track code blocks
        if "```" in token:
            self.in_code_block = not self.in_code_block
            # Extract language if present
            if not self.in_code_block and token.startswith("```"):
                self.code_language = token[3:].strip()

        # Could add syntax highlighting here later
        return token

    def format_chunk(self, chunk: str) -> str:
        """Format a chunk of tokens for display."""
        # Remove excessive whitespace at end
        return chunk.rstrip()

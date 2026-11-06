"""
Streaming Response Handler

Handles token-by-token rendering of agent responses via WebSocket.
Manages streaming state, error recovery, and connection lifecycle.
"""

import logging
import asyncio
from typing import Callable, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class StreamingState(Enum):
    """Streaming connection states."""
    IDLE = "idle"
    CONNECTING = "connecting"
    STREAMING = "streaming"
    PAUSED = "paused"
    COMPLETE = "complete"
    ERROR = "error"
    DISCONNECTED = "disconnected"


class StreamingEventType(Enum):
    """Event types during streaming."""
    TOKEN = "token"
    PARTIAL = "partial"
    COMPLETE = "complete"
    ERROR = "error"
    RECONNECT = "reconnect"
    RATE_LIMIT = "rate_limit"


@dataclass
class StreamingEvent:
    """Single streaming event."""
    event_type: StreamingEventType
    content: str = ""
    timestamp: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class StreamingStats:
    """Streaming session statistics."""
    tokens_received: int = 0
    tokens_rendered: int = 0
    bytes_received: int = 0
    start_time: datetime = None
    end_time: datetime = None
    errors: int = 0
    reconnects: int = 0
    
    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.now()
    
    @property
    def elapsed_seconds(self) -> float:
        """Calculate elapsed time in seconds."""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()
    
    @property
    def tokens_per_second(self) -> float:
        """Calculate tokens per second."""
        elapsed = self.elapsed_seconds
        if elapsed == 0:
            return 0
        return self.tokens_received / elapsed
    
    def __str__(self) -> str:
        return (
            f"Tokens: {self.tokens_received} ({self.tokens_per_second:.1f} t/s) | "
            f"Errors: {self.errors} | Reconnects: {self.reconnects}"
        )


class StreamingResponseHandler:
    """Handles streaming response rendering and state management.
    
    Features:
    - Token-by-token rendering with configurable delay
    - Error recovery and reconnection
    - Connection state tracking
    - Statistics collection
    - Backpressure handling (pause when rendering slows down)
    """
    
    def __init__(
        self,
        on_token: Optional[Callable[[str], None]] = None,
        on_complete: Optional[Callable[[StreamingStats], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
        min_token_delay_ms: int = 20,
        max_buffer_size: int = 100,
    ):
        """Initialize streaming handler.
        
        Args:
            on_token: Callback for each token received
            on_complete: Callback when streaming completes
            on_error: Callback for errors
            min_token_delay_ms: Minimum milliseconds between token renders
            max_buffer_size: Maximum buffered tokens before backpressure
        """
        self.on_token = on_token
        self.on_complete = on_complete
        self.on_error = on_error
        self.min_token_delay_ms = min_token_delay_ms
        self.max_buffer_size = max_buffer_size
        
        self.state = StreamingState.IDLE
        self.stats = StreamingStats()
        self.buffer: asyncio.Queue = asyncio.Queue(maxsize=max_buffer_size)
        self.task: Optional[asyncio.Task] = None
        self._last_render_time: float = 0
        self._cancel_event = asyncio.Event()
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # Not paused by default
        
        logger.debug(f"StreamingResponseHandler initialized")
    
    async def start_streaming(self) -> None:
        """Start processing token buffer."""
        if self.state != StreamingState.IDLE:
            logger.warning(f"Cannot start streaming: already in state {self.state}")
            return
        
        self.state = StreamingState.CONNECTING
        self.stats = StreamingStats()
        self._cancel_event.clear()
        
        self.task = asyncio.create_task(self._process_buffer())
        logger.info("Streaming started")
    
    async def add_token(self, token: str, metadata: Dict[str, Any] = None) -> bool:
        """Add a token to the streaming buffer.
        
        Args:
            token: Token string to add
            metadata: Optional metadata (token index, timing, etc.)
        
        Returns:
            True if added, False if buffer full (backpressure)
        """
        if self.state not in [StreamingState.CONNECTING, StreamingState.STREAMING]:
            logger.warning(f"Cannot add token: handler in state {self.state}")
            return False
        
        if self.state == StreamingState.CONNECTING:
            self.state = StreamingState.STREAMING
        
        self.stats.tokens_received += 1
        self.stats.bytes_received += len(token.encode('utf-8'))
        
        try:
            event = StreamingEvent(
                event_type=StreamingEventType.TOKEN,
                content=token,
                metadata=metadata or {}
            )
            self.buffer.put_nowait(event)
            logger.debug(f"Token added (buffer: {self.buffer.qsize()}/{self.max_buffer_size})")
            return True
        except asyncio.QueueFull:
            logger.warning("Token buffer full - backpressure triggered")
            self.stats.metadata = {"backpressure": True}
            return False
    
    async def add_error(self, error_msg: str) -> None:
        """Add an error event to the buffer."""
        self.stats.errors += 1
        event = StreamingEvent(
            event_type=StreamingEventType.ERROR,
            content=error_msg
        )
        try:
            self.buffer.put_nowait(event)
        except asyncio.QueueFull:
            logger.error("Cannot add error: buffer full")
    
    async def complete(self) -> None:
        """Signal completion of streaming."""
        self.state = StreamingState.COMPLETE
        self.stats.end_time = datetime.now()
        
        event = StreamingEvent(event_type=StreamingEventType.COMPLETE)
        try:
            self.buffer.put_nowait(event)
        except asyncio.QueueFull:
            pass
        
        logger.info(f"Streaming complete: {self.stats}")
    
    async def cancel(self) -> None:
        """Cancel streaming."""
        self.state = StreamingState.DISCONNECTED
        self._cancel_event.set()
        
        if self.task and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        logger.info("Streaming cancelled")
    
    async def pause(self) -> None:
        """Pause token rendering."""
        self._pause_event.clear()
        self.state = StreamingState.PAUSED
        logger.debug("Streaming paused")
    
    async def resume(self) -> None:
        """Resume token rendering."""
        self._pause_event.set()
        if self.state == StreamingState.PAUSED:
            self.state = StreamingState.STREAMING
        logger.debug("Streaming resumed")
    
    async def _process_buffer(self) -> None:
        """Process tokens from buffer and render them."""
        try:
            while not self._cancel_event.is_set():
                # Respect pause requests
                await self._pause_event.wait()
                
                # Get next event with timeout
                try:
                    event = await asyncio.wait_for(
                        self.buffer.get(),
                        timeout=0.1
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Process event
                if event.event_type == StreamingEventType.TOKEN:
                    await self._render_token(event.content)
                    self.stats.tokens_rendered += 1
                
                elif event.event_type == StreamingEventType.ERROR:
                    if self.on_error:
                        await self._call_async(self.on_error, event.content)
                
                elif event.event_type == StreamingEventType.COMPLETE:
                    self.state = StreamingState.COMPLETE
                    if self.on_complete:
                        await self._call_async(self.on_complete, self.stats)
                    break
        
        except asyncio.CancelledError:
            logger.info("Buffer processing cancelled")
        except Exception as e:
            logger.error(f"Error in buffer processing: {e}")
            self.state = StreamingState.ERROR
            if self.on_error:
                await self._call_async(self.on_error, f"Processing error: {str(e)}")
    
    async def _render_token(self, token: str) -> None:
        """Render a single token with rate limiting."""
        if not self.on_token:
            return
        
        # Rate limiting: enforce minimum delay between renders
        now = asyncio.get_event_loop().time()
        elapsed_ms = (now - self._last_render_time) * 1000
        
        if elapsed_ms < self.min_token_delay_ms:
            delay = (self.min_token_delay_ms - elapsed_ms) / 1000
            await asyncio.sleep(delay)
        
        # Call the render callback
        await self._call_async(self.on_token, token)
        self._last_render_time = asyncio.get_event_loop().time()
    
    @staticmethod
    async def _call_async(func: Callable, *args) -> Any:
        """Call function, handling both sync and async."""
        import inspect
        
        if inspect.iscoroutinefunction(func):
            return await func(*args)
        else:
            return func(*args)
    
    def is_streaming(self) -> bool:
        """Check if currently streaming."""
        return self.state == StreamingState.STREAMING
    
    def is_complete(self) -> bool:
        """Check if streaming complete."""
        return self.state == StreamingState.COMPLETE
    
    def get_stats(self) -> StreamingStats:
        """Get current streaming statistics."""
        return self.stats

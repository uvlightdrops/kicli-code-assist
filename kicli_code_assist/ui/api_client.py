"""
Backend API Client

Handles HTTP requests and WebSocket streaming to backend.
Async/await patterns for non-blocking UI.
"""

import logging
import asyncio
import json
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
import httpx
import websockets

logger = logging.getLogger(__name__)


@dataclass
class APIResponse:
    """Response from backend API."""
    success: bool
    status_code: int
    data: Dict[str, Any] = None
    error: str = None


class HTTPClient:
    """HTTP client for REST endpoints."""
    
    def __init__(self, base_url: str, timeout: int = 30, retry_count: int = 3):
        """Initialize HTTP client.
        
        Args:
            base_url: Backend base URL (e.g., http://localhost:8000)
            timeout: Request timeout in seconds
            retry_count: Number of retries on failure
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retry_count = retry_count
        self.client: Optional[httpx.AsyncClient] = None
    
    async def init(self) -> None:
        """Initialize async client."""
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
        )
    
    async def close(self) -> None:
        """Close async client."""
        if self.client:
            await self.client.aclose()
    
    async def _request(
        self,
        method: str,
        path: str,
        **kwargs
    ) -> APIResponse:
        """Execute HTTP request with retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: API endpoint path
            **kwargs: Additional arguments for httpx
            
        Returns:
            APIResponse with result or error
        """
        if not self.client:
            await self.init()
        
        url = f"{self.base_url}{path}"
        
        for attempt in range(self.retry_count):
            try:
                response = await self.client.request(method, path, **kwargs)
                
                data = None
                try:
                    data = response.json()
                except:
                    data = response.text
                
                if response.status_code < 400:
                    logger.debug(f"{method} {path} -> {response.status_code}")
                    return APIResponse(
                        success=True,
                        status_code=response.status_code,
                        data=data,
                    )
                else:
                    error = data.get("error") if isinstance(data, dict) else str(data)
                    logger.warning(f"{method} {path} -> {response.status_code}: {error}")
                    return APIResponse(
                        success=False,
                        status_code=response.status_code,
                        error=error,
                    )
            
            except httpx.TimeoutException:
                logger.warning(f"Timeout on {method} {path} (attempt {attempt + 1})")
                if attempt == self.retry_count - 1:
                    return APIResponse(
                        success=False,
                        status_code=0,
                        error="Request timeout",
                    )
            
            except Exception as e:
                logger.error(f"Request error: {e}")
                if attempt == self.retry_count - 1:
                    return APIResponse(
                        success=False,
                        status_code=0,
                        error=str(e),
                    )
            
            await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff
        
        return APIResponse(
            success=False,
            status_code=0,
            error="Max retries exceeded",
        )
    
    async def post(self, path: str, json: Dict = None, **kwargs) -> APIResponse:
        """POST request."""
        return await self._request("POST", path, json=json, **kwargs)
    
    async def get(self, path: str, **kwargs) -> APIResponse:
        """GET request."""
        return await self._request("GET", path, **kwargs)
    
    async def put(self, path: str, json: Dict = None, **kwargs) -> APIResponse:
        """PUT request."""
        return await self._request("PUT", path, json=json, **kwargs)


class WebSocketClient:
    """WebSocket client for streaming responses."""
    
    def __init__(self, ws_url: str):
        """Initialize WebSocket client.
        
        Args:
            ws_url: WebSocket URL (e.g., ws://localhost:8000/socket.io)
        """
        self.ws_url = ws_url
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.on_message: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
    
    async def connect(self) -> bool:
        """Connect to WebSocket.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.websocket = await websockets.connect(self.ws_url)
            logger.info(f"WebSocket connected: {self.ws_url}")
            return True
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            if self.on_error:
                await self._call_callback(self.on_error, str(e))
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from WebSocket."""
        if self.websocket:
            await self.websocket.close()
            logger.info("WebSocket disconnected")
    
    async def send(self, message: str) -> None:
        """Send message to WebSocket.
        
        Args:
            message: Message to send
        """
        if not self.websocket:
            logger.error("WebSocket not connected")
            return
        
        try:
            await self.websocket.send(message)
            logger.debug(f"WebSocket sent: {message[:50]}...")
        except Exception as e:
            logger.error(f"WebSocket send error: {e}")
            if self.on_error:
                await self._call_callback(self.on_error, f"Send error: {e}")
    
    async def listen(self) -> None:
        """Listen for messages (blocking).
        
        Calls on_message callback for each received message.
        """
        if not self.websocket:
            logger.error("WebSocket not connected")
            return
        
        try:
            async for message in self.websocket:
                logger.debug(f"WebSocket received: {message[:50]}...")
                if self.on_message:
                    await self._call_callback(self.on_message, message)
        except Exception as e:
            logger.error(f"WebSocket listen error: {e}")
            if self.on_error:
                await self._call_callback(self.on_error, f"Listen error: {e}")
    
    async def _call_callback(self, callback: Callable, *args) -> None:
        """Call callback safely."""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(*args)
            else:
                callback(*args)
        except Exception as e:
            logger.error(f"Callback error: {e}")
    
    def set_on_message(self, callback: Callable[[str], None]) -> None:
        """Set message callback."""
        self.on_message = callback
    
    def set_on_error(self, callback: Callable[[str], None]) -> None:
        """Set error callback."""
        self.on_error = callback


class BackendClient:
    """High-level backend client combining HTTP and WebSocket."""
    
    def __init__(self, backend_url: str, timeout: int = 30, retry_count: int = 3):
        """Initialize backend client.
        
        Args:
            backend_url: Backend base URL
            timeout: Request timeout
            retry_count: Retry count
        """
        self.backend_url = backend_url
        self.http_client = HTTPClient(backend_url, timeout, retry_count)
        
        # Auto-derive WebSocket URL
        ws_url = backend_url.replace("http://", "ws://").replace("https://", "wss://")
        self.ws_client = WebSocketClient(f"{ws_url}/socket.io")
        
        self.is_connected = False
    
    async def init(self) -> bool:
        """Initialize and connect to backend.
        
        Returns:
            True if successful
        """
        await self.http_client.init()
        
        # Test connection
        response = await self.http_client.get("/api/health")
        if response.success:
            self.is_connected = True
            logger.info("Backend connected")
            return True
        else:
            logger.error(f"Backend connection failed: {response.error}")
            return False
    
    async def close(self) -> None:
        """Close connections."""
        await self.http_client.close()
        await self.ws_client.disconnect()
    
    async def send_request(self, request_text: str, context_file: str = None) -> APIResponse:
        """Send analysis request to backend.
        
        Args:
            request_text: User request
            context_file: Optional context file path
            
        Returns:
            APIResponse with analysis result
        """
        payload = {
            "request": request_text,
        }
        
        if context_file:
            payload["context_file"] = context_file
        
        return await self.http_client.post("/api/agent/route", json=payload)
    
    async def stream_reasoning(self, callback: Callable[[str], None]) -> None:
        """Stream reasoning traces via WebSocket.
        
        Args:
            callback: Called for each event
        """
        if not await self.ws_client.connect():
            return
        
        self.ws_client.set_on_message(callback)
        await self.ws_client.listen()
    
    async def get_logs(self, lines: int = 100) -> APIResponse:
        """Get recent logs.
        
        Args:
            lines: Number of log lines
            
        Returns:
            APIResponse with log content
        """
        return await self.http_client.get(f"/api/logs/tail?lines={lines}")

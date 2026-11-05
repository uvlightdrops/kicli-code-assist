"""TUI Agent Client - HTTP + WebSocket adapter."""

import httpx
import json
import logging
from typing import AsyncGenerator, Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class TUIAgentClient:
    """
    Adapter layer: TUI → Backend API
    
    Wraps HTTP requests and WebSocket connections to provide
    async streaming for all agent modes (Explain, Suggest, Reason, etc).
    """
    
    def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.ws_url = base_url.replace("http://", "ws://").replace("https://", "wss://")
        self.timeout = timeout
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=timeout)
    
    async def health_check(self) -> bool:
        """Check if backend is available by attempting a simple request."""
        try:
            # Try root endpoint (all Flask apps have this)
            resp = await self._client.get("/", timeout=2.0)
            # Accept any non-timeout response (even 404, error messages, etc.)
            return resp.status_code < 500
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def call_agent_route(
        self,
        project_path: str,
        selected_file: Optional[str] = None,
        user_request: Optional[str] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Call /api/agent/route with streaming response.
        
        Yields (event_type, data) tuples for UI rendering.
        """
        try:
            payload = {
                "project_path": project_path,
                "selected_file": selected_file,
                "user_request": user_request or "Analyze this code",
            }
            
            logger.info(f"Calling agent_route: {payload}")
            
            async with self._client.stream(
                "POST",
                "/api/agent/route",
                json=payload,
            ) as resp:
                if resp.status_code != 200:
                    error_text = await resp.atext()
                    yield {
                        "event_type": "error",
                        "message": f"API error {resp.status_code}: {error_text}",
                    }
                    return
                
                # Stream response line-by-line (JSON-L format)
                async for line in resp.aiter_lines():
                    if line.strip():
                        try:
                            data = json.loads(line)
                            yield data
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON: {line}")
                            yield {"event_type": "raw_text", "text": line}
        
        except httpx.ConnectError as e:
            yield {
                "event_type": "error",
                "message": f"Connection failed: {e}. Is backend running on {self.base_url}?",
            }
        except Exception as e:
            logger.exception("Agent call failed")
            yield {
                "event_type": "error",
                "message": f"Request failed: {e}",
            }
    
    async def get_project_files(self, project_path: str) -> list[str]:
        """Fetch list of files in project."""
        try:
            resp = await self._client.get(
                "/api/project/files",
                params={"project_path": project_path},
            )
            resp.raise_for_status()
            return resp.json().get("files", [])
        except Exception as e:
            logger.error(f"Failed to fetch files: {e}")
            return []
    
    async def read_file(self, file_path: str) -> str:
        """Read file contents."""
        try:
            resp = await self._client.get(
                "/api/read-file",
                params={"file_path": file_path},
            )
            resp.raise_for_status()
            return resp.json().get("content", "")
        except Exception as e:
            logger.error(f"Failed to read file: {e}")
            return ""
    
    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()

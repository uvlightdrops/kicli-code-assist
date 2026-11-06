"""HTTP Client for TUI to communicate with kicli backend.

Handles:
- POST /api/agent/route for analysis requests
- Error handling & timeouts
- Response parsing to match agent_tabs.py expectations
"""

import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResponse:
    """Parsed response from /api/agent/route endpoint."""
    success: bool
    answer: str
    chunks: List[Tuple[str, str]]  # List of (type, content) tuples
    intent: str
    agents_used: List[str]
    error: Optional[str] = None


class TUIBackendClient:
    """HTTP client for TUI to query backend."""
    
    def __init__(self, base_url: str = "http://localhost:3000"):
        """Initialize client.
        
        Args:
            base_url: Backend URL (default: http://localhost:3000)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = 32  # 32 second timeout per AGENT_ROUTE_SPEC
    
    def analyze_file(
        self,
        query: str,
        file_path: str,
        project_root: str,
        scope: str = "file"
    ) -> AnalysisResponse:
        """Query backend for file analysis.
        
        Args:
            query: User's analysis request (e.g., "Explain this file")
            file_path: Path to file to analyze
            project_root: Project root directory
            scope: "file", "folder", or "project" (default: "file")
        
        Returns:
            AnalysisResponse with answer, chunks, metadata
        
        Raises:
            ConnectionError: If backend unreachable
            ValueError: If response invalid
        """
        
        payload = {
            "query": query,
            "file_path": file_path,
            "project_root": project_root,
            "scope": scope,
        }
        
        endpoint = f"{self.base_url}/api/agent/route"
        
        try:
            logger.info(f"Querying backend: {endpoint} query='{query[:50]}'")
            
            # Prepare request
            req = Request(
                endpoint,
                data=json.dumps(payload).encode('utf-8'),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            
            # Execute request with timeout
            with urlopen(req, timeout=self.timeout) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    return self._parse_response(data)
                else:
                    raise ValueError(f"Backend returned status {response.status}")
        
        except HTTPError as e:
            body = e.read().decode('utf-8')
            logger.error(f"Backend error {e.code}: {body}")
            try:
                error_data = json.loads(body)
                return AnalysisResponse(
                    success=False,
                    answer="",
                    chunks=[],
                    intent="error",
                    agents_used=[],
                    error=error_data.get("error", f"Backend error: {e.code}")
                )
            except:
                return AnalysisResponse(
                    success=False,
                    answer="",
                    chunks=[],
                    intent="error",
                    agents_used=[],
                    error=f"Backend error: {e.code}"
                )
        
        except URLError as e:
            logger.error(f"Connection error: {e}")
            return AnalysisResponse(
                success=False,
                answer="",
                chunks=[],
                intent="error",
                agents_used=[],
                error=f"Connection error: Cannot reach backend at {self.base_url}"
            )
        
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return AnalysisResponse(
                success=False,
                answer="",
                chunks=[],
                intent="error",
                agents_used=[],
                error=f"Error: {str(e)}"
            )
    
    def _parse_response(self, data: Dict[str, Any]) -> AnalysisResponse:
        """Parse backend response into AnalysisResponse.
        
        Converts agent response + tabs into chunks format expected by UI.
        
        Args:
            data: JSON response from /api/agent/route
        
        Returns:
            AnalysisResponse with formatted chunks
        """
        
        if not data.get("success"):
            return AnalysisResponse(
                success=False,
                answer="",
                chunks=[],
                intent="error",
                agents_used=[],
                error=data.get("error", "Unknown error")
            )
        
        # Main answer
        answer = data.get("answer", "")
        
        # Extract chunks from tabs (each tab can have chunks)
        chunks: List[Tuple[str, str]] = []
        
        tabs = data.get("tabs", {})
        for tab_name, tab_data in tabs.items():
            if isinstance(tab_data, dict):
                # Each tab might have a 'chunks' field
                tab_chunks = tab_data.get("chunks", [])
                for chunk in tab_chunks:
                    if isinstance(chunk, dict):
                        chunk_type = chunk.get("type", "info")
                        content = chunk.get("content", "")
                        chunks.append((chunk_type, content))
        
        # If no chunks in tabs, create one from summary
        if not chunks and tabs:
            for tab_name, tab_data in tabs.items():
                if isinstance(tab_data, dict):
                    summary = tab_data.get("summary", "")
                    if summary:
                        chunks.append(("observation", f"{tab_name}: {summary}"))
        
        intent = data.get("intent", {})
        if isinstance(intent, dict):
            intent_type = intent.get("type", "analyze")
        else:
            intent_type = str(intent)
        
        agents_used = data.get("agents_used", [])
        
        return AnalysisResponse(
            success=True,
            answer=answer,
            chunks=chunks,
            intent=intent_type,
            agents_used=agents_used,
            error=None
        )


# Global client instance
_client: Optional[TUIBackendClient] = None


def get_backend_client(base_url: str = "http://localhost:3000") -> TUIBackendClient:
    """Get or create global backend client."""
    global _client
    if _client is None:
        _client = TUIBackendClient(base_url)
    return _client


def set_backend_url(base_url: str) -> None:
    """Update backend URL for client."""
    global _client
    _client = TUIBackendClient(base_url)

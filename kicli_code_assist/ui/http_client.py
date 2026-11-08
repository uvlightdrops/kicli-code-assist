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
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize client.
        
        Args:
            base_url: Backend URL (default: http://localhost:8000)
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
        The bottom panel displays these chunks as the agent's "thinking" / reasoning.
        
        Args:
            data: JSON response from /api/agent/route
        
        Returns:
            AnalysisResponse with formatted chunks for thinking display
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
        
        # Main answer (top panel)
        answer = data.get("answer", "")
        
        # Extract chunks for thinking/reasoning display (bottom panel)
        chunks: List[Tuple[str, str]] = []
        
        # Strategy 1: Extract explicit chunks from tabs
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
        
        # Strategy 2: Extract execution_results as thinking output (Layer 2 reasoning)
        if not chunks and tabs:
            for tab_name, tab_data in tabs.items():
                if isinstance(tab_data, dict):
                    # Extract execution results (what agents did)
                    exec_results = tab_data.get("execution_results", {})
                    if isinstance(exec_results, dict):
                        for result_key, result_value in exec_results.items():
                            if isinstance(result_value, str):
                                chunks.append(("execution", result_value))
                            elif isinstance(result_value, dict):
                                # Flatten dict to readable text
                                for k, v in result_value.items():
                                    if isinstance(v, str):
                                        chunks.append(("execution", f"{k}: {v}"))
                    
                    # Extract summary as fallback
                    summary = tab_data.get("summary", "")
                    if summary and not chunks:
                        chunks.append(("observation", f"{tab_name}: {summary}"))
        
        # Strategy 3: Extract agents_used as thinking context
        agents_used = data.get("agents_used", [])
        if agents_used and not chunks:
            chunk_text = "Coordination: Agents running: " + ", ".join(agents_used)
            chunks.append(("execution", chunk_text))
        
        intent = data.get("intent", {})
        if isinstance(intent, dict):
            intent_type = intent.get("type", "analyze")
        else:
            intent_type = str(intent)
        
        return AnalysisResponse(
            success=True,
            answer=answer,
            chunks=chunks,
            intent=intent_type,
            agents_used=agents_used,
            error=None
        )

    def analyze_project(self, project_root: str) -> Optional[Dict[str, Any]]:
        """Query backend for project-wide analysis.
        
        Phase I2.1: Full project analysis with dependency graph.
        
        Args:
            project_root: Project root directory path
        
        Returns:
            JSON response from /api/projects/analyze or None on error
        """
        try:
            url = f"{self.base_url}/api/projects/analyze"
            payload = {
                "project_root": project_root,
                "depth": 3,
                "include_extensions": [".py", ".yaml", ".json"],
                "exclude_patterns": [".git", "__pycache__", ".venv"]
            }
            
            logger.info(f"Analyzing project: {project_root}")
            request = Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            
            with urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
                logger.info(f"Project analysis received: {data.get('project', {}).get('stats', {})}")
                return data
        
        except HTTPError as e:
            logger.error(f"HTTP error analyzing project: {e.code} - {e.reason}")
            return {
                "success": False,
                "error": f"HTTP error {e.code}: {e.reason}"
            }
        
        except URLError as e:
            logger.error(f"Cannot reach backend: {e.reason}")
            return {
                "success": False,
                "error": f"Connection error: {e.reason}"
            }
        
        except Exception as e:
            logger.error(f"Project analysis error: {e}")
            return {
                "success": False,
                "error": f"Error: {str(e)}"
            }

    def create_file(self, path: str, content: str, project_root: str) -> Dict[str, Any]:
        """Create new file via backend API.
        
        Args:
            path: Relative file path (e.g., 'src/new_file.py')
            content: File content
            project_root: Project root directory
        
        Returns:
            Response dict with success, path, message or error
        """
        try:
            url = f"{self.base_url}/api/files"
            payload = {
                "path": path,
                "content": content,
                "project": project_root
            }
            
            logger.info(f"Creating file: {path}")
            request = Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            
            with urlopen(request, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                logger.info(f"File created: {path}")
                return data
        
        except HTTPError as e:
            error_msg = f"HTTP error {e.code}"
            if e.code == 409:
                error_msg = "File already exists"
            logger.error(f"Error creating file: {error_msg}")
            return {"success": False, "error": error_msg}
        except Exception as e:
            logger.error(f"File create error: {e}")
            return {"success": False, "error": str(e)}

    def update_file(self, path: str, content: str, project_root: str) -> Dict[str, Any]:
        """Update existing file via backend API.
        
        Args:
            path: Relative file path (e.g., 'src/file.py')
            content: File content
            project_root: Project root directory
        
        Returns:
            Response dict with success, path, message or error
        """
        try:
            url = f"{self.base_url}/api/files/{path}"
            payload = {
                "content": content,
                "project": project_root
            }
            
            logger.info(f"Updating file: {path}")
            request = Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="PUT"
            )
            
            with urlopen(request, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                logger.info(f"File updated: {path}")
                return data
        
        except HTTPError as e:
            error_msg = f"HTTP error {e.code}"
            if e.code == 404:
                error_msg = "File not found"
            logger.error(f"Error updating file: {error_msg}")
            return {"success": False, "error": error_msg}
        except Exception as e:
            logger.error(f"File update error: {e}")
            return {"success": False, "error": str(e)}

    def understand_project(
        self,
        project_path: str,
        depth: str = "detailed"
    ) -> Dict[str, Any]:
        """Request comprehensive project understanding from backend.
        
        Args:
            project_path: Path to project directory
            depth: Analysis depth ('overview', 'detailed', 'deep')
        
        Returns:
            Response dict with synthesis_report, metrics, etc.
        """
        try:
            url = f"{self.base_url}/api/projects/understand"
            payload = {
                "project_path": project_path,
                "depth": depth,
            }
            
            request_body = json.dumps(payload).encode('utf-8')
            req = Request(url, data=request_body, headers={"Content-Type": "application/json"})
            
            logger.info(f"Understanding project: {project_path} (depth: {depth})")
            
            with urlopen(req, timeout=60) as response:
                data = json.loads(response.read().decode('utf-8'))
                logger.info(f"Project understanding complete")
                return data
        
        except HTTPError as e:
            error_msg = f"HTTP error {e.code}"
            if e.code == 404:
                error_msg = "Project not found"
            elif e.code == 400:
                error_msg = "Invalid project path"
            logger.error(f"Error understanding project: {error_msg}")
            return {"success": False, "error": error_msg}
        except Exception as e:
            logger.error(f"Project understanding error: {e}")
            return {"success": False, "error": str(e)}


# Global client instance
_client: Optional[TUIBackendClient] = None


def get_backend_client(base_url: str = "http://localhost:8000") -> TUIBackendClient:
    """Get or create global backend client."""
    global _client
    if _client is None:
        _client = TUIBackendClient(base_url)
    return _client


def set_backend_url(base_url: str) -> None:
    """Update backend URL for client."""
    global _client
    _client = TUIBackendClient(base_url)

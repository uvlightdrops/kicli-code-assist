"""
Agent Tabs Panel Widget - Phase I1

Tabbed container for agent analysis results.
Each tab = one agent type (Explain, Metrics, Refactor, Suggest, Dependencies, Reason)

Layout per tab:
- Top 50%: Agent Response (conversational result)
- Bottom 50%: Agent Chunks (streaming thinking/observations)

Features:
- Real LLM analysis via /api/agent/route (Phase I1)
- Analyze button to trigger analysis
- Rich formatted output
- Scrollable panels
- Tab navigation
- Error handling
"""

import logging
from typing import Dict, Optional, List, Callable
from pathlib import Path
from textual.widgets import TabbedContent, TabPane, Static, Button
from textual.containers import Container, Vertical, Horizontal
from textual.reactive import reactive
from textual.app import ComposeResult
from textual import work

from .agent_response import AgentTabContent
from ..mock_data import get_mock_response, get_mock_chunks
from ..http_client import get_backend_client, AnalysisResponse

logger = logging.getLogger(__name__)


class AgentTabPanel(Static):
    """Tabbed panel for agent analysis results.
    
    Each tab contains:
    - Response Panel (top): Agent's analysis/answer
    - Chunks Panel (bottom): Streaming observations/thoughts
    
    Real LLM integration: On Analyze button, queries /api/agent/route backend.
    Falls back to mock data if backend unavailable.
    """
    
    DEFAULT_CSS = """
    AgentTabPanel {
        width: 1fr;
        height: 1fr;
        border: solid $primary;
        background: $surface;
    }
    
    AgentTabPanel > Vertical {
        width: 1fr;
        height: 1fr;
        layout: vertical;
    }
    
    AgentTabPanel > Vertical > Button {
        margin: 1 2;
        width: 20;
    }
    
    AgentTabPanel > Vertical > TabbedContent {
        width: 1fr;
        height: 1fr;
    }
    
    AgentTabPanel TabbedContent {
        width: 1fr;
        height: 1fr;
    }
    
    AgentTabPanel TabbedContent > TabPane {
        width: 1fr;
        height: 1fr;
    }
    """
    
    def __init__(
        self,
        enabled_tabs: List[str] = None,
        default_tab: str = "explain",
        file_path: Optional[str] = None,
        project_root: Optional[str] = None,
        backend_url: str = "http://localhost:8000"
    ):
        """Initialize agent tabs.
        
        Args:
            enabled_tabs: List of tab names to show (default: all)
            default_tab: Default active tab (lowercase)
            file_path: Current file to analyze (optional)
            project_root: Project root directory (optional)
            backend_url: Backend URL for API calls
        """
        super().__init__()
        self.enabled_tabs = enabled_tabs or ["Explain", "Metrics", "Refactor", "Suggest", "Dependencies", "Reason"]
        self.default_tab = default_tab.lower() if default_tab else "explain"
        self.tab_contents: Dict[str, AgentTabContent] = {}
        self.tabbed_content: Optional[TabbedContent] = None
        self.file_path = file_path
        self.project_root = project_root or str(Path.cwd())
        self.backend_url = backend_url
        self.backend_client = get_backend_client(backend_url)
        self.is_analyzing = False
    
    def compose(self):
        """Compose the panel: button + tabs."""
        yield Button("Analyze", id="btn-analyze", variant="primary")
        
        # Create tabbed content with tabs as children
        with TabbedContent():
            for tab_name in self.enabled_tabs:
                tab_id = tab_name.lower()
                tab_content = AgentTabContent(tab_id)
                self.tab_contents[tab_id] = tab_content
                
                yield TabPane(tab_name, tab_content, id=f"tab-{tab_id}")
    
    def on_mount(self) -> None:
        """Setup after mount."""
        pass
    
    def set_file_context(self, file_path: str, project_root: Optional[str] = None) -> None:
        """Update file context for analysis.
        
        Args:
            file_path: Path to file to analyze
            project_root: Project root (optional, uses current if not provided)
        """
        self.file_path = file_path
        if project_root:
            self.project_root = project_root
    
    def action_analyze(self) -> None:
        """Action handler for Analyze button - trigger real API analysis."""
        if self.is_analyzing:
            logger.warning("Analysis already in progress")
            return
        
        if not self.file_path:
            logger.error("No file selected for analysis")
            self._show_error("No file selected. Please select a file first.")
            return
        
        self.is_analyzing = True
        # Trigger async analysis in background
        self._perform_analysis()
    
    @work(thread=False)
    async def _perform_analysis(self) -> None:
        """Perform async analysis and update UI."""
        try:
            logger.info(f"Starting analysis: file={self.file_path}")
            
            # Resolve paths to absolute (backend requires absolute paths)
            file_path_abs = str(Path(self.file_path).resolve())
            project_root_abs = str(Path(self.project_root).resolve())
            logger.info(f"Resolved: file={file_path_abs}, project_root={project_root_abs}")
            
            # Get active tab
            try:
                tabbed = self.query_one(TabbedContent)
                active_tab_id = tabbed.active
                agent_type = active_tab_id.replace("tab-", "").lower()
            except Exception as e:
                logger.error(f"Failed to get active tab: {e}")
                agent_type = "explain"
            
            # Build analysis query from agent type
            query = self._build_query(agent_type)
            
            # Call backend with absolute paths
            logger.info(f"Calling backend: query='{query}' file={file_path_abs}")
            response = self.backend_client.analyze_file(
                query=query,
                file_path=file_path_abs,
                project_root=project_root_abs,
                scope="file"
            )
            
            # Update UI with response
            if response.success:
                logger.info(f"Analysis succeeded: {len(response.chunks)} chunks")
                if agent_type in self.tab_contents:
                    tab_content = self.tab_contents[agent_type]
                    tab_content.set_response(response.answer)
                    tab_content.set_chunks(response.chunks)
            else:
                logger.error(f"Analysis failed: {response.error}")
                self._show_error(response.error or "Analysis failed")
        
        except Exception as e:
            logger.error(f"Error in analysis: {e}", exc_info=True)
            self._show_error(f"Error: {str(e)}")
        
        finally:
            self.is_analyzing = False
    
    def _build_query(self, agent_type: str) -> str:
        """Build analysis query from agent type.
        
        Args:
            agent_type: Type of agent (explain, metrics, refactor, etc)
        
        Returns:
            Query string for backend
        """
        file_name = Path(self.file_path).name if self.file_path else "file"
        
        queries = {
            "explain": f"Analyze and explain {file_name}. What does it do? How is it structured?",
            "metrics": f"Show code quality metrics for {file_name}. Complexity, maintainability, coverage?",
            "refactor": f"What refactoring opportunities exist in {file_name}? What could be improved?",
            "dependencies": f"Show dependencies and imports in {file_name}. Any circular dependencies?",
            "suggest": f"Suggest improvements and best practices for {file_name}.",
            "reason": f"Provide detailed reasoning about the design choices in {file_name}."
        }
        
        return queries.get(agent_type, f"Analyze {file_name}")
    
    def _show_error(self, error_msg: str) -> None:
        """Show error message in active tab."""
        try:
            tabbed = self.query_one(TabbedContent)
            active_tab_id = tabbed.active
            agent_type = active_tab_id.replace("tab-", "").lower()
            
            if agent_type in self.tab_contents:
                tab_content = self.tab_contents[agent_type]
                tab_content.set_response(f"❌ Error: {error_msg}")
                tab_content.set_chunks([("issue", error_msg)])
        except Exception as e:
            logger.error(f"Failed to show error: {e}")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "btn-analyze":
            self.action_analyze()
    
    def set_response(self, tab_id: str, text: str) -> None:
        """Set response for a tab.
        
        Args:
            tab_id: Tab identifier (lowercase, e.g., 'explain')
            text: Response text
        """
        if tab_id in self.tab_contents:
            self.tab_contents[tab_id].set_response(text)
    
    def set_chunks(self, tab_id: str, chunks_list: list) -> None:
        """Set chunks for a tab.
        
        Args:
            tab_id: Tab identifier (lowercase)
            chunks_list: List of (type, content) tuples
        """
        if tab_id in self.tab_contents:
            self.tab_contents[tab_id].set_chunks(chunks_list)
    
    def clear_tab(self, tab_id: str) -> None:
        """Clear a tab's content."""
        if tab_id in self.tab_contents:
            self.tab_contents[tab_id].clear()
    
    def clear_all_tabs(self) -> None:
        """Clear all tabs."""
        for tab_content in self.tab_contents.values():
            tab_content.clear()

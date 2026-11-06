"""
Agent Tabs Panel Widget - Phase I1

Tabbed container for agent analysis results.
Each tab = one agent type (Explain, Metrics, Refactor, Suggest, Dependencies, Reason)

Layout per tab:
- Top 50%: Agent Response (conversational result)
- Bottom 50%: Agent Chunks (streaming thinking/observations)

Features:
- Mock data for UI testing (Phase I1)
- Analyze button to trigger analysis
- Rich formatted output
- Scrollable panels
- Tab navigation
"""

import logging
from typing import Dict, Optional, List, Callable
from textual.widgets import TabbedContent, TabPane, Static, Button
from textual.containers import Container, Vertical, Horizontal
from textual.reactive import reactive
from textual.app import ComposeResult

from .agent_response import AgentTabContent
from ..mock_data import get_mock_response, get_mock_chunks

logger = logging.getLogger(__name__)


class AgentTabPanel(Static):
    """Tabbed panel for agent analysis results.
    
    Each tab contains:
    - Response Panel (top): Agent's analysis/answer
    - Chunks Panel (bottom): Streaming observations/thoughts
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
    
    def __init__(self, enabled_tabs: List[str] = None, default_tab: str = "explain"):
        """Initialize agent tabs.
        
        Args:
            enabled_tabs: List of tab names to show (default: all)
            default_tab: Default active tab (lowercase)
        """
        super().__init__()
        self.enabled_tabs = enabled_tabs or ["Explain", "Metrics", "Refactor", "Suggest", "Dependencies", "Reason"]
        self.default_tab = default_tab.lower() if default_tab else "explain"
        self.tab_contents: Dict[str, AgentTabContent] = {}
        self.tabbed_content: Optional[TabbedContent] = None
    
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
        # Button will trigger action_analyze via on_button_pressed
        pass
    
    def action_analyze(self) -> None:
        """Action handler for Analyze button."""
        logger.debug("Analyze action triggered")
        
        # Query for TabbedContent
        try:
            tabbed = self.query_one(TabbedContent)
            active_tab_id = tabbed.active
            
            # Map tab ID to agent type
            agent_type = active_tab_id.replace("tab-", "").lower()
            
            # Load mock data
            response_text = get_mock_response(agent_type)
            chunks_list = get_mock_chunks(agent_type)
            
            # Get tab content and populate
            if agent_type in self.tab_contents:
                tab_content = self.tab_contents[agent_type]
                tab_content.set_response(response_text)
                tab_content.set_chunks(chunks_list)
                logger.debug(f"Loaded mock data for tab: {agent_type}")
        except Exception as e:
            logger.error(f"Error in analyze action: {e}")
    
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

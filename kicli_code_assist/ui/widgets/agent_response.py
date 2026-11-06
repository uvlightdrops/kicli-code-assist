"""Agent Response and Chunks Display Panels

Displays agent analysis results in two sections:
- AgentResponsePanel: Conversational response/analysis result (scrollable)
- AgentChunksPanel: Streaming chunks/thinking (scrollable)
"""

import logging
from textual.widgets import Static
from textual.containers import Container, Vertical
from rich.text import Text
from rich.panel import Panel
from rich.syntax import Syntax
from rich.console import Console

logger = logging.getLogger(__name__)


class AgentResponsePanel(Static):
    """Displays agent's conversational response/analysis result."""
    
    DEFAULT_CSS = """
    AgentResponsePanel {
        width: 1fr;
        height: 1fr;
        border: solid $secondary;
        overflow: auto;
        padding: 1 2;
    }
    """
    
    def __init__(self, id: str = "agent-response"):
        super().__init__(id=id)
        self.response_text = ""
    
    def set_response(self, text: str) -> None:
        """Set and display response text."""
        self.response_text = text
        self.refresh()
    
    def clear(self) -> None:
        """Clear response."""
        self.response_text = ""
        self.refresh()
    
    def render(self) -> Text:
        """Render response as text."""
        return Text(self.response_text) if self.response_text else Text("")


class AgentChunksPanel(Static):
    """Displays streaming chunks/thinking from agent."""
    
    DEFAULT_CSS = """
    AgentChunksPanel {
        width: 1fr;
        height: 1fr;
        border: solid $secondary;
        overflow: auto;
        padding: 1 2;
    }
    """
    
    def __init__(self, id: str = "agent-chunks"):
        super().__init__(id=id)
        self.chunks = []
    
    def add_chunk(self, chunk_type: str, content: str) -> None:
        """Add a chunk to display.
        
        Args:
            chunk_type: 'observation', 'issue', 'solution', 'impact', 'info'
            content: Text content
        """
        icons = {
            "observation": "🔍",
            "issue": "⚠️ ",
            "solution": "💡",
            "impact": "✅",
            "info": "ℹ️ ",
        }
        
        icon = icons.get(chunk_type, "•")
        formatted = f"{icon} {content}"
        self.chunks.append(formatted)
    
    def set_chunks(self, chunks_list: list) -> None:
        """Set all chunks at once.
        
        Args:
            chunks_list: List of (type, content) tuples
        """
        self.chunks = []
        for chunk_type, content in chunks_list:
            self.add_chunk(chunk_type, content)
        self.refresh()
    
    def clear(self) -> None:
        """Clear all chunks."""
        self.chunks = []
        self.refresh()
    
    def render(self) -> Text:
        """Render all chunks as text."""
        if not self.chunks:
            return Text("")
        
        text = "\n\n".join(self.chunks)
        return Text(text)


class AgentTabContent(Container):
    """Container for a single agent tab.
    
    Contains:
    - AgentResponsePanel (top, 50%)
    - AgentChunksPanel (bottom, 50%)
    """
    
    DEFAULT_CSS = """
    AgentTabContent {
        width: 1fr;
        height: 1fr;
        layout: vertical;
    }
    
    AgentTabContent > AgentResponsePanel {
        height: 50%;
        width: 1fr;
    }
    
    AgentTabContent > AgentChunksPanel {
        height: 50%;
        width: 1fr;
    }
    """
    
    def __init__(self, tab_id: str):
        super().__init__(id=f"tab-content-{tab_id}")
        self.tab_id = tab_id
        self.response_panel = AgentResponsePanel(id=f"response-{tab_id}")
        self.chunks_panel = AgentChunksPanel(id=f"chunks-{tab_id}")
    
    def compose(self):
        """Compose response and chunks panels."""
        yield self.response_panel
        yield self.chunks_panel
    
    def set_response(self, text: str) -> None:
        """Set response text."""
        self.response_panel.set_response(text)
    
    def set_chunks(self, chunks_list: list) -> None:
        """Set chunks. Each item: (type, content)."""
        self.chunks_panel.set_chunks(chunks_list)
    
    def clear(self) -> None:
        """Clear both panels."""
        self.response_panel.clear()
        self.chunks_panel.clear()

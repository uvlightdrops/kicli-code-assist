"""Status bar showing real-time metrics."""

from textual.widgets import Static
from textual.containers import Container, Horizontal
from rich.text import Text
from typing import Optional


class StatusBar(Static):
    """Display real-time metrics: time, cost, tokens."""
    
    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        dock: bottom;
        background: $surface;
        color: $text;
        padding: 0 1;
    }
    
    StatusBar Static {
        width: 1fr;
        height: 100%;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.elapsed_time = 0.0
        self.token_count = 0
        self.estimated_cost = 0.0
        self.status_message = "Ready"
    
    def render(self) -> Text:
        """Render status bar."""
        status_text = self.status_message
        time_str = f"⏱ {self.elapsed_time:.1f}s"
        tokens_str = f"🔤 {self.token_count}"
        cost_str = f"💰 ${self.estimated_cost:.4f}"
        
        return Text(
            f"{status_text}  {time_str}  {tokens_str}  {cost_str}",
            style="dim white on blue",
        )
    
    def update_metrics(
        self,
        elapsed_time: Optional[float] = None,
        token_count: Optional[int] = None,
        estimated_cost: Optional[float] = None,
        status: Optional[str] = None,
    ) -> None:
        """Update displayed metrics."""
        if elapsed_time is not None:
            self.elapsed_time = elapsed_time
        if token_count is not None:
            self.token_count = token_count
        if estimated_cost is not None:
            self.estimated_cost = estimated_cost
        if status is not None:
            self.status_message = status
        
        self.refresh()

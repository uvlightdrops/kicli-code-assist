"""Main TUI application."""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from textual.app import ComposeResult, App
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static
from textual.binding import Binding

from kicli_code_assist.ui.tui_config import TUIConfig
from kicli_code_assist.ui.tui_agent_client import TUIAgentClient
from kicli_code_assist.ui.widgets.project_explorer import ProjectExplorer
from kicli_code_assist.ui.widgets.agent_output_panel import AgentOutputPanel
from kicli_code_assist.ui.widgets.input_panel import InputPanel
from kicli_code_assist.ui.widgets.status_bar import StatusBar

logger = logging.getLogger(__name__)


class CodeAssistantTUIApp(App):
    """Main TUI application for agent-driven code analysis."""
    
    CSS = """
    Screen {
        layout: grid;
        grid-size: 2 3;
        grid-columns: 25% 1fr;
        grid-rows: 1fr auto 3;
    }
    
    #project-panel {
        column-span: 1;
        row-span: 1;
    }
    
    #output-panel {
        column-span: 1;
        row-span: 1;
    }
    
    #status-bar {
        column-span: 2;
        row-span: 1;
    }
    
    #input-panel {
        column-span: 2;
        row-span: 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("h", "show_help", "Help"),
        Binding("f1", "focus_project", "Project (F1)"),
        Binding("f2", "focus_output", "Output (F2)"),
        Binding("f7", "focus_input", "Input (F7)"),
    ]
    
    TITLE = "Code Assistant TUI"
    SUB_TITLE = "Press h for help, q to quit"
    
    def __init__(self, project_path: str, config: Optional[TUIConfig] = None):
        super().__init__()
        self.project_path = Path(project_path)
        self.config = config or TUIConfig.from_env()
        self.client = TUIAgentClient(self.config.api_base_url)
        
        # UI components
        self.project_explorer: Optional[ProjectExplorer] = None
        self.output_panel: Optional[AgentOutputPanel] = None
        self.input_panel: Optional[InputPanel] = None
        self.status_bar: Optional[StatusBar] = None
        
        # State
        self.selected_file: Optional[str] = None
        self.is_processing = False
    
    def compose(self) -> ComposeResult:
        """Create main layout."""
        yield Header()
        
        with Horizontal():
            self.project_explorer = ProjectExplorer(str(self.project_path), id="project-panel")
            yield self.project_explorer
            
            self.output_panel = AgentOutputPanel(id="output-panel")
            yield self.output_panel
        
        self.status_bar = StatusBar(id="status-bar")
        yield self.status_bar
        
        self.input_panel = InputPanel(id="input-panel")
        yield self.input_panel
        
        yield Footer()
    
    async def on_mount(self) -> None:
        """Initialize on mount."""
        # Check backend health
        is_healthy = await self.client.health_check()
        
        if not is_healthy:
            self.status_bar.update_metrics(
                status=f"❌ Cannot reach backend at {self.config.api_base_url}",
            )
            if self.output_panel:
                self.output_panel.render_event({
                    "event_type": "error",
                    "message": f"Backend unreachable: {self.config.api_base_url}\n\n"
                               "Make sure the backend is running:\n"
                               "  KI_STAGE=development python -m stackenv start",
                })
        else:
            self.status_bar.update_metrics(status="✅ Ready")
    
    def on_message(self, message) -> None:
        """Handle widget messages."""
        if isinstance(message, InputPanel.RequestSubmitted):
            asyncio.create_task(self._handle_request(message.request))
        
        elif hasattr(message, "file_path"):  # ProjectExplorer.FileSelected
            self.selected_file = message.file_path
            self.status_bar.update_metrics(status=f"Selected: {Path(message.file_path).name}")
    
    async def _handle_request(self, user_request: str) -> None:
        """Process user request via agent."""
        if self.is_processing:
            return
        
        if not self.selected_file:
            if self.output_panel:
                self.output_panel.render_event({
                    "event_type": "error",
                    "message": "Please select a file first.",
                })
            return
        
        self.is_processing = True
        self.status_bar.update_metrics(status="⏳ Processing...")
        
        if self.output_panel:
            self.output_panel.clear()
        
        try:
            async for event in self.client.call_agent_route(
                project_path=str(self.project_path),
                selected_file=self.selected_file,
                user_request=user_request,
            ):
                if self.output_panel:
                    self.output_panel.render_event(event)
                
                # Update metrics if present
                if "elapsed_time" in event and self.status_bar:
                    self.status_bar.update_metrics(
                        elapsed_time=event["elapsed_time"],
                        token_count=event.get("tokens_used", 0),
                        estimated_cost=event.get("estimated_cost", 0.0),
                    )
            
            self.status_bar.update_metrics(status="✅ Complete")
        
        except Exception as e:
            logger.exception("Request failed")
            if self.output_panel:
                self.output_panel.render_event({
                    "event_type": "error",
                    "message": f"Request failed: {e}",
                })
            self.status_bar.update_metrics(status="❌ Error")
        
        finally:
            self.is_processing = False
    
    def action_focus_project(self) -> None:
        """Focus project explorer."""
        if self.project_explorer:
            self.set_focus(self.project_explorer)
    
    def action_focus_output(self) -> None:
        """Focus output panel."""
        if self.output_panel:
            self.set_focus(self.output_panel)
    
    def action_focus_input(self) -> None:
        """Focus input panel."""
        if self.input_panel:
            self.set_focus(self.input_panel)
    
    def action_show_help(self) -> None:
        """Show help message."""
        help_text = """
[bold cyan]Code Assistant TUI - Help[/bold cyan]

[yellow]Navigation:[/yellow]
  F1 - Focus project tree
  F2 - Focus output panel
  F7 - Focus input field
  Tab - Cycle focus

[yellow]Controls:[/yellow]
  1. Select file in project tree (left panel)
  2. Type request in input field (bottom)
  3. Press Enter or click Submit
  4. View results in output panel (right)

[yellow]Agent Modes:[/yellow]
  - Explain: Code explanation & documentation
  - Suggest: Improvement suggestions
  - Reason: Full reasoning trace
  - Refactor: Refactoring recommendations
  - Metrics: Code quality metrics

[yellow]Keyboard:[/yellow]
  Ctrl+Enter - Submit request
  Escape - Clear input
  q - Quit
  h - This help
        """
        if self.output_panel:
            self.output_panel.render_event({
                "event_type": "raw_text",
                "text": help_text,
            })
    
    async def action_quit(self) -> None:
        """Quit application."""
        await self.client.close()
        self.exit()


def run_tui(project_path: Optional[str] = None, config: Optional[TUIConfig] = None):
    """Launch TUI application."""
    if project_path is None:
        project_path = str(Path.cwd())
    
    app = CodeAssistantTUIApp(project_path, config)
    app.run()

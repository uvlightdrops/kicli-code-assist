"""
Main TUI Application

Textual app that serves as the main container for all UI components.
Composes file tree, agent tabs, input bar, and status bar.
"""

from pathlib import Path
import logging
import asyncio
from textual.app import ComposeResult, on, App
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static
from textual import work

from .config import ConfigLoader, TUIConfig
from .api_client import BackendClient
from .widgets.file_browser import FileTree
from .widgets.agent_tabs import AgentTabPanel
from .widgets.input_bar import InputBar, StatusBar
from .widgets.preview_panel import PreviewPanel
from .widgets.preview_modal import FilePreviewModal
from .widgets.vi_editor_modal import VIEditorModal


logger = logging.getLogger(__name__)


class KICLITUIApp(App):
    """Main KI Code Assistant TUI Application.
    
    Layout:
    ```
    ┌─────────────────────────────────────────┐
    │ Header: KI Code Assistant               │
    ├─────────────┬───────────────────────────┤
    │ File Tree   │ Agent Tabs (Explain...)  │
    │             │                           │
    │ 📁 Project  │ [Agent Response Output]  │
    │ • src/      │                           │
    │ • tests/    │                           │
    │             ├───────────────────────────┤
    │             │ Input: [user request...] │
    ├─────────────┴───────────────────────────┤
    │ Status: ✅ Ready | Backend: localhost  │
    ├─────────────────────────────────────────┤
    │ Footer: Help                            │
    └─────────────────────────────────────────┘
    ```
    """
    
    CSS = """
    Screen {
        background: $surface;
        color: $text;
    }
    
    Header {
        dock: top;
        height: 1;
        background: $primary;
        color: $text;
    }
    
    Footer {
        dock: bottom;
        height: 1;
        background: $panel;
        color: $text;
    }
    
    #main-container {
        width: 1fr;
        height: 1fr;
    }
    
    #content-area {
        width: 1fr;
        height: 1fr;
    }
    
    #left-panel {
        width: 25%;
        height: 1fr;
        border-right: solid $primary;
        layout: vertical;
    }
    
    #left-panel FileTree {
        width: 1fr;
        height: 50%;
        border-bottom: solid $primary;
        overflow: auto;
    }
    
    #left-panel PreviewPanel {
        width: 1fr;
        height: 50%;
        overflow: auto;
    }
    
    #right-panel {
        width: 75%;
        height: 1fr;
    }
    
    InputBar {
        width: 1fr;
        height: 3;
        border-top: solid $primary;
    }
    
    StatusBar {
        width: 1fr;
        height: 1;
        border-top: solid $primary;
    }
    """
    
    TITLE = "KI Code Assistant"
    SUB_TITLE = "Intelligent Terminal IDE for Code Analysis"
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
        ("ctrl+1", "tab_1", "Tab 1"),
        ("ctrl+2", "tab_2", "Tab 2"),
        ("ctrl+3", "tab_3", "Tab 3"),
        ("ctrl+4", "tab_4", "Tab 4"),
        ("ctrl+5", "tab_5", "Tab 5"),
        ("ctrl+6", "tab_6", "Tab 6"),
    ]
    
    def __init__(self, config_path: str = None):
        """Initialize TUI app with configuration."""
        super().__init__()
        self.config_loader = ConfigLoader(config_path)
        self.config = self.config_loader.config
        self.backend_client: BackendClient = None
        self.selected_file: str = None
        
        if self.config.debug:
            self.config_loader.debug_print()
    
    def compose(self) -> ComposeResult:
        """Compose main UI layout."""
        # Header
        yield Header()
        
        # Main content area
        with Vertical(id="main-container"):
            with Horizontal(id="content-area"):
                # Left panel: File tree + Preview
                if self.config_loader.is_enabled("file_tree"):
                    with Vertical(id="left-panel"):
                        yield FileTree(
                            project_root=self.config.file_tree.project_root,
                            ignore_patterns=self.config.file_tree.ignore_patterns,
                        )
                        yield PreviewPanel()  # Add preview panel below file tree
                
                # Right panel: Agent tabs
                with Vertical(id="right-panel"):
                    if self.config_loader.is_enabled("agent_tabs"):
                        yield AgentTabPanel(
                            enabled_tabs=self.config.agent_tabs.enabled_tabs,
                            default_tab=self.config.agent_tabs.default_tab,
                        )
        
        # Input bar (always visible)
        yield InputBar(multiline=True)
        
        # Status bar (always visible)
        yield StatusBar()
        
        # Footer
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize app on mount."""
        logger.info("=" * 60)
        logger.info(f"KI Code Assistant TUI started")
        logger.info(f"Backend: {self.config.backend.url}")
        logger.info(f"Enabled panels: {self.config_loader.get_enabled_panels()}")
        logger.info("=" * 60)
        
        if self.config.debug:
            self.title = f"{self.TITLE} [DEBUG]"
        
        # Initialize status bar (always present)
        try:
            status_bar = self.query_one(StatusBar)
            status_bar.set_connected(False)
        except Exception as e:
            logger.warning(f"StatusBar not found: {e}")
        
        # Initialize backend client and connect
        self.backend_client = BackendClient(self.config.backend.url)
        self._connect_backend()
        
        # Bind InputBar submit to handler (InputBar always present)
        try:
            input_bar = self.query_one(InputBar)
            input_bar.on_submit_callback = self._on_input_submit
        except Exception as e:
            logger.warning(f"InputBar not found: {e}")
        
        # Bind FileTree selection to handler (if FileTree is enabled)
        try:
            file_tree = self.query_one(FileTree, expect_type=FileTree)
            file_tree.set_on_file_selected(self._on_file_selected)
            file_tree.focus()  # Give focus to FileTree so user can interact with it
            logger.debug("FileTree focused")
        except Exception as e:
            logger.debug(f"FileTree not found or not enabled: {e}")
    
    def action_quit(self) -> None:
        """Handle quit action."""
        logger.info("Shutting down TUI")
        
        # Close backend connection
        if self.backend_client:
            asyncio.create_task(self.backend_client.close())
        
        self.exit()
    
    @work(exclusive=True)
    async def _connect_backend(self) -> None:
        """Connect to backend (background task)."""
        status_bar = self.query_one(StatusBar)
        
        try:
            connected = await self.backend_client.init()
            status_bar.set_connected(connected)
            
            if connected:
                logger.info("Backend connected successfully")
            else:
                logger.error("Failed to connect to backend")
                status_bar.set_error("Backend unavailable")
        except Exception as e:
            logger.error(f"Backend connection error: {e}")
            status_bar.set_error(f"Connection failed: {e}")
    
    @work(exclusive=True)
    async def _on_input_submit(self, user_input: str) -> None:
        """Handle user input submission with streaming."""
        if not user_input.strip():
            return
        
        status_bar = self.query_one(StatusBar)
        tabs = self.query_one(AgentTabPanel)
        
        try:
            status_bar.set_streaming(True, "starting...")
            status_bar.set_status(f"Processing: {user_input[:40]}...")
            
            # Send request to backend
            if not self.backend_client.is_connected:
                status_bar.set_error("Not connected to backend")
                return
            
            # Check if streaming is enabled in config
            if self.config.streaming.enabled:
                await self._stream_agent_response(user_input, tabs, status_bar)
            else:
                # Fallback to regular HTTP request
                response = await self.backend_client.send_request(
                    request_text=user_input,
                    context_file=self.selected_file,
                )
                
                if response.success:
                    tabs.display_response(response.data)
                    status_bar.set_status("✅ Complete")
                    logger.info(f"Response processed: {response.status_code}")
                else:
                    error_msg = response.error or "Unknown error"
                    status_bar.set_error(f"Error: {error_msg}")
                    logger.error(f"Request failed: {error_msg}")
        
        except Exception as e:
            logger.error(f"Input submission error: {e}")
            status_bar.set_error(f"Error: {e}")
        
        finally:
            status_bar.set_streaming(False)
    
    async def _stream_agent_response(self, user_input: str, tabs: 'AgentTabPanel', status_bar: 'StatusBar') -> None:
        """Stream agent response via WebSocket.
        
        Args:
            user_input: User request text
            tabs: Agent tabs widget
            status_bar: Status bar for updates
        """
        from .streaming import StreamingResponseHandler, StreamingStats
        
        # Create streaming handler
        handler = StreamingResponseHandler(
            min_token_delay_ms=self.config.streaming.min_token_delay_ms,
            max_buffer_size=self.config.streaming.max_buffer_size,
        )
        
        # Prepare tab for streaming (stream to "Explain" tab by default)
        default_tab = self.config.agent_tabs.default_tab.lower()
        token_callback = await tabs.stream_to_tab(default_tab, flush=True)
        
        # Create handlers for streaming events
        def on_token(token: str) -> None:
            """Render token to tab."""
            token_callback(token)
            
            # Update status with token count
            stats = handler.get_stats()
            if stats.tokens_received % 10 == 0:  # Update every 10 tokens
                status_bar.set_token_stats(
                    received=stats.tokens_received,
                    rate=stats.tokens_per_second
                )
        
        async def on_complete(stats: StreamingStats) -> None:
            """Handle streaming completion."""
            await tabs.complete_streaming(default_tab)
            status_bar.set_status(f"✅ Complete: {stats}")
            logger.info(f"Streaming complete: {stats}")
        
        async def on_error(error_msg: str) -> None:
            """Handle streaming error."""
            await tabs.stream_error(default_tab, error_msg)
            status_bar.set_error(f"Streaming error: {error_msg}")
            logger.error(f"Streaming error: {error_msg}")
        
        handler.on_token = on_token
        handler.on_complete = on_complete
        handler.on_error = on_error
        
        # Start streaming
        try:
            await handler.start_streaming()
            
            # Stream via WebSocket
            await self.backend_client.stream_agent_response(
                request_text=user_input,
                context_file=self.selected_file,
                on_token=handler.add_token,
                on_complete=handler.complete,
                on_error=handler.add_error,
            )
        
        except Exception as e:
            await handler.add_error(f"Streaming failed: {str(e)}")
            logger.error(f"Streaming error: {e}")
        
        finally:
            await handler.cancel()
    
    def _on_file_selected(self, file_path: str) -> None:
        """Handle file selection from tree."""
        self.selected_file = file_path
        logger.debug(f"File selected: {file_path}")
        
        # Update preview panel if available
        try:
            preview_panel = self.query_one(PreviewPanel)
            preview_panel.preview_file(file_path)
        except Exception as e:
            logger.debug(f"Could not update preview panel: {e}")
    
    def action_tab_1(self) -> None:
        """Tab 1."""
        try:
            tabs = self.query_one(AgentTabPanel)
            tabs.action_tab_1()
        except Exception:
            pass
    
    def action_tab_2(self) -> None:
        """Tab 2."""
        try:
            tabs = self.query_one(AgentTabPanel)
            tabs.action_tab_2()
        except Exception:
            pass
    
    def action_tab_3(self) -> None:
        """Tab 3."""
        try:
            tabs = self.query_one(AgentTabPanel)
            tabs.action_tab_3()
        except Exception:
            pass
    
    def action_tab_4(self) -> None:
        """Tab 4."""
        try:
            tabs = self.query_one(AgentTabPanel)
            tabs.action_tab_4()
        except Exception:
            pass
    
    def action_tab_5(self) -> None:
        """Tab 5."""
        try:
            tabs = self.query_one(AgentTabPanel)
            tabs.action_tab_5()
        except Exception:
            pass
    
    def action_tab_6(self) -> None:
        """Tab 6."""
        try:
            tabs = self.query_one(AgentTabPanel)
            tabs.action_tab_6()
        except Exception:
            pass


def run_tui(config_path: str = None) -> None:
    """Run the TUI application."""
    app = KICLITUIApp(config_path)
    app.run()


if __name__ == "__main__":
    import sys
    config_path = sys.argv[1] if len(sys.argv) > 1 else None
    run_tui(config_path)

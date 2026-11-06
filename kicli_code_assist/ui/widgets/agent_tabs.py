"""
Agent Tabs Panel Widget

Tabbed container for agent response display.
Each tab = one agent mode (Explain, Suggest, Reason, Metrics, etc.)

Features:
- Rich formatted output (code blocks, diffs, etc.)
- Token-by-token streaming display (Phase 1.2.2)
- Loading state with spinner
- Keyboard navigation (Ctrl+1-6)
- Scrollable content
- Clear tab history
"""

import logging
import asyncio
from typing import Dict, Optional, List, Callable
from textual.widgets import TabbedContent, TabPane, Static, RichLog
from textual.containers import Container, Vertical
from textual.reactive import reactive
from rich.text import Text
from rich.markdown import Markdown

logger = logging.getLogger(__name__)


class AgentTabPanel(Static):
    """Tabbed panel for agent responses.
    
    Features:
    - Multiple tabs (Explain, Suggest, Reason, Metrics, Refactor, Dependencies)
    - Rich formatted output (code blocks, diffs, etc.)
    - Loading state with spinner
    - Keyboard navigation (Ctrl+1-6)
    - Scrollable content
    - Clear tab history
    """
    
    # Observable state
    active_tab = reactive("")
    
    DEFAULT_CSS = """
    AgentTabPanel {
        width: 1fr;
        height: 1fr;
        border: solid $primary;
        background: $surface;
    }
    
    AgentTabPanel > TabbedContent {
        width: 1fr;
        height: 1fr;
    }
    
    AgentTabPanel TabbedContent > TabPane {
        width: 1fr;
        height: 1fr;
    }
    
    AgentTabPanel Tabs {
        background: $panel;
        height: 3;
    }
    
    AgentTabPanel .tab-content {
        width: 1fr;
        height: 1fr;
        overflow: auto;
    }
    
    AgentTabPanel .loading-spinner {
        align: center middle;
        content-align: center middle;
    }
    """
    
    def __init__(self, enabled_tabs: List[str] = None, default_tab: str = "explain"):
        """Initialize agent tabs.
        
        Args:
            enabled_tabs: List of enabled tab names
            default_tab: Default active tab
        """
        super().__init__()
        self.enabled_tabs = enabled_tabs or [
            "explain", "suggest", "reason", "metrics", "refactor", "dependencies"
        ]
        self.default_tab = default_tab
        self.tab_panels: Dict[str, RichLog] = {}
        self.is_loading = reactive(False)
        self.tabbed_content: Optional[TabbedContent] = None
        
        # Streaming state (Phase 1.2.2)
        self.streaming_active: bool = False
        self.current_streaming_tab: Optional[str] = None
        
        logger.info(f"AgentTabPanel initialized with tabs: {self.enabled_tabs}")
    
    def compose(self):
        """Compose tab panels."""
        # Create TabbedContent container - panes are added in on_mount
        self.tabbed_content = TabbedContent()
        yield self.tabbed_content
    
    def on_mount(self) -> None:
        """Initialize on mount."""
        # Add panes to TabbedContent after it's mounted
        tab_map = {
            "explain": ("💡 Explain", "Code explanation and analysis"),
            "suggest": ("💡 Suggest", "Improvement suggestions"),
            "reason": ("🧠 Reasoning", "Agent reasoning trace"),
            "metrics": ("📊 Metrics", "Code quality metrics"),
            "refactor": ("🔄 Refactor", "Refactoring recommendations"),
            "dependencies": ("🔗 Dependencies", "Dependency analysis"),
        }
        
        for tab_name in self.enabled_tabs:
            title, description = tab_map.get(tab_name, (tab_name, ""))
            
            # Create tab pane with RichLog
            log = RichLog(classes="tab-content")
            pane = TabPane(title, log, id=f"tab-{tab_name}")
            self.tab_panels[tab_name] = log
            self.tabbed_content.add_pane(pane)
        
        # Set active tab to default
        if self.tabbed_content and self.default_tab in self.tab_panels:
            try:
                pane_id = f"tab-{self.default_tab}"
                self.tabbed_content.active = pane_id
                self.active_tab = self.default_tab
                logger.debug(f"Default tab set: {self.default_tab}")
            except Exception as e:
                logger.warning(f"Failed to set default tab: {e}")
    
    def display_response(self, response_data, flush: bool = True) -> None:
        """Display response data from backend.
        
        Args:
            response_data: Dict with tab names as keys and content as values
                          or string to display in 'Explain' tab
            flush: Clear tabs before displaying
        """
        from textual.text import Text
        
        if flush:
            self.clear_all()
        
        # Handle string response (display in Explain tab)
        if isinstance(response_data, str):
            if "Explain" in self.tab_panels:
                self.tab_panels["Explain"].write(Text(response_data))
            return
        
        # Handle dict response (multiple tabs)
        if not isinstance(response_data, dict):
            logger.warning(f"Invalid response data type: {type(response_data)}")
            return
        
        # Display each tab's content
        for tab_name, content in response_data.items():
            if tab_name not in self.tab_panels:
                # Skip unknown tabs
                continue
            
            log = self.tab_panels[tab_name]
            
            # Handle different content types
            if isinstance(content, str):
                log.write(Text(content))
            elif isinstance(content, list):
                # Handle list of items
                for item in content:
                    if isinstance(item, str):
                        log.write(Text(item))
                        log.write(Text("\n"))
                    else:
                        log.write(Text(str(item)))
                        log.write(Text("\n"))
            else:
                log.write(Text(str(content)))
        
        logger.debug(f"Response displayed in tabs")
    
    def append_output(self, tab_name: str, content, newline: bool = True) -> None:
        """Append output to a tab.
        
        Args:
            tab_name: Tab name
            content: Content to append
            newline: Add newline after content
        """
        if tab_name not in self.tab_panels:
            logger.warning(f"Tab not found: {tab_name}")
            return
        
        log = self.tab_panels[tab_name]
        
        if isinstance(content, str):
            text = Text(content)
            if newline:
                text.append("\n")
            log.write(text)
        else:
            log.write(content)
    
    def clear_tab(self, tab_name: str) -> None:
        """Clear a specific tab.
        
        Args:
            tab_name: Tab name to clear
        """
        if tab_name not in self.tab_panels:
            logger.warning(f"Tab not found: {tab_name}")
            return
        
        self.tab_panels[tab_name].clear()
        logger.debug(f"Tab cleared: {tab_name}")
    
    def clear_all(self) -> None:
        """Clear all tabs."""
        for log in self.tab_panels.values():
            log.clear()
        logger.debug("All tabs cleared")
    
    # === STREAMING DISPLAY METHODS (Phase 1.2.2) ===
    
    async def stream_to_tab(
        self,
        tab_name: str,
        on_token: Optional[Callable[[str], None]] = None,
        flush: bool = True,
    ) -> Callable[[str], None]:
        """Start streaming response to a tab.
        
        Args:
            tab_name: Tab to stream to
            on_token: Optional callback for UI updates
            flush: Clear tab before streaming
        
        Returns:
            Callback to receive tokens (await on_token(token) for each)
        """
        if tab_name not in self.tab_panels:
            logger.warning(f"Tab not found: {tab_name}")
            return lambda x: None
        
        if flush:
            self.tab_panels[tab_name].clear()
        
        self.streaming_active = True
        self.current_streaming_tab = tab_name
        
        # Create token callback that writes to the tab
        def render_token(token: str) -> None:
            """Render token to tab's RichLog."""
            log = self.tab_panels[tab_name]
            # Write each token individually (preserves formatting)
            log.write(Text(token, no_wrap=True))
            
            # Call optional UI callback
            if on_token:
                try:
                    if asyncio.iscoroutinefunction(on_token):
                        asyncio.create_task(on_token(token))
                    else:
                        on_token(token)
                except Exception as e:
                    logger.error(f"Error in on_token callback: {e}")
        
        logger.debug(f"Streaming to tab: {tab_name}")
        return render_token
    
    async def complete_streaming(self, tab_name: str = None) -> None:
        """Signal completion of streaming.
        
        Args:
            tab_name: Tab that was being streamed to (None = current)
        """
        if tab_name is None:
            tab_name = self.current_streaming_tab
        
        if tab_name is None:
            return
        
        self.streaming_active = False
        self.current_streaming_tab = None
        
        # Add final newline
        if tab_name in self.tab_panels:
            self.tab_panels[tab_name].write(Text("\n"))
        
        logger.debug(f"Streaming complete: {tab_name}")
    
    async def stream_error(self, tab_name: str, error_msg: str) -> None:
        """Display streaming error in tab.
        
        Args:
            tab_name: Tab to display error in
            error_msg: Error message
        """
        if tab_name not in self.tab_panels:
            logger.warning(f"Tab not found: {tab_name}")
            return
        
        # Format error with red text
        error_text = Text(f"❌ Error: {error_msg}\n", style="bold red")
        self.tab_panels[tab_name].write(error_text)
        
        self.streaming_active = False
        logger.error(f"Streaming error in {tab_name}: {error_msg}")
    
    def set_loading(self, tab_name: str, loading: bool) -> None:
        """Set loading state for a tab.
        
        Args:
            tab_name: Tab name
            loading: Loading state
        """
        if tab_name not in self.tab_panels:
            return
        
        if loading:
            self.display_response(tab_name, "⏳ Processing...", flush=True)
        
        logger.debug(f"Tab {tab_name} loading: {loading}")
    
    def action_next_tab(self) -> None:
        """Switch to next tab."""
        if not self.tabbed_content:
            return
        
        tab_names = list(self.tab_panels.keys())
        if not tab_names:
            return
        
        try:
            current_idx = tab_names.index(self.active_tab)
            next_idx = (current_idx + 1) % len(tab_names)
            next_tab = tab_names[next_idx]
            self.tabbed_content.active = f"tab-{next_tab}"
            self.active_tab = next_tab
        except (ValueError, IndexError):
            pass
    
    def action_prev_tab(self) -> None:
        """Switch to previous tab."""
        if not self.tabbed_content:
            return
        
        tab_names = list(self.tab_panels.keys())
        if not tab_names:
            return
        
        try:
            current_idx = tab_names.index(self.active_tab)
            prev_idx = (current_idx - 1) % len(tab_names)
            prev_tab = tab_names[prev_idx]
            self.tabbed_content.active = f"tab-{prev_tab}"
            self.active_tab = prev_tab
        except (ValueError, IndexError):
            pass
    
    def action_tab_1(self) -> None:
        """Switch to tab 1."""
        if not self.tabbed_content:
            return
        
        tabs = list(self.tab_panels.keys())
        if len(tabs) > 0:
            self.tabbed_content.active = f"tab-{tabs[0]}"
            self.active_tab = tabs[0]
    
    def action_tab_2(self) -> None:
        """Switch to tab 2."""
        if not self.tabbed_content:
            return
        
        tabs = list(self.tab_panels.keys())
        if len(tabs) > 1:
            self.tabbed_content.active = f"tab-{tabs[1]}"
            self.active_tab = tabs[1]
    
    def action_tab_3(self) -> None:
        """Switch to tab 3."""
        if not self.tabbed_content:
            return
        
        tabs = list(self.tab_panels.keys())
        if len(tabs) > 2:
            self.tabbed_content.active = f"tab-{tabs[2]}"
            self.active_tab = tabs[2]
    
    def action_tab_4(self) -> None:
        """Switch to tab 4."""
        if not self.tabbed_content:
            return
        
        tabs = list(self.tab_panels.keys())
        if len(tabs) > 3:
            self.tabbed_content.active = f"tab-{tabs[3]}"
            self.active_tab = tabs[3]
    
    def action_tab_5(self) -> None:
        """Switch to tab 5."""
        if not self.tabbed_content:
            return
        
        tabs = list(self.tab_panels.keys())
        if len(tabs) > 4:
            self.tabbed_content.active = f"tab-{tabs[4]}"
            self.active_tab = tabs[4]
    
    def action_tab_6(self) -> None:
        """Switch to tab 6."""
        if not self.tabbed_content:
            return
        
        tabs = list(self.tab_panels.keys())
        if len(tabs) > 5:
            self.tabbed_content.active = f"tab-{tabs[5]}"
            self.active_tab = tabs[5]

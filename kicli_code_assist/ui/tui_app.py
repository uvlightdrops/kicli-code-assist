"""Terminal UI for code assistant using prompt_toolkit."""
import sys
import os
import asyncio
from typing import Optional, Callable
from dataclasses import dataclass

from prompt_toolkit.application import Application
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.containers import (
    Window, HSplit, VSplit
)
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.filters import Condition
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.widgets import TextArea

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .diff_viewer import CodeChange, DiffViewer
from .file_browser import FileBrowser
from kicli_code_assist.chat_session import ChatSession


@dataclass
class UIState:
    """State of the TUI."""
    chat_history: list[tuple[str, str]]  # (role, message)
    pending_changes: list[CodeChange]
    current_change_idx: int = 0
    selected_changes: set[int] = None
    current_file: Optional[str] = None  # Selected file path
    file_preview: str = ""  # Preview of selected file
    project_context_status: str = "❌ No context loaded"  # Project context status
    focus_area: str = "input"  # Visual mode for file nav vs chat input
    
    def __post_init__(self):
        if self.selected_changes is None:
            self.selected_changes = set()


class CodeAssistantTUI:
    """Terminal UI for code assistant with file browser and diff preview."""
    
    def __init__(self, on_message: Optional[Callable[[str], None]] = None, provider: str = None):
        """Initialize TUI.
        
        Args:
            on_message: Callback when user sends message
            provider: LLM provider (auto-detect if None)
        """
        # Load ki-core config
        from ki_core import Config
        from kicli_code_assist.examples.simple_chat import create_client
        
        self.config = Config.from_env()
        
        # Auto-detect or use specified provider
        if provider is None:
            from kicli_code_assist.cli import _detect_best_provider
            provider = _detect_best_provider()
        
        self.provider = provider
        self.client = create_client(self.config, provider)
        self.on_message = on_message
        self.state = UIState(chat_history=[], pending_changes=[])
        self.console = Console()
        self.diff_viewer = DiffViewer(self.console)
        
        # File browser
        self.file_browser = FileBrowser(os.getcwd())
        
        # Chat session with project context
        self.chat_session = ChatSession(os.getcwd())
        
        # Buffers
        # Chat buffer displays messages (we add text programmatically)
        self.chat_buffer = Buffer()
        # Input buffer is where user types
        self.input_buffer = Buffer()
        self.input_field: Optional[TextArea] = None
        self.file_buffer = Buffer()
        
        # Key bindings (will be set up after layout is created)
        self.kb = KeyBindings()
        
        # Layout - must create before setting up keybindings
        self.app = self._create_app()
        
        # Now setup keybindings (after app/layout exists)
        self._setup_keybindings()
    
    def _setup_keybindings(self):
        """Setup keyboard shortcuts."""
        
        @self.kb.add('c-c')
        def _(event):
            """Quit on Ctrl-C."""
            event.app.exit()
        
        @self.kb.add('c-l')
        def _(event):
            """Load project context with Ctrl-L."""
            self._load_project_context()
            self._redraw()
        
        @self.kb.add('escape')
        def _(event):
            """Return to input mode and focus the chat field."""
            self.state.focus_area = "input"
            event.app.layout.focus(self.input_field)
            self._redraw()

        # File browser navigation - only active when file mode is enabled
        @self.kb.add('down', filter=Condition(lambda: self.state.focus_area == "files"))
        def _(event):
            """Move down in file list."""
            self.file_browser.select_next()
            self._update_file_preview()
            self._redraw()
        
        @self.kb.add('up', filter=Condition(lambda: self.state.focus_area == "files"))
        def _(event):
            """Move up in file list."""
            self.file_browser.select_prev()
            self._update_file_preview()
            self._redraw()
        
        @self.kb.add('enter', filter=Condition(lambda: self.state.focus_area == "files"))
        def _(event):
            """Enter directory in file browser."""
            self.file_browser.enter_selected()
            self._update_file_preview()
            self._redraw()
        
        @self.kb.add('enter', filter=Condition(lambda: self.app.layout.has_focus(self.input_field)))
        def _(event):
            """Send chat message from input."""
            self._send_chat_message()
        
        @self.kb.add('l', filter=Condition(lambda: self.state.focus_area == "files"))
        def _(event):
            """Load selected file content."""
            item = self.file_browser.get_selected()
            if item and not item.is_dir:
                self.state.current_file = str(item.path)
                self._show_message(f"📄 Loaded: {item.name}")
                self._redraw()
        
        @self.kb.add('h', filter=Condition(lambda: self.state.focus_area == "files"))
        def _(event):
            """Go to home directory."""
            self.file_browser.go_home()
            self._update_file_preview()
            self._redraw()
        
        @self.kb.add('r', filter=Condition(lambda: self.state.focus_area == "files"))
        def _(event):
            """Refresh file list."""
            self.file_browser.refresh()
            self._update_file_preview()
            self._redraw()
        
        @self.kb.add('s-tab')
        def _(event):
            """Toggle between file navigation mode and input mode."""
            if self.state.focus_area == "files":
                self.state.focus_area = "input"
                event.app.layout.focus(self.input_field)
            else:
                self.state.focus_area = "files"
            self._redraw()
        
        @self.kb.add('y', filter=Condition(lambda: self.state.focus_area == "files"))
        def _(event):
            """Accept change with 'y'."""
            if self.state.pending_changes:
                idx = self.state.current_change_idx
                self.state.selected_changes.add(idx)
                self._show_message("✓ Change accepted")
                self._next_change()
        
        @self.kb.add('n', filter=Condition(lambda: self.state.focus_area == "files"))
        def _(event):
            """Reject change with 'n'."""
            if self.state.pending_changes:
                idx = self.state.current_change_idx
                self.state.selected_changes.discard(idx)
                self._show_message("✗ Change rejected")
                self._next_change()
        
        @self.kb.add('e', filter=Condition(lambda: self.state.focus_area == "files"))
        def _(event):
            """Edit change with 'e' - only if there are pending changes."""
            if self.state.pending_changes:
                # Only show message if edit mode is actually needed
                idx = self.state.current_change_idx
                self._show_message(f"✎ Editing change {idx+1}/{len(self.state.pending_changes)}")
            # Otherwise do nothing - 'e' key is ignored if no changes
        
        @self.kb.add('?')
        def _(event):
            """Show help."""
            self._show_help()
    
    def _send_chat_message(self) -> None:
        """Send message to chat and get LLM response."""
        msg = self.input_field.text.strip() if self.input_field else ""
        if not msg:
            return
        
        # Add user message to UI and session
        self.add_message("You", msg)
        self.chat_session.add_message("user", msg)
        if self.input_field:
            self.input_field.text = ""
        self._redraw()
        
        # Show loading message
        self.add_message("System", "🔄 Sending to LLM...")
        self._redraw()
        
        try:
            # Get messages for API (includes system prompt with project context)
            api_messages = self.chat_session.get_messages_for_api()
            
            # Convert to ki-core Message format
            from ki_core.core.models import Message, Role
            messages = [
                Message(
                    role=Role.SYSTEM if msg["role"] == "system" else 
                    Role.ASSISTANT if msg["role"] == "assistant" else 
                    Role.USER,
                    content=msg["content"]
                )
                for msg in api_messages
            ]
            
            # Create request
            from ki_core.core.models import ChatRequest
            request = ChatRequest(messages=messages)
            
            # Stream response
            response_text = ""
            for event in self.client.chat_stream(request):
                if event.text:
                    response_text += event.text
            
            # Add assistant message
            self.add_message("Assistant", response_text)
            self.chat_session.add_message("assistant", response_text)
            
        except Exception as e:
            self.add_message("Error", f"Failed to get response: {str(e)}")
        
        self._redraw()
    
    def _update_file_preview(self) -> None:
        """Update file preview."""
        item = self.file_browser.get_selected()
        if item and not item.is_dir:
            self.state.file_preview = self.file_browser.get_file_content_preview()
        else:
            self.state.file_preview = ""
    
    def _show_help(self) -> None:
        """Show keyboard help (display only, don't add to chat)."""
        # Help is already shown in the help_window at the bottom
        pass
    
    def _create_app(self) -> Application:
        """Create the prompt_toolkit application."""
        
        from prompt_toolkit.layout.controls import FormattedTextControl
        from prompt_toolkit.layout.containers import DynamicContainer
        
        # File browser window - use proportional sizing
        file_window = Window(
            content=FormattedTextControl(text=self._get_file_tree),
            height=None  # Dynamic height
        )
        
        # File preview window - use proportional sizing
        preview_window = Window(
            content=FormattedTextControl(text=self._get_preview_text),
            height=None  # Dynamic height
        )
        
        chat_window = Window(
            content=BufferControl(buffer=self.chat_buffer),
            height=None,  # Dynamic height
            always_hide_cursor=True  # Hide cursor in chat window
        )
        
        diff_window = Window(
            content=FormattedTextControl(text=self._get_diff_text),
            height=None  # Dynamic height
        )
        
        self.input_field = TextArea(
            multiline=False,
            wrap_lines=False,
            focus_on_click=True,
            scrollbar=False,
            height=3,
        )
        self.input_buffer = self.input_field.buffer
        
        # Context status window
        context_status_window = Window(
            content=FormattedTextControl(text=self._get_context_status_text),
            height=1
        )
        
        help_text = HTML(
            "<b>[SHIFT+TAB]</b> Toggle Mode  <b>[ESC]</b> Input  <b>[↑↓]</b> Navigate  <b>[ENTER]</b> Open/Send  "
            "<b>[L]</b> Load  <b>[H]</b> Home  <b>[R]</b> Refresh  "
            "<b>[CTRL+L]</b> Load Context  <b>[?]</b> Help  <b>[CTRL+C]</b> Quit"
        )
        
        help_window = Window(content=FormattedTextControl(text=help_text), height=1)
        
        # Title windows
        title_window = Window(
            content=FormattedTextControl(text="=== KI Code Assistant ==="),
            height=1
        )
        
        file_title = Window(
            content=FormattedTextControl(text="📂 File Browser"),
            height=1
        )
        
        preview_title = Window(
            content=FormattedTextControl(text="👁️  File Preview"),
            height=1
        )
        
        chat_title = Window(
            content=FormattedTextControl(text="💬 Chat"),
            height=1
        )
        
        input_title = Window(
            content=FormattedTextControl(text="⌨️  Input"),
            height=1
        )
        
        # Left side: File browser + preview (vertical split)
        # File browser gets more space (60%) than preview (40%)
        left_panel = HSplit([
            file_title,
            file_window,  # Proportional height
            preview_title,
            preview_window,  # Proportional height
        ])
        
        # Right side: Chat + input (vertical split)
        # Chat gets most space, input only 3 lines
        right_panel = HSplit([
            chat_title,
            chat_window,  # Proportional height - fills available space
            input_title,
            self.input_field,  # Fixed 3 lines for input
        ])
        
        # Main layout: Left and right panels (horizontal split)
        main_content = VSplit([
            left_panel,
            right_panel,
        ])
        
        root_container = HSplit([
            title_window,
            main_content,
            context_status_window,
            help_window,
        ])
        
        layout = Layout(root_container, focused_element=self.input_field)

        return Application(
            layout=layout,
            key_bindings=self.kb,
            full_screen=True
        )
    
    def _get_file_tree(self) -> str:
        """Get formatted file tree."""
        return self.file_browser.get_tree_view(max_items=20)
    
    def _get_preview_text(self) -> str:
        """Get file preview text."""
        if not self.state.file_preview:
            return "No file selected"
        
        lines = self.state.file_preview.split('\n')[:15]
        return '\n'.join(lines)
    
    def add_message(self, role: str, message: str) -> None:
        """Add message to chat history."""
        self.state.chat_history.append((role, message))
        text = f"\n{role}: {message}"
        self.chat_buffer.insert_text(text)
    
    def add_change(self, change: CodeChange) -> None:
        """Add pending code change."""
        self.state.pending_changes.append(change)
        self._redraw()
    
    def _next_change(self) -> None:
        """Move to next change."""
        if self.state.pending_changes:
            self.state.current_change_idx = (
                self.state.current_change_idx + 1
            ) % len(self.state.pending_changes)
            self._redraw()
    
    def _redraw(self) -> None:
        """Redraw the diff window."""
        self.app.invalidate()
    
    def _get_diff_text(self) -> str:
        """Get current diff as formatted text."""
        if not self.state.pending_changes:
            return "No pending changes"
        
        change = self.state.pending_changes[self.state.current_change_idx]
        lines = change.get_diff_lines()
        
        result = []
        result.append(f"File: {change.filepath}")
        result.append("-" * 60)
        result.extend(lines[:50])  # Limit to 50 lines
        
        return "\n".join(result)
    
    def _show_message(self, msg: str) -> None:
        """Show temporary message."""
        self.add_message("System", msg)
    
    def _load_project_context(self) -> None:
        """Load project context for chat."""
        try:
            self._show_message("📊 Scanning project...")
            self.chat_session.load_project_context()
            status = self.chat_session.get_context_status()
            self.state.project_context_status = status
            self._show_message(f"✅ {status}")
        except Exception as e:
            self.state.project_context_status = f"❌ Error: {str(e)}"
            self._show_message(f"❌ Failed to load context: {str(e)}")
    
    def _get_context_status_text(self) -> str:
        """Get status bar text with focus indicator."""
        focus_char = "B" if self.state.focus_area == "files" else "I"
        return f"Curr-focus: {focus_char}  |  {self.state.project_context_status}"
    
    def run(self) -> None:
        """Run the TUI."""
        self.app.run()
    
    def get_accepted_changes(self) -> list[CodeChange]:
        """Get changes that were accepted."""
        return [
            change
            for i, change in enumerate(self.state.pending_changes)
            if i in self.state.selected_changes
        ]

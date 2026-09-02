"""Modern TUI for code assistant using Textual."""

import os
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Header, Footer, Static, Input, RichLog
from textual.binding import Binding
from textual.reactive import reactive
from textual.message import Message

from kicli_code_assist.chat_session import ChatSession


class FocusAwareInput(Input):
    """Input widget that handles ENTER submission properly."""
    
    def __init__(self, parent_app=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent_app = parent_app
    
    def on_key(self, event) -> None:
        """Handle ENTER key to trigger submission."""
        from textual.keys import Keys
        
        # When ENTER is pressed, submit the input
        if event.key == Keys.Enter:
            # Only trigger if we have a parent app in input focus
            if self.parent_app and self.parent_app.current_focus == "input":
                self.parent_app.action_select_cursor()
                event.prevent_default()
        else:
            # Let Input handle other keys normally
            super()._on_key(event) if hasattr(super(), '_on_key') else None


class SelectableFileList(Static):
    """Navigable file list for current directory."""
    
    def __init__(self, parent_app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent_app = parent_app
        self.current_dir = Path(os.getcwd())
        self.entries = []  # (path, is_dir)
        self.selected_index = 0
        self.load_directory()
    
    def load_directory(self):
        """Load entries for current directory."""
        self.entries = []
        try:
            # Add parent directory entry
            if self.current_dir != self.current_dir.parent:
                self.entries.append((self.current_dir.parent, True, ".."))
            
            # Add files and directories
            for item in sorted(self.current_dir.iterdir()):
                if item.name.startswith('.'):
                    continue
                is_dir = item.is_dir()
                icon = "📁" if is_dir else "📄"
                self.entries.append((item, is_dir, f"{icon} {item.name}"))
        except Exception as e:
            self.entries = [(None, False, f"Error: {e}")]
        
        self.selected_index = 0
        self.update_display()
    
    def update_display(self):
        """Update the file list display."""
        lines = []
        for i, (path, is_dir, display) in enumerate(self.entries):
            marker = ">" if i == self.selected_index else " "
            lines.append(f"{marker} {display}")
        
        self.update("\n".join(lines))
    
    def action_cursor_down(self):
        """Move cursor down."""
        if self.selected_index < len(self.entries) - 1:
            self.selected_index += 1
            self.update_display()
            self._update_preview()
    
    def action_cursor_up(self):
        """Move cursor up."""
        if self.selected_index > 0:
            self.selected_index -= 1
            self.update_display()
            self._update_preview()
    
    def action_select_cursor(self):
        """Enter directory or select file."""
        if not self.entries:
            return
        
        path, is_dir, _ = self.entries[self.selected_index]
        if is_dir:
            self.current_dir = path
            self.load_directory()
        else:
            self.parent_app.update_file_preview(path)
    
    def _update_preview(self):
        """Update preview for current selection."""
        if not self.entries:
            return
        path, is_dir, _ = self.entries[self.selected_index]
        if not is_dir and path:
            self.parent_app.update_file_preview(path)
            self.parent_app.selected_file = str(path)
    
    def get_selected_file(self):
        """Get currently selected file."""
        if not self.entries:
            return None
        path, is_dir, _ = self.entries[self.selected_index]
        return str(path) if not is_dir and path else None


class CodeAssistantApp(Static):
    """Code assistant with file browser and chat."""
    
    # Reactive state
    current_focus = reactive("browser")  # "browser" or "input"
    project_loaded = reactive(False)
    
    BINDINGS = [
        Binding("tab", "focus_next", "Focus Next", show=True),
        Binding("shift+tab", "focus_previous", "Focus Previous", show=True),
        Binding("up", "cursor_up", "Up", show=False),
        Binding("down", "cursor_down", "Down", show=False),
        Binding("ctrl+l", "load_context", "Load Context", show=True),
        Binding("l", "load_file", "Load File to Context", show=True),
        Binding("q", "app_quit", "Quit", show=True),
    ]
    
    def __init__(self):
        super().__init__()
        self.chat_session = ChatSession(os.getcwd())
        self.file_list = None
        self.preview_display = None
        self.chat_display = None
        self.input_field = None
        self.status_bar = None
        self.selected_file = None
        
        # Load ki-core config and LLM client
        from ki_core import Config
        from kicli_code_assist.examples.simple_chat import create_client
        
        self.config = Config.from_env()
        from kicli_code_assist.cli import _detect_best_provider
        provider = _detect_best_provider()
        self.client = create_client(self.config, provider)
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        # Title
        yield Static("🤖 KI Code Assistant", classes="title")
        
        # Main content area
        with Horizontal(id="main_container"):
            # Left: File list + preview
            with Vertical(id="left_panel", classes="panel"):
                yield Static("📂 File List", classes="panel_title")
                self.file_list = SelectableFileList(self, id="file_list_display", classes="preview")
                yield self.file_list
                yield Static("👁️  File Preview", classes="panel_title")
                # Use static widget for preview
                self.preview_display = Static("No file selected", classes="preview")
                yield self.preview_display
        
            # Right: Chat area
            with Vertical(id="right_panel", classes="panel"):
                yield Static("💬 Chat", classes="panel_title")
                self.chat_display = RichLog(highlight=False, markup=True)
                yield self.chat_display
        
        # Input area
        yield Static("⌨️  Input", classes="input_title")
        self.input_field = FocusAwareInput(self, id="chat_input")
        yield self.input_field
        
        # Status bar
        self.status_bar = Static("Curr-focus: B  |  ❌ No context loaded", classes="status_bar")
        yield self.status_bar
    
    def on_mount(self) -> None:
        """Setup after mount."""
        self.file_list.focus()  # Start with browser focus, not input
        # Defer preview initialization until rendering is complete
        self.app.call_later(self._init_preview_async)
    
    def _init_preview_async(self) -> None:
        """Initialize preview after rendering."""
        self.chat_display.write("Welcome to KI Code Assistant!\n")
        self.chat_display.write("Use UP/DOWN to navigate files, ENTER to select, TAB to switch focus.\n")
    
    def action_focus_next(self) -> None:
        """Focus next widget (TAB)."""
        if self.current_focus == "browser":
            self.current_focus = "input"
            self.input_field.focus()
        else:
            self.current_focus = "browser"
            self.file_list.focus()
    
    def _on_key(self, event) -> None:
        """Handle ENTER key at app level for browser mode."""
        from textual.events import Key
        
        # ENTER in browser mode selects file
        if event.key == "enter" and self.current_focus == "browser":
            self.action_select_cursor()
            event.prevent_default()
    
    def action_focus_previous(self) -> None:
        """Focus previous widget (Shift+TAB)."""
        if self.current_focus == "input":
            self.current_focus = "browser"
            self.file_list.focus()
        else:
            self.current_focus = "input"
            self.input_field.focus()
    
    def action_cursor_up(self) -> None:
        """Move cursor up in file list (browser mode only)."""
        if self.current_focus == "browser" and self.file_list:
            self.file_list.action_cursor_up()
    
    def action_cursor_down(self) -> None:
        """Move cursor down in file list (browser mode only)."""
        if self.current_focus == "browser" and self.file_list:
            self.file_list.action_cursor_down()
    
    def action_select_cursor(self) -> None:
        """Select item in file list (browser mode) or submit (input mode)."""
        if self.current_focus == "browser" and self.file_list:
            self.file_list.action_select_cursor()
        elif self.current_focus == "input":
            # Manually handle input submission
            msg = self.input_field.value.strip()
            if msg:
                self.on_input_submitted_manual(msg)
    
    def action_app_quit(self) -> None:
        """Quit the application (Q key)."""
        self.app.exit()
    
    def action_load_file(self) -> None:
        """Load selected file to context (L key)."""
        if self.file_list:
            file_path = self.file_list.get_selected_file()
            if file_path:
                self.chat_display.write(f"\n[bold cyan]📄 Added to context:[/] {file_path}")
                self.selected_file = file_path
            else:
                self.chat_display.write("\n[bold yellow]⚠️  No file selected[/]")
    
    def action_load_context(self) -> None:
        """Load project context (Ctrl+L)."""
        self.chat_display.write("[bold cyan]📊 Scanning project...[/]")
        try:
            self.chat_session.load_project_context()
            status = self.chat_session.get_context_status()
            self.chat_display.write(f"[bold green]✅ {status}[/]")
            self.project_loaded = True
        except Exception as e:
            self.chat_display.write(f"[bold red]❌ Error: {str(e)}[/]")
    
    def watch_current_focus(self, focus: str) -> None:
        """Update status when focus changes."""
        focus_char = "B" if focus == "browser" else "I"
        if self.status_bar:
            ctx_status = self.chat_session.get_context_status() if self.project_loaded else "❌ No context"
            self.status_bar.update(f"Curr-focus: {focus_char}  |  {ctx_status}")
    
    def on_input_submitted(self, event) -> None:
        """Handle message submission from Input widget."""
        if self.current_focus != "input":
            return
        
        msg = event.value.strip()
        if not msg:
            return
        
        self.on_input_submitted_manual(msg)
    
    def on_input_submitted_manual(self, msg: str) -> None:
        """Handle input submission (used by both event and action_select_cursor)."""
        self.input_field.value = ""
        
        # Add user message to chat
        self.chat_display.write(f"\n[bold cyan]You:[/] {msg}")
        self.chat_session.add_message("user", msg)
        
        # Show loading - NOW send async task
        self.chat_display.write("\n[bold yellow]⏳ Waiting for LLM response...[/]")
        self.app.call_later(self._send_to_llm_async, msg)
    
    async def _send_to_llm_async(self, msg: str) -> None:
        """Send message to LLM asynchronously (non-blocking)."""
        try:
            # Get messages for API
            api_messages = self.chat_session.get_messages_for_api()
            
            # Convert to ki-core Message format
            from ki_core.core.models import Message, Role, ChatRequest
            messages = [
                Message(
                    role=Role.SYSTEM if msg["role"] == "system" else 
                    Role.ASSISTANT if msg["role"] == "assistant" else 
                    Role.USER,
                    content=msg["content"]
                )
                for msg in api_messages
            ]
            
            # Create request and stream response
            request = ChatRequest(messages=messages)
            response_text = ""
            
            self.chat_display.write("\n[bold green]Assistant:[/]\n")
            # Build response as single text to avoid line wrapping per word
            for event in self.client.chat_stream(request):
                if event.text:
                    response_text += event.text
            
            # Write full response as one piece
            self.chat_display.write(response_text)
            self.chat_display.write("\n")
            
            # Add to session
            self.chat_session.add_message("assistant", response_text)
        
        except Exception as e:
            self.chat_display.write(f"[bold red]Error: {str(e)}[/]")
    
    def update_file_preview(self, path: Path) -> None:
        """Update file preview when file is selected."""
        try:
            if path.is_file() and path.suffix not in ['.pyc', '.o']:
                # Read first 30 lines
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()[:30]
                
                # Format preview text - NO MARKUP for Static widgets
                preview_lines = [f"{path.name}"]
                preview_lines.append("─" * 60)
                for i, line in enumerate(lines, 1):
                    preview_lines.append(f"{i:3} {line.rstrip()}")
                
                if len(lines) == 30:
                    preview_lines.append("... (truncated)")
                
                # Update static widget
                self.preview_display.update("\n".join(preview_lines))
        except Exception as e:
            self.preview_display.update(f"Error reading file: {str(e)}")
    
    def show_fallback_preview(self):
        """Show first Python file as fallback."""
        try:
            # Find first .py file
            for path in sorted(Path(os.getcwd()).rglob('*.py')):
                if any(part.startswith('.') for part in path.relative_to(os.getcwd()).parts):
                    continue
                if 'venv' in path.parts or '__pycache__' in path.parts:
                    continue
                self.update_file_preview(path)
                return
        except Exception as e:
            # Silently fail
            pass


def main():
    """Run the application."""
    from textual.app import App
    
    class CodeAssistantMain(App):
        CSS = """
        Screen {
            layout: vertical;
        }
        
        .title {
            width: 100%;
            height: 1;
            content-align: center middle;
            background: $accent;
            color: $text;
            text-style: bold;
        }
        
        #main_container {
            height: 1fr;
        }
        
        #left_panel {
            width: 1fr;
            height: 1fr;
            border: heavy $primary;
            overflow: hidden;
        }
        
        #right_panel {
            width: 1fr;
            height: 1fr;
            border: heavy $primary;
            overflow: hidden;
        }
        
        .panel_title {
            width: 100%;
            height: 1;
            background: $boost;
            text-style: bold;
        }
        
        ListView {
            width: 100%;
            height: 1fr;
            border: none;
        }
        
        .preview {
            width: 100%;
            height: auto;
            border: none;
            background: $panel;
            padding: 1;
            overflow: auto;
        }
        
        RichLog {
            width: 100%;
            height: 1fr;
            overflow: hidden;
            overflow-x: hidden;
            text-wrap: wrap;
        }
        
        #chat_input {
            width: 100%;
            height: 3;
            border: solid $primary;
        }
        
        .input_title {
            width: 100%;
            height: 1;
            background: $boost;
            text-style: bold;
        }
        
        .status_bar {
            width: 100%;
            height: 1;
            background: $panel;
        }
        """
        
        BINDINGS = [
            ("ctrl+c", "quit", "Quit"),
        ]
        
        def compose(self) -> ComposeResult:
            yield Header()
            yield CodeAssistantApp()
            yield Footer()
    
    app = CodeAssistantMain()
    app.run()


if __name__ == "__main__":
    main()

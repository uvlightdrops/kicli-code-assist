"""Modern TUI for code assistant using Textual."""

import os
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Header, Footer, Static, Input, RichLog
from textual.binding import Binding
from textual.reactive import reactive
from textual.message import Message
from textual.worker import Worker, WorkerState
import threading
import textwrap

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
    current_focus = reactive("browser")  # "browser", "chat", or "input"
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
        self.loaded_files = []  # Track files added to context via L key
        self.waiting_for_response = False  # Track if waiting for LLM
        self.spinner_index = 0  # For spinner animation
        self.llm_worker = None  # Track worker thread
        
        # Load ki-core config and LLM client
        from ki_core import Config
        from kicli_code_assist.examples.simple_chat import create_client
        
        self.config = Config.from_env()
        from kicli_code_assist.cli import _detect_best_provider
        provider = _detect_best_provider()
        self.client = create_client(self.config, provider)
    
    def _wrap_text(self, text: str, width: int = 80) -> str:
        """Wrap text to fit terminal width."""
        # Remove existing newlines and wrap
        lines = []
        for line in text.split('\n'):
            if len(line) > width:
                # Use textwrap to break long lines
                wrapped = textwrap.fill(line, width=width)
                lines.append(wrapped)
            else:
                lines.append(line)
        return '\n'.join(lines)
    
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
        # Blur input field first, then focus file list
        self.input_field.blur()
        self.file_list.focus()
        # Defer preview initialization until rendering is complete
        self.app.call_later(self._init_preview_async)
    
    def _init_preview_async(self) -> None:
        """Initialize preview after rendering."""
        self.chat_display.write("Welcome to KI Code Assistant!\nTAB: Browser (B) → Chat (C) → Input (I), UP/DOWN to navigate/scroll, L to load files.\n")
    
    def action_focus_next(self) -> None:
        """Focus next widget (TAB) - cycle: browser → chat → input → browser."""
        if self.current_focus == "browser":
            self.current_focus = "chat"
        elif self.current_focus == "chat":
            self.current_focus = "input"
        else:  # input
            self.current_focus = "browser"
        # watch_current_focus will be called automatically
    
    def _on_key(self, event) -> None:
        """Handle ENTER key at app level for browser mode."""
        from textual.events import Key
        
        # ENTER in browser mode selects file
        if event.key == "enter" and self.current_focus == "browser":
            self.action_select_cursor()
            event.prevent_default()
    
    def action_focus_previous(self) -> None:
        """Focus previous widget (Shift+TAB) - cycle: browser ← chat ← input ← browser."""
        if self.current_focus == "input":
            self.current_focus = "chat"
        elif self.current_focus == "chat":
            self.current_focus = "browser"
        else:  # browser
            self.current_focus = "input"
            # watch_current_focus will be called automatically
    
    def action_cursor_up(self) -> None:
        """Move cursor up in file list (browser) or scroll chat (chat mode)."""
        if self.current_focus == "browser" and self.file_list:
            self.file_list.action_cursor_up()
        elif self.current_focus == "chat" and self.chat_display:
            # Scroll chat up
            self.chat_display.scroll_up()
    
    def action_cursor_down(self) -> None:
        """Move cursor down in file list (browser) or scroll chat (chat mode)."""
        if self.current_focus == "browser" and self.file_list:
            self.file_list.action_cursor_down()
        elif self.current_focus == "chat" and self.chat_display:
            # Scroll chat down
            self.chat_display.scroll_down()
    
    def action_select_cursor(self) -> None:
        """Select item in file list (browser) or submit (input mode)."""
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
        if not self.file_list:
            return
        
        file_path = self.file_list.get_selected_file()
        if not file_path:
            self.chat_display.write("[bold yellow]⚠️  No file selected[/]\n")
            return
        
        # Try to read file content
        try:
            path_obj = Path(file_path)
            if path_obj.is_file():
                with open(path_obj, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Limit to first 10KB to avoid huge contexts
                if len(content) > 10000:
                    content = content[:10000] + "\n... [truncated]"
                
                # Store file in loaded files
                self.loaded_files.append({
                    "path": str(file_path),
                    "content": content
                })
                
                file_size = len(content)
                self.chat_display.write(f"[bold cyan]📄 Added to context:[/] {file_path} ({file_size} bytes)\n")
                self.selected_file = str(file_path)
            else:
                self.chat_display.write(f"[bold yellow]⚠️  Not a file: {file_path}[/]\n")
        except Exception as e:
            self.chat_display.write(f"[bold red]❌ Error reading file: {str(e)}[/]\n")
    
    def action_load_context(self) -> None:
        """Load project context (Ctrl+L)."""
        self.chat_display.write("[bold cyan]📊 Scanning project...[/] ")
        try:
            self.chat_session.load_project_context()
            status = self.chat_session.get_context_status()
            self.chat_display.write(f"[bold green]✅ {status}[/]\n")
            self.project_loaded = True
        except Exception as e:
            self.chat_display.write(f"[bold red]❌ Error: {str(e)}[/]\n")
    
    def watch_current_focus(self, focus: str) -> None:
        """Update UI when focus changes."""
        if focus == "input":
            self.input_field.focus()
            self.input_field.disabled = False
        elif focus == "chat":
            # Chat mode: give focus to chat display for scrolling
            self.input_field.blur()
            self.input_field.disabled = True
            self.chat_display.focus()
        else:  # browser
            # Browser mode: blur input and disable it
            self.input_field.blur()
            self.input_field.disabled = True
            self.file_list.focus()
        
        # Update status bar with current focus indicator
        focus_char = "B" if focus == "browser" else "C" if focus == "chat" else "I"
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
        
        # Add user message to chat with text wrapping
        wrapped_msg = self._wrap_text(msg, width=76)
        self.chat_display.write(f"[bold cyan]You:[/] {wrapped_msg}\n")
        self.chat_session.add_message("user", msg)
        
        # Mark that we're waiting for response
        self.waiting_for_response = True
        self.spinner_index = 0
        
        # Show processing message with spinner
        spinners = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        spinner = spinners[self.spinner_index % len(spinners)]
        self.chat_display.write(f"[bold yellow]{spinner} Processing...[/]\n")
        
        # Run LLM call in background worker thread (non-blocking UI)
        self.llm_worker = self.run_worker(self._send_to_llm_worker, thread=True)
    
    def _send_to_llm_worker(self) -> None:
        """Send message to LLM in background thread (non-blocking)."""
        try:
            # Build context with loaded files
            context_text = ""
            if self.loaded_files:
                context_text += "\n\n📁 Loaded Files:\n"
                for file_info in self.loaded_files:
                    context_text += f"\n--- File: {file_info['path']} ---\n"
                    context_text += file_info['content']
                    context_text += "\n---\n"
            
            # Get messages for API
            api_messages = self.chat_session.get_messages_for_api()
            
            # Inject loaded files into system message if present
            if api_messages and api_messages[0]["role"] == "system" and context_text:
                api_messages[0]["content"] += context_text
            
            # Convert to ki-core Message format
            from ki_core.core.models import Message, Role, ChatRequest
            messages = [
                Message(
                    role=Role.SYSTEM if m["role"] == "system" else 
                    Role.ASSISTANT if m["role"] == "assistant" else 
                    Role.USER,
                    content=m["content"]
                )
                for m in api_messages
            ]
            
            # Create request
            request = ChatRequest(messages=messages)
            response_text = ""
            
            # Mark that response is arriving (clear waiting state)
            self.waiting_for_response = False
            
            # Show that assistant is responding
            self.chat_display.write("[bold green]Assistant:[/] ")
            
            # Stream response chunks and display as they arrive
            for event in self.client.chat_stream(request):
                if event.text:
                    response_text += event.text
            
            # Write full response with text wrapping
            wrapped_response = self._wrap_text(response_text, width=76)
            self.chat_display.write(wrapped_response + "\n")
            
            # Add to session history
            self.chat_session.add_message("assistant", response_text)
        
        except Exception as e:
            self.waiting_for_response = False
            self.chat_display.write(f"[bold red]❌ Error: {str(e)}[/]\n")
    
    
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
            overflow: auto;
            overflow-x: auto;
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

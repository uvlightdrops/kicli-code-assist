"""Modern TUI for code assistant using Textual."""

import os
import asyncio
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Header, Footer, Static, RichLog, TextArea, TabbedContent, TabPane
from textual.binding import Binding
from textual.reactive import reactive
from textual.message import Message
from textual.worker import Worker, WorkerState
from textual.screen import ModalScreen
import threading
import textwrap

from kicli_code_assist.chat_session import ChatSession
from kicli_code_assist.prompts import PromptManager
from kicli_code_assist.ui.prompts_panel import PromptsPanel
from kicli_code_assist.ui.shell_executor_integration import ShellExecutorIntegration
from kicli_code_assist.ui.shell_approval_widget import ShellCommandApprovalModal
from kicli_code_assist.ui.command_editing_workflow import CommandEditingWorkflow
from kicli_code_assist.ui.terminal_panel import TerminalPanel
from kicli_code_assist.ui.edit_tab import EditTab
from kicli_code_assist.executor.shell_execution import ShellCommandBatch


class PromptsModal(ModalScreen):
    """Modal dialog for prompt management."""
    
    CSS = """
    PromptsModal {
        align: center middle;
        background: $surface 50%;
    }
    
    PromptsModal PromptsPanel {
        width: 100;
        height: 40;
        border: solid $primary;
        background: $surface;
        padding: 1;
    }
    """
    
    BINDINGS = [
        Binding("escape", "close_modal", "Close", show=True),
    ]
    
    def __init__(self, prompt_manager: PromptManager):
        super().__init__()
        self.prompt_manager = prompt_manager
        self.prompts_panel = None
    
    def compose(self) -> ComposeResult:
        """Create modal content - direct panel without containers."""
        self.prompts_panel = PromptsPanel(self.prompt_manager)
        yield self.prompts_panel
    
    def on_mount(self) -> None:
        """Focus the prompts panel on mount after render."""
        self.call_after_refresh(self._ensure_focus)
    
    def _ensure_focus(self) -> None:
        """Ensure prompts panel has focus."""
        if self.prompts_panel:
            # Try to focus on the first child widget (RoleSelector)
            for child in self.prompts_panel.children:
                if child.can_focus:
                    child.focus()
                    return
            # Fallback to panel itself
            if self.prompts_panel.can_focus:
                self.prompts_panel.focus()
    
    def action_close_modal(self) -> None:
        """Close the modal."""
        self.app.pop_screen()


class SelectableFileList(Static):
    """Navigable file list for current directory."""

    can_focus = True
    
    def __init__(self, parent_app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent_app = parent_app
        self.current_dir = self.parent_app.get_allowed_base_path()
        self.entries = []  # (path, is_dir)
        self.selected_index = 0
        self.load_directory()
    
    def _is_in_allowed_root(self, path: Path) -> bool:
        """Return True when path stays within the configured workspace root."""
        return self.parent_app.is_path_allowed(path)
    
    def load_directory(self):
        """Load entries for current directory."""
        allowed_root = self.parent_app.get_allowed_base_path()
        if not self.current_dir or not self._is_in_allowed_root(self.current_dir):
            self.current_dir = allowed_root
        self.entries = []
        try:
            # Add parent directory entry only while still inside the allowed base root.
            parent_dir = self.current_dir.parent
            if self.current_dir != allowed_root and self._is_in_allowed_root(parent_dir):
                self.entries.append((parent_dir, True, ".."))
            
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
            if path and self.parent_app.is_path_allowed(path):
                self.current_dir = path
                self.load_directory()
            elif path and path.name == "..":
                base_dir = self.parent_app.get_allowed_base_path()
                if self.current_dir != base_dir:
                    self.current_dir = self.current_dir.parent
                    if not self.parent_app.is_path_allowed(self.current_dir):
                        self.current_dir = base_dir
                    self.load_directory()
        else:
            if path and self.parent_app.is_path_allowed(path):
                self.parent_app.update_file_preview(path)
    
    def _update_preview(self):
        """Update preview for current selection."""
        if not self.entries:
            return
        path, is_dir, _ = self.entries[self.selected_index]
        if not is_dir and path and self.parent_app.is_path_allowed(path):
            self.parent_app.update_file_preview(path)
            self.parent_app.selected_file = str(path)
    
    def get_selected_file(self):
        """Get currently selected file."""
        if not self.entries:
            return None
        path, is_dir, _ = self.entries[self.selected_index]
        if not path or is_dir or not self.parent_app.is_path_allowed(path):
            return None
        return str(path)


class PreviewPane(Static):
    """Scrollable preview with line selection support."""

    can_focus = True

    def __init__(self, parent_app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent_app = parent_app
        self.lines: list[str] = []
        self.file_path: Path | None = None
        self.cursor_line = 0
        self.selection_start: int | None = None
        self.selection_end: int | None = None
        self.preview_scroll_offset = 0
        self.page_size = 20

    def set_content(self, path: Path, lines: list[str]) -> None:
        """Load preview content for a file."""
        self.file_path = path
        self.lines = lines
        self.cursor_line = 0
        self.selection_start = None
        self.selection_end = None
        self.preview_scroll_offset = 0
        self._refresh_preview()

    def action_cursor_down(self) -> None:
        """Move cursor down one line."""
        if self.cursor_line < max(0, len(self.lines) - 1):
            self.cursor_line += 1
            self._ensure_cursor_visible()
            self._refresh_preview()

    def action_cursor_up(self) -> None:
        """Move cursor up one line."""
        if self.cursor_line > 0:
            self.cursor_line -= 1
            self._ensure_cursor_visible()
            self._refresh_preview()

    def action_page_down(self) -> None:
        """Scroll down like less/more."""
        if self.lines:
            self.cursor_line = min(len(self.lines) - 1, self.cursor_line + self.page_size)
            self._ensure_cursor_visible()
            self._refresh_preview()

    def action_page_up(self) -> None:
        """Scroll up like less/more."""
        if self.lines:
            self.cursor_line = max(0, self.cursor_line - self.page_size)
            self._ensure_cursor_visible()
            self._refresh_preview()

    def mark_start(self) -> None:
        """Mark selection start line."""
        self.selection_start = self.cursor_line
        if self.selection_end is not None and self.selection_end < self.selection_start:
            self.selection_end = None
        self._refresh_preview()

    def mark_end(self) -> None:
        """Mark selection end line."""
        if self.selection_start is None:
            self.selection_start = self.cursor_line
        self.selection_end = self.cursor_line
        self._refresh_preview()

    def append_selection_to_context(self) -> None:
        """Append selected range to the next KI request."""
        if self.file_path is None or not self.lines:
            return

        start = self.selection_start if self.selection_start is not None else self.cursor_line
        end = self.selection_end if self.selection_end is not None else self.cursor_line
        start, end = sorted((start, end))
        selected_lines = self.lines[start:end + 1]
        self.parent_app.append_preview_selection(self.file_path, start + 1, end + 1, selected_lines)

    def _ensure_cursor_visible(self) -> None:
        if self.cursor_line < self.preview_scroll_offset:
            self.preview_scroll_offset = self.cursor_line
        elif self.cursor_line >= self.preview_scroll_offset + self.page_size:
            self.preview_scroll_offset = self.cursor_line - self.page_size + 1

    def _refresh_preview(self) -> None:
        if self.file_path is None:
            self.update("No file selected")
            return

        start = self.preview_scroll_offset
        end = min(len(self.lines), start + self.page_size)
        rendered = [f"{self.file_path.name}", "─" * 60]
        selection_range = None
        if self.selection_start is not None:
            selection_end = self.selection_end if self.selection_end is not None else self.selection_start
            selection_range = range(min(self.selection_start, selection_end), max(self.selection_start, selection_end) + 1)

        for line_no in range(start, end):
            cursor = ">" if line_no == self.cursor_line else " "
            marker = "* " if selection_range and line_no in selection_range else "  "
            rendered.append(f"{cursor}{marker}{line_no + 1:3} {self.lines[line_no]}")

        if end < len(self.lines):
            rendered.append("... (truncated)")

        self.update("\n".join(rendered))


class ChatInput(TextArea):
    """Single-purpose chat input with Enter-to-send."""

    def __init__(self, parent_app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent_app = parent_app

    def on_key(self, event) -> None:
        """Submit on Enter when the input has focus."""
        if event.key == "enter" and self.parent_app.current_focus == "input":
            self.parent_app.action_select_cursor()
            event.prevent_default()
            event.stop()


class CodeAssistantApp(Static):
    """Code assistant with file browser and chat."""
    
    CSS_PATH = "styles/textual_app.tcss"
    
    # Reactive state
    current_focus = reactive("browser")  # "browser", "chat", "input", or "preview"
    project_loaded = reactive(False)
    
    BINDINGS = [
        Binding("tab", "focus_next", "Focus Next", show=True),
        Binding("shift+tab", "focus_previous", "Focus Previous", show=True),
        Binding("enter", "select_cursor", "Select / Send", show=False),
        Binding("up", "cursor_up", "Up", show=False),
        Binding("down", "cursor_down", "Down", show=False),
        Binding("pageup", "page_up", "Page Up", show=False),
        Binding("pagedown", "page_down", "Page Down", show=False),
        Binding("ctrl+b", "focus_browser", "Browser", show=True),
        Binding("ctrl+f", "focus_preview", "Preview", show=True),
        Binding("ctrl+c", "focus_chat", "Chat", show=True),
        Binding("ctrl+i", "focus_input", "Input", show=True),
        Binding("ctrl+o", "open_prompts", "Prompts", show=True),
        Binding("ctrl+s", "open_settings", "Settings", show=True),
        Binding("ctrl+l", "load_context", "Load Context", show=True),
        Binding("ctrl+x", "open_shell_command_dialog", "Shell Command", show=True),
        Binding("s", "mark_selection_start", "Mark Start", show=True),
        Binding("e", "mark_selection_end", "Mark End", show=True),
        Binding("l", "load_file", "Load File to Context", show=True),
        Binding("q", "app_quit", "Quit", show=True),
    ]
    
    # Local keys per focus area
    FOCUS_KEYS = {
        "browser": ["↑/↓ navigate", "enter select", "s mark start"],
        "preview": ["↑/↓ scroll", "pgup/pgdn page", "enter select"],
        "chat": ["↑/↓ scroll", "pgup/pgdn page"],
        "input": ["enter send", "esc cancel"],
    }
    
    def __init__(self):
        super().__init__()
        self.chat_session = ChatSession(os.getcwd())
        self.file_list = None
        self.preview_display = None
        self.preview_title = None
        self.chat_display = None
        self.terminal_panel = None  # Terminal output panel
        self.input_field = None
        self.status_bar = None
        self.selected_file = None
        self.loaded_files = []  # Track files added to context via L key
        self.waiting_for_response = False  # Track if waiting for LLM
        self.spinner_index = 0  # For spinner animation
        self.llm_worker = None  # Track worker thread
        self.open_edit_tabs = {}  # Track {file_path: EditTab}
        
        # Load resolved kicli-code-assist config and LLM client
        from kicli_code_assist.app_config import AppConfig as Config
        from kicli_code_assist.examples.simple_chat import create_client
        
        self.config = Config.from_env()
        self.allowed_base_path = self._resolve_allowed_base_path()
        from kicli_code_assist.cli import _detect_best_provider
        provider = _detect_best_provider()
        self.client = create_client(self.config, provider)
        
        # Initialize prompt manager with the full raw config dict (needed
        # for the top-level "prompts" section, which AppConfig doesn't
        # flatten into its own attributes).
        self.prompt_manager = PromptManager(self.config.raw)
        
        # Initialize shell execution integration and workflow
        self.shell_integration = ShellExecutorIntegration(self.chat_session)
        self.editing_workflow = CommandEditingWorkflow()
    
    def get_allowed_base_path(self) -> Path:
        """Return the allowed project root for file browsing and previews."""
        return self.allowed_base_path
    
    def _resolve_allowed_base_path(self) -> Path:
        """Resolve the workspace root but prevent escapes outside the configured base."""
        configured = self.config.kicli_allowed_base_path or os.getcwd()
        candidate = Path(configured).expanduser().resolve()
        if not candidate.exists() or not candidate.is_dir():
            candidate = Path(os.getcwd()).resolve()
        return candidate
    
    def is_path_allowed(self, path: Path | str) -> bool:
        """Check whether a path stays within the configured project root."""
        try:
            resolved = Path(path).expanduser().resolve()
        except OSError:
            return False
        return resolved == self.allowed_base_path or self.allowed_base_path in resolved.parents
    
    def action_focus_browser(self) -> None:
        """Focus the file browser panel."""
        self.current_focus = "browser"
        self.call_after_refresh(self.file_list.focus)

    def action_focus_preview(self) -> None:
        """Focus the file preview panel."""
        self.current_focus = "preview"
        if self.preview_display:
            self.call_after_refresh(self.preview_display.focus)

    def action_focus_chat(self) -> None:
        """Focus the chat panel."""
        self.current_focus = "chat"
        if self.chat_display:
            self.call_after_refresh(self.chat_display.focus)

    def action_focus_input(self) -> None:
        """Focus the input panel."""
        self.current_focus = "input"
        if self.input_field:
            self.call_after_refresh(self.input_field.focus)
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        # Title
        yield Static("🤖 KI Code Assistant", classes="title")
        
        # Main content area
        with Horizontal(id="main_container"):
            # Left: Browser/Editor tabs
            with Vertical(id="left_panel", classes="panel"):
                self.browser_title = Static("📂 Browser", classes="panel_title", id="browser_title")
                yield self.browser_title
                with TabbedContent(id="browser_editor_tabs"):
                    # Browser tab
                    with TabPane("📂 Browser", id="tab_browser"):
                        with Vertical():
                            self.file_list = SelectableFileList(self, id="file_list_display", classes="preview")
                            yield self.file_list
                            self.preview_title = Static("👁️  File Preview", classes="panel_title", id="preview_title")
                            yield self.preview_title
                            self.preview_display = PreviewPane(self, id="preview_display", classes="preview")
                            yield self.preview_display
        
            # Right: Chat/Terminal tabs
            with Vertical(id="right_panel", classes="panel"):
                self.chat_title = Static("💬 Chat  🖥️  Terminal", classes="panel_title", id="chat_title")
                yield self.chat_title
                with TabbedContent(id="chat_terminal_tabs"):
                    # Chat tab
                    with TabPane("💬 Chat", id="tab_chat"):
                        self.chat_display = RichLog(highlight=False, markup=True)
                        yield self.chat_display
                    
                    # Terminal tab
                    with TabPane("🖥️  Terminal", id="tab_terminal"):
                        self.terminal_panel = TerminalPanel(id="terminal_panel")
                        yield self.terminal_panel
        
        # Input area
        self.input_title = Static("⌨️  Input", classes="input_title", id="input_title")
        yield self.input_title
        self.input_field = ChatInput(self, id="chat_input", language="markdown")
        self.input_field.show_line_numbers = False
        self.input_field.show_cursor_line = False
        self.input_field.can_focus = True
        yield self.input_field
        
        # Status bar
        self.status_bar = Static("Curr-focus: B  |  ❌ No context loaded", classes="status_bar")
        yield self.status_bar
    
    def on_mount(self) -> None:
        """Setup after mount."""
        self.input_field.focus()
        self.current_focus = "input"
        # Defer preview initialization until rendering is complete
        self.app.call_later(self._init_preview_async)
    
    def _init_preview_async(self) -> None:
        """Initialize preview after rendering."""
        self.chat_display.write("Welcome to KI Code Assistant!\nTAB: Browser (B) → Chat (C) → Input (I), UP/DOWN to navigate/scroll, L to load files.\n")
    
    def action_focus_next(self) -> None:
        """Focus next widget (TAB) - cycle: browser → chat → input → preview → browser."""
        if self.current_focus == "browser":
            self.current_focus = "chat"
        elif self.current_focus == "chat":
            self.current_focus = "input"
        elif self.current_focus == "input":
            self.current_focus = "preview"
        else:  # preview
            self.current_focus = "browser"
        # watch_current_focus will be called automatically
    
    def action_focus_previous(self) -> None:
        """Focus previous widget (Shift+TAB) - cycle: preview ← input ← chat ← browser ← preview."""
        if self.current_focus == "preview":
            self.current_focus = "input"
        elif self.current_focus == "input":
            self.current_focus = "chat"
        elif self.current_focus == "chat":
            self.current_focus = "browser"
        else:  # browser
            self.current_focus = "preview"
            # watch_current_focus will be called automatically
    
    def action_cursor_up(self) -> None:
        """Move cursor up in file list, scroll chat/preview if focused."""
        if self.current_focus == "browser" and self.file_list:
            self.file_list.action_cursor_up()
        elif self.current_focus == "chat" and self.chat_display:
            self.chat_display.scroll_up()
        elif self.current_focus == "preview" and self.preview_display:
            self.preview_display.scroll_up()
    
    def action_cursor_down(self) -> None:
        """Move cursor down in file list, scroll chat/preview if focused."""
        if self.current_focus == "browser" and self.file_list:
            self.file_list.action_cursor_down()
        elif self.current_focus == "chat" and self.chat_display:
            self.chat_display.scroll_down()
        elif self.current_focus == "preview" and self.preview_display:
            self.preview_display.action_cursor_down()

    def action_select_cursor(self) -> None:
        """Select item in file list (browser) or submit (input mode)."""
        if self.current_focus == "browser" and self.file_list:
            self.file_list.action_select_cursor()
        elif self.current_focus == "preview" and self.preview_display:
            self.preview_display.append_selection_to_context()
        elif self.current_focus == "input":
            # Manually handle input submission
            msg = self.input_field.text.strip()
            if msg:
                self.on_input_submitted_manual(msg)

    def action_page_up(self) -> None:
        """Page up in preview/chat."""
        if self.current_focus == "chat" and self.chat_display:
            self.chat_display.scroll_page_up()
        elif self.current_focus == "preview" and self.preview_display:
            self.preview_display.action_page_up()

    def action_page_down(self) -> None:
        """Page down in preview/chat."""
        if self.current_focus == "chat" and self.chat_display:
            self.chat_display.scroll_page_down()
        elif self.current_focus == "preview" and self.preview_display:
            self.preview_display.action_page_down()

    def action_mark_selection_start(self) -> None:
        """Mark selection start in preview."""
        if self.current_focus == "preview" and self.preview_display:
            self.preview_display.mark_start()

    def action_mark_selection_end(self) -> None:
        """Mark selection end in preview."""
        if self.current_focus == "preview" and self.preview_display:
            self.preview_display.mark_end()
    
    def action_app_quit(self) -> None:
        """Quit the application (Q key)."""
        self.app.exit()
    
    def action_load_file(self) -> None:
        """Load selected file to context (L key)."""
        if not self.file_list:
            return
        
        file_path = self.file_list.get_selected_file()
        if not file_path:
            self.chat_display.write("[bold yellow]⚠️  No valid file selected within the allowed workspace[/]\n")
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
    
    def action_edit_file(self) -> None:
        """Edit selected file in editor tab (E key)."""
        if not self.file_list:
            return
        
        file_path = self.file_list.get_selected_file()
        if not file_path:
            self.chat_display.write("[bold yellow]⚠️  No valid file selected[/]\n")
            return
        
        path_obj = Path(file_path)
        if not path_obj.is_file():
            self.chat_display.write(f"[bold yellow]⚠️  Not a file: {file_path}[/]\n")
            return
        
        self.open_file_in_editor(path_obj)
    
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
    
    def action_open_prompts(self) -> None:
        """Open prompt management UI (Ctrl+O)."""
        self.app.push_screen(PromptsModal(self.prompt_manager))

    def action_open_settings(self) -> None:
        """Open the schema-driven settings editor (Ctrl+S)."""
        from kicli_code_assist.ui.settings_panel import SettingsModal
        import ki_core
        self.app.push_screen(
            SettingsModal(self.config.raw, ki_core.find_config_path())
        )

    def action_open_shell_command_dialog(self) -> None:
        """Open manual shell command entry dialog (Ctrl+X)."""
        from kicli_code_assist.executor.shell_execution import ShellCommandBatch
        from kicli_code_assist.ui.shell_command_editor import CommandManualEntryDialog
        
        # Create empty batch to populate
        modal = CommandManualEntryDialog()
        self.app.push_screen(modal, callback=self._on_manual_command_entry_result)
    
    def _on_manual_command_entry_result(self, batch: ShellCommandBatch) -> None:
        """Handle manual command entry dialog result."""
        if batch is None or len(batch.commands) == 0:
            self.chat_display.write("[bold yellow]⊘ No commands entered[/]\n")
            return
        
        # Show approval modal with user-entered commands
        self.show_shell_approval_modal(batch, "User-entered commands")

    
    def watch_current_focus(self, focus: str) -> None:
        """Update UI when focus changes."""
        # Update CSS classes for title highlighting
        self.browser_title.remove_class("active")
        self.chat_title.remove_class("active")
        self.input_title.remove_class("active")
        if self.preview_title:
            self.preview_title.remove_class("active")
        
        if focus == "input":
            if self.input_field:
                self.call_after_refresh(self.input_field.focus)
            self.input_title.add_class("active")
        elif focus == "chat":
            self.chat_display.focus()
            self.chat_title.add_class("active")
        elif focus == "preview":
            if self.preview_display:
                self.call_after_refresh(self.preview_display.focus)
            self.preview_title.add_class("active")
        else:  # browser
            self.call_after_refresh(self.file_list.focus)
            self.browser_title.add_class("active")
        
        # Update status bar with intelligent key hints
        self._update_status_bar(focus)
    
    def _update_status_bar(self, focus: str) -> None:
        """Update status bar with global and local key hints."""
        # Global navigation shortcuts
        global_keys = "tab/⇧tab ↔  ^b ^f ^i ^c  ^o ^s"
        
        # Local keys for current focus area
        local_keys = "  |  "
        if focus in self.FOCUS_KEYS:
            local_keys += " ".join(self.FOCUS_KEYS[focus])
        
        # Context status
        ctx_status = self.chat_session.get_context_status() if self.project_loaded else "❌ No context"
        
        # Full status line
        status_text = f"Focus: {global_keys}{local_keys}  |  {ctx_status}"
        self.status_bar.update(status_text)
    
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
        self.input_field.text = ""
        
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

    def _wrap_text(self, text: str, width: int = 76) -> str:
        """Wrap plain text for chat display."""
        lines = text.splitlines() or [text]
        wrapped_lines = [
            textwrap.fill(line, width=width) if line.strip() else ""
            for line in lines
        ]
        return "\n".join(wrapped_lines)
    
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
            
            # Try to extract shell commands from response
            command_batch = self.shell_integration.try_extract_commands(response_text)
            
            if command_batch and len(command_batch.commands) > 0:
                # Commands found - show approval modal instead of printing response
                self.chat_display.write("[bold cyan]🔧 Found shell commands - awaiting approval...[/]\n")
                
                # Add response to history
                self.chat_session.add_message("assistant", response_text)
                
                # Show approval modal (will handle execution, editing, etc. in message handlers)
                self.show_shell_approval_modal(command_batch, response_text)
            else:
                # No commands - show response normally
                wrapped_response = self._wrap_text(response_text, width=76)
                self.chat_display.write(wrapped_response + "\n")
                
                # Add to session history
                self.chat_session.add_message("assistant", response_text)
        
        except Exception as e:
            self.waiting_for_response = False
            self.chat_display.write(f"[bold red]❌ Error: {str(e)}[/]\n")
    
    def show_shell_approval_modal(self, command_batch, response_text: str) -> None:
        """Show shell command approval modal."""
        modal = ShellCommandApprovalModal(command_batch)
        self.app.push_screen(modal, callback=self._on_shell_approval_result)
    
    def _on_shell_approval_result(self, result) -> None:
        """Handle result from shell approval modal."""
        if result is None:
            # User cancelled
            self.chat_display.write("[bold yellow]⊘ Shell command execution cancelled[/]\n")
        elif hasattr(result, 'approved') and result.approved:
            # User approved - execute commands in background worker
            if hasattr(result, 'edited_commands') and result.edited_commands:
                # Create batch from edited commands
                batch = ShellCommandBatch(commands=result.edited_commands)
                
                # Create async wrapper (Python doesn't support async lambda)
                async def run_execution():
                    await self._execute_shell_batch_worker(batch, result)
                
                # Run execution in background worker
                self.run_worker(run_execution)
            else:
                self.chat_display.write("[bold yellow]⊘ No commands to execute[/]\n")
        else:
            # User skipped
            self.chat_display.write("[bold yellow]⊘ Commands skipped[/]\n")
    
    async def _execute_shell_batch_worker(self, batch: ShellCommandBatch, result) -> None:
        """Execute shell batch in background worker (async)."""
        try:
            from kicli_code_assist.executor.shell_execution import (
                ShellExecutionApproval, 
                ApprovalDecision, 
                SessionPermissionLevel
            )
            
            # Determine session permission level from result
            session_mode = getattr(result, 'session_mode', False)
            perm_level = SessionPermissionLevel.SESSION if session_mode else SessionPermissionLevel.BATCH
            
            # Create approval object
            approval = ShellExecutionApproval(
                batch_id=batch.id,
                decision=ApprovalDecision.APPROVED,
                approved_by="user",
                session_permission_level=perm_level
            )
            
            # Execute batch in thread pool to avoid blocking
            execution_result = await asyncio.get_event_loop().run_in_executor(
                None, 
                self.chat_session.execute_shell_batch, 
                batch, 
                approval
            )
            
            # Display results in chat AND terminal
            self.chat_display.write(f"\n[bold cyan]🔧 Execution Results:[/]\n")
            if self.terminal_panel:
                self.terminal_panel.write(f"\n[bold cyan]🔧 Execution Results:[/]\n")
            
            if execution_result.get("status") == "completed":
                attempted = execution_result.get("commands_attempted", 0)
                succeeded = execution_result.get("commands_succeeded", 0)
                failed = execution_result.get("commands_failed", 0)
                
                summary = f"[bold green]✓ {succeeded}/{attempted} commands succeeded[/]\n"
                self.chat_display.write(summary)
                if self.terminal_panel:
                    self.terminal_panel.write_success(f"{succeeded}/{attempted} commands succeeded")
                
                # Show output for each command
                results = execution_result.get("results", [])
                for i, cmd_result in enumerate(results, 1):
                    cmd = batch.commands[i-1] if i <= len(batch.commands) else None
                    
                    status_icon = "✓" if cmd_result["success"] else "✗"
                    status_color = "green" if cmd_result["success"] else "red"
                    
                    line = f"\n[bold]{i}. [{status_color}]{status_icon}[/] {cmd.command if cmd else 'Unknown'}\n"
                    self.chat_display.write(line)
                    if self.terminal_panel:
                        self.terminal_panel.write_command(cmd.command if cmd else "Unknown")
                    
                    if cmd_result.get("stdout"):
                        self.chat_display.write(f"[dim]{cmd_result['stdout']}[/]\n")
                        if self.terminal_panel:
                            self.terminal_panel.write_stdout(cmd_result['stdout'])
                    
                    if cmd_result.get("stderr"):
                        self.chat_display.write(f"[bold red]{cmd_result['stderr']}[/]\n")
                        if self.terminal_panel:
                            self.terminal_panel.write_stderr(cmd_result['stderr'])
                    
                    # Show returncode if non-zero
                    returncode = cmd_result.get("returncode", 0)
                    if returncode != 0:
                        rc_line = f"[yellow]Return code: {returncode}[/]\n"
                        self.chat_display.write(rc_line)
                        if self.terminal_panel:
                            self.terminal_panel.write(f"[yellow]Return code: {returncode}[/]\n")
            else:
                error_msg = f"[bold red]✗ Execution failed: {execution_result.get('reason', 'Unknown error')}[/]\n"
                self.chat_display.write(error_msg)
                if self.terminal_panel:
                    self.terminal_panel.write_error(execution_result.get('reason', 'Unknown error'))
        
        except Exception as e:
            self.chat_display.write(f"[bold red]❌ Error executing commands: {str(e)}[/]\n")
    
    def update_file_preview(self, path: Path) -> None:
        """Update file preview when file is selected."""
        try:
            if path.is_file() and path.suffix not in ['.pyc', '.o']:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = [line.rstrip("\n") for line in f.readlines()]

                self.preview_display.set_content(path, lines)
        except Exception as e:
            self.preview_display.update(f"Error reading file: {str(e)}")

    def append_preview_selection(self, path: Path, start_line: int, end_line: int, lines: list[str]) -> None:
        """Add a selected preview range to the next KI request context."""
        selection_content = "\n".join(lines)
        self.loaded_files.append({
            "path": f"{path}#L{start_line}-L{end_line}",
            "content": selection_content,
        })
        self.chat_display.write(
            f"[bold cyan]📎 Added line range:[/] {path} L{start_line}-L{end_line}\n"
        )
    
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
    
    def open_file_in_editor(self, path: Path) -> None:
        """Open a file in a new editor tab.
        
        Args:
            path: Path to file to edit
        """
        if not path or not path.is_file():
            return
        
        # Convert to absolute path
        abs_path = path.resolve()
        
        # Check if already open
        if abs_path in self.open_edit_tabs:
            # Switch to existing tab
            tabs = self.query_one("#browser_editor_tabs", TabbedContent)
            tab_id = f"edit_tab_{abs_path.name}"
            tabs.active = tab_id
            return
        
        try:
            # Read file content
            content = abs_path.read_text()
            
            # Create edit tab
            edit_tab = EditTab(abs_path, content)
            
            # Add to tab pane
            tabs = self.query_one("#browser_editor_tabs", TabbedContent)
            tab_pane = TabPane(f"✏️ {abs_path.name}", edit_tab, id=f"edit_tab_{abs_path.name}")
            tabs.add_pane(tab_pane)
            
            # Track it
            self.open_edit_tabs[abs_path] = edit_tab
            
            # Switch to new tab
            tabs.active = f"edit_tab_{abs_path.name}"
            
            self.chat_display.write(f"[cyan]📂 Opened {abs_path.name} in editor[/]\n")
        
        except Exception as e:
            self.chat_display.write(f"[red]✗ Error opening file: {str(e)}[/]\n")


def main():
    """Run the application."""
    from textual.app import App
    
    class CodeAssistantMain(App):
        CSS_PATH = "styles/textual_app.tcss"
        
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

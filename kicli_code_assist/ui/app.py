"""Main code assistant application widget."""

import os
import asyncio
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, TabbedContent, TabPane, Button
from textual.binding import Binding
from textual.reactive import reactive
from textual.worker import Worker, WorkerState
import threading
import textwrap

from kicli_code_assist.chat_session import ChatSession
from kicli_code_assist.prompts import PromptManager
from kicli_code_assist.ui.shell_executor_integration import ShellExecutorIntegration
from kicli_code_assist.ui.shell_approval_widget import ShellCommandApprovalModal
from kicli_code_assist.ui.command_editing_workflow import CommandEditingWorkflow
from kicli_code_assist.ui.terminal_panel import TerminalPanel
from kicli_code_assist.ui.widgets.shell_input import ShellPanel
from kicli_code_assist.ui.edit_tab import EditTab
from kicli_code_assist.executor.shell_execution import ShellCommandBatch
from kicli_code_assist.ui.panels.file_browser import SelectableFileList
from kicli_code_assist.ui.panels.preview_pane import PreviewPane
from kicli_code_assist.ui.panels.left_panel import LeftPanel
from kicli_code_assist.ui.panels.chat_display import SelectableRichLog
from kicli_code_assist.ui.input.chat_input import ChatInput
from kicli_code_assist.ui.panels.file_editor import FileEditorPane
from kicli_code_assist.ui.modals.approval_modal import ApprovalModal
from kicli_code_assist.ui.modals.diff_viewer import DiffViewerModal
from kicli_code_assist.ai_workflow import AIWorkflowManager
from kicli_code_assist.llm_integration import get_async_integration


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
        Binding("ctrl+a", "focus_ai_background", "AI Background", show=True),
        Binding("ctrl+i", "focus_input", "Input", show=True),
        Binding("ctrl+x", "focus_shell", "Shell", show=True),
        Binding("ctrl+o", "open_prompts", "Prompts", show=True),
        Binding("ctrl+s", "open_settings", "Settings", show=True),
        Binding("ctrl+l", "load_context", "Load Context", show=True),
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
        "shell": ["↑/↓ history", "enter run", "esc cancel"],
    }
    
    def __init__(self):
        super().__init__()
        self.chat_session = ChatSession(os.getcwd())
        self.current_cwd = os.getcwd()  # Track current working directory
        self.file_list = None
        self.left_panel = None  # New LeftPanel with browser/editor tabs
        self.preview_display = None
        self.preview_title = None
        self.chat_display = None
        self.terminal_panel = None  # Terminal output panel
        self.shell_panel = None  # Shell input panel
        self.input_field = None
        self.status_bar = None
        self.selected_file = None
        self.loaded_files = []  # Track files added to context via L key
        self.waiting_for_response = False  # Track if waiting for LLM
        self.spinner_index = 0  # For spinner animation
        self.llm_worker = None  # Track worker thread
        self.open_edit_tabs = {}  # Track {file_path: EditTab}
        self.background_debug_display = None  # AI background/debug log
        
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
        
        # Initialize AI workflow manager
        self.ai_workflow_manager = AIWorkflowManager(
            llm_integration=get_async_integration(),
        )
        self._current_ai_suggestion = None  # Track active AI suggestion
    
    def _resolve_allowed_base_path(self) -> Path:
        """Resolve the base path that file operations are allowed to access."""
        if hasattr(self.config, 'workspace') and self.config.workspace:
            return Path(self.config.workspace).expanduser().resolve()
        return Path.cwd()
    
    def get_allowed_base_path(self) -> Path:
        """Get the workspace root path."""
        return self.allowed_base_path
    
    def is_path_allowed(self, path: Path | str) -> bool:
        """Return True if path is within the allowed workspace."""
        try:
            path_obj = Path(path).resolve()
            base = self.allowed_base_path.resolve()
            path_obj.relative_to(base)
            return True
        except ValueError:
            return False
    
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

    def action_focus_ai_background(self) -> None:
        """Focus the AI Background/Debug tab."""
        self.current_focus = "ai_background"
        tabs = self.query_one("#chat_terminal_tabs", TabbedContent)
        tabs.active = "tab_ai_background"
        if self.background_debug_display:
            self.call_after_refresh(self.background_debug_display.focus)

    def action_focus_input(self) -> None:
        """Focus the input panel."""
        self.current_focus = "input"
        if self.input_field:
            self.call_after_refresh(self.input_field.focus)
    
    def action_focus_shell(self) -> None:
        """Focus the shell panel (Ctrl+X)."""
        self.current_focus = "shell"
        tabs = self.query_one("#chat_terminal_tabs", TabbedContent)
        tabs.active = "tab_shell"
        # Update CWD display and focus input
        if hasattr(self, 'shell_panel') and self.shell_panel:
            self.shell_panel.update_cwd(self.current_cwd)
            if self.shell_panel.input:
                self.call_after_refresh(self.shell_panel.input.focus)
    
    def _write_background_log(self, message: str) -> None:
        """Write message to AI Background debug tab."""
        if self.background_debug_display:
            self.call_later(lambda: self.background_debug_display.write(f"[dim]{message}[/]"))
    
    def set_cwd(self, new_cwd: str) -> None:
        """Change current working directory and update shell panel."""
        if os.path.isdir(new_cwd):
            self.current_cwd = new_cwd
            if self.shell_panel:
                self.shell_panel.update_cwd(new_cwd)
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        # Title
        yield Static("🤖 KI Code Assistant", classes="title")
        
        # Main content area
        with Horizontal(id="main_container"):
            # Left: Browser/Editor tabs (new LeftPanel)
            with Vertical(id="left_panel", classes="panel"):
                self.left_panel = LeftPanel(parent_app=self)
                yield self.left_panel
        
            # Right: Chat/Terminal tabs
            with Vertical(id="right_panel", classes="panel"):
                with TabbedContent(id="chat_terminal_tabs"):
                    # Chat tab
                    with TabPane("💬 Chat", id="tab_chat"):
                        self.chat_display = SelectableRichLog(highlight=False, markup=True)
                        yield self.chat_display
                    
                    # AI Background / Debug tab
                    with TabPane("🧠 AI Background", id="tab_ai_background"):
                        self.background_debug_display = SelectableRichLog(highlight=False, markup=True)
                        yield self.background_debug_display
                    
                    # Terminal tab
                    with TabPane("🖥️  Terminal", id="tab_terminal"):
                        self.terminal_panel = TerminalPanel(id="terminal_panel")
                        yield self.terminal_panel
                    
                    # Shell tab (Ctrl+X)
                    with TabPane("⌨️  Shell", id="tab_shell"):
                        self.shell_panel = ShellPanel(id="shell_panel")
                        yield self.shell_panel
        
        # Input area with Send button
        self.input_title = Static("⌨️  Input", classes="input_title", id="input_title")
        yield self.input_title
        
        # Input field and button in horizontal layout (with no extra container, just use compose context)
        self.input_field = ChatInput(self, id="chat_input", language="markdown")
        self.input_field.show_line_numbers = False
        self.input_field.show_cursor_line = False
        self.input_field.can_focus = True
        
        with Horizontal(id="input_container", classes="input_container"):
            yield self.input_field
            yield Button("↵ Send", id="chat-send-btn", variant="primary")
        
        # Status bar
        self.status_bar = Static("Curr-focus: B  |  ❌ No context loaded", classes="status_bar")
        yield self.status_bar
    
    def on_mount(self) -> None:
        """Setup after mount."""
        # Get references to file_list and preview_display after widgets are mounted
        self.file_list = self.left_panel.query_one("#file-browser", SelectableFileList)
        self.preview_display = PreviewPane(self, id="preview_display", classes="preview")
        self.left_panel.add_preview_pane(self.preview_display)
        
        # Set Chat tab as default active tab
        tabs = self.query_one("#chat_terminal_tabs", TabbedContent)
        tabs.active = "tab_chat"
        
        if self.input_field:
            self.call_after_refresh(self.input_field.focus)
    
    def on_preview_pane_preview_enter(self, message: PreviewPane.PreviewEnter) -> None:
        """Handle Enter key in preview to open editor tab."""
        # Create editor tab
        editor = self.left_panel.create_editor_tab(str(message.file_path), message.content)
        self.app.notify(f"📝 Editing {message.file_path.name}", timeout=2)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "chat-send-btn":
            # Send button clicked
            self.input_field.send_message()
            event.stop()  # Prevent bubbling
    
    def action_open_prompts(self) -> None:
        """Open prompt management UI (Ctrl+O)."""
        from kicli_code_assist.ui.modals.prompts_modal import PromptsModal
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
        # Set focus to appropriate widget based on focus mode
        if focus == "input":
            if self.input_field:
                self.call_after_refresh(self.input_field.focus)
            self.input_title.add_class("active")
        elif focus == "chat":
            if self.chat_display:
                self.chat_display.focus()
        elif focus == "preview":
            if self.preview_display and self.preview_title:
                self.call_after_refresh(self.preview_display.focus)
                self.preview_title.add_class("active")
        else:  # browser
            if self.file_list:
                self.call_after_refresh(self.file_list.focus)
        
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
        
        # Context status: show loaded files or project context
        if self.loaded_files:
            # Show loaded files with truncation if too many
            files_display = ", ".join(Path(f).name for f in self.loaded_files[:5])
            if len(self.loaded_files) > 5:
                files_display += f", +{len(self.loaded_files) - 5} more"
            ctx_status = f"📁 Loaded: {files_display}"
        else:
            ctx_status = self.chat_session.get_context_status() if self.project_loaded else "❌ No context"
        
        # Full status line
        status_text = f"Focus: {global_keys}{local_keys}  |  {ctx_status}"
        self.status_bar.update(status_text)
    
    def show_status_message(self, message: str, duration_ms: int = 3000) -> None:
        """Show a temporary status message, then restore status bar.
        
        Args:
            message: Message to display
            duration_ms: How long to show (milliseconds)
        """
        def _show_and_restore():
            self.status_bar.update(message)
            self.set_timer(duration_ms / 1000.0, self._restore_status_bar)
        
        # If called from worker thread, schedule on main thread via app
        try:
            # Try to call from thread if we're in a worker
            self.app.call_from_thread(_show_and_restore)
        except RuntimeError:
            # Already on main thread
            _show_and_restore()
    
    def _restore_status_bar(self) -> None:
        """Restore status bar to show focus and context info."""
        self._update_status_bar(self.current_focus)
    
    
    def action_cursor_up(self) -> None:
        """Move cursor up in current panel."""
        if self.current_focus == "browser" and self.file_list:
            self.file_list.action_cursor_up()
        elif self.current_focus == "preview" and self.preview_display:
            self.preview_display.action_cursor_up()

    def action_cursor_down(self) -> None:
        """Move cursor down in current panel."""
        if self.current_focus == "browser" and self.file_list:
            self.file_list.action_cursor_down()
        elif self.current_focus == "preview" and self.preview_display:
            self.preview_display.action_cursor_down()

    def action_page_up(self) -> None:
        """Page up in current panel."""
        if self.current_focus == "preview" and self.preview_display:
            self.preview_display.action_page_up()

    def action_page_down(self) -> None:
        """Page down in current panel."""
        if self.current_focus == "preview" and self.preview_display:
            self.preview_display.action_page_down()

    def action_select_cursor(self) -> None:
        """Handle selection in current focus area."""
        if self.current_focus == "browser":
            if self.file_list:
                self.file_list.action_select_cursor()
        elif self.current_focus == "input":
            # Submit chat message
            text = self.input_field.text.strip()
            if text:
                self.input_field.text = ""
                self.run_worker(lambda: self._submit_chat(text), thread=True)
    
    def action_mark_selection_start(self) -> None:
        """Mark selection start in preview."""
        if self.current_focus == "preview" and self.preview_display:
            self.preview_display.mark_start()
    
    def action_mark_selection_end(self) -> None:
        """Mark selection end in preview."""
        if self.current_focus == "preview" and self.preview_display:
            self.preview_display.mark_end()
            self.preview_display.append_selection_to_context()
    
    def action_load_context(self) -> None:
        """Load selected file to context (Ctrl+L)."""
        if self.selected_file:
            self.run_worker(lambda: self._load_file_to_context(self.selected_file), thread=True)
    
    def action_load_file(self) -> None:
        """Load file to context via L key."""
        if not self.file_list:
            self.show_status_message("[bold red]✗ File browser not available[/]", duration_ms=2000)
            return
            
        if self.current_focus != "browser":
            self.show_status_message(
                f"[bold yellow]ℹ️  Focus on {self.current_focus}. Press Ctrl+B for browser, then L.[/]",
                duration_ms=3000
            )
            return
        
        selected = self.file_list.get_selected_file()
        if not selected:
            self.show_status_message(
                "[bold yellow]ℹ️  No file selected. Navigate ↑↓ and press L.[/]",
                duration_ms=2500
            )
            return
            
        self.run_worker(lambda: self._load_file_to_context(selected), thread=True)
    
    def action_app_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
    
    def _submit_chat(self, text: str) -> None:
        """Submit chat message (worker thread)."""
        try:
            self.chat_display.write(f"[bold cyan]You:[/] {text}\n")
            
            # Get context files
            context_text = self.chat_session.get_context()
            prompt = f"{context_text}\n{text}" if context_text else text
            
            # Stream response
            self.chat_display.write("[bold green]KI:[/] ")
            response_text = ""
            
            for chunk in self.client.messages.stream(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4096,
            ):
                if chunk.type == "content_block_delta":
                    delta_text = chunk.delta.text
                    response_text += delta_text
                    self.chat_display.write(delta_text)
            
            self.chat_display.write("\n")
            
        except Exception as e:
            self.chat_display.write(f"[bold red]❌ Error: {str(e)}[/]\n")
    
    def _load_file_to_context(self, file_path: str) -> None:
        """Load file to context (worker thread)."""
        try:
            path = Path(file_path)
            if not self.is_path_allowed(path):
                self.show_status_message(f"[bold red]✗ Path not allowed: {file_path}[/]", duration_ms=2000)
                return
            
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            # Add file as a message to include in chat context
            msg_content = f"<file path=\"{path}\">\n{content}\n</file>"
            self.chat_session.add_message("user", msg_content, include_context=True)
            self.loaded_files.append(str(path))
            self.project_loaded = True
            
            # Refresh file browser display to show loaded file in color
            if self.file_list:
                def refresh_display():
                    self.file_list.update_display()
                self.app.call_from_thread(refresh_display)
            
            # Show success message, then update to show loaded files
            self.show_status_message(f"[bold green]✓ Loaded: {path.name}[/]", duration_ms=2000)
            
        except Exception as e:
            self.show_status_message(f"[bold red]✗ Error loading file: {str(e)}[/]", duration_ms=3000)
    
    def update_file_preview(self, path: Path) -> None:
        """Update preview pane with file contents."""
        try:
            if not self.is_path_allowed(path):
                self.preview_display.update("❌ Path not allowed")
                return
            
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
            
            # Remove trailing newlines
            lines = [line.rstrip('\n') for line in lines]
            
            self.preview_display.set_content(path, lines)
            self.selected_file = str(path)
        except Exception as e:
            self.preview_display.update(f"Error loading preview: {e}")
    
    def append_preview_selection(self, file_path: Path, start_line: int, end_line: int, lines: list[str]) -> None:
        """Append file selection to context."""
        try:
            selected_content = "\n".join(lines)
            self.chat_session.add_selection(str(file_path), start_line, end_line, selected_content)
            self.chat_display.write(
                f"[bold green]✓ Added {file_path.name}:{start_line}-{end_line} to context[/]\n"
            )
            self.project_loaded = True
        except Exception as e:
            self.chat_display.write(f"[bold red]✗ Error: {str(e)}[/]\n")
    
    def show_shell_approval_modal(self, batch: ShellCommandBatch, description: str) -> None:
        """Show shell command approval modal."""
        modal = ShellCommandApprovalModal(batch, description)
        self.app.push_screen(modal, callback=self._on_shell_approval_result)
    
    def _on_shell_approval_result(self, result) -> None:
        """Handle shell approval result."""
        if result is None:
            return
        
        # Execute approved commands
        self.chat_display.write(f"[bold blue]→ Executing {len(result.commands)} commands...[/]\n")
        self.run_worker(lambda: self._execute_shell_commands(result), thread=True)
    
    def _execute_shell_commands(self, batch: ShellCommandBatch) -> None:
        """Execute shell commands (worker thread)."""
        try:
            for cmd_obj in batch.commands:
                command = cmd_obj.command
                self.terminal_panel.write_command(command)
                
                # Execute
                import subprocess
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.stdout:
                    self.terminal_panel.write_stdout(result.stdout)
                if result.stderr:
                    self.terminal_panel.write_stderr(result.stderr)
                
                if result.returncode == 0:
                    self.terminal_panel.write_success(f"Exit code: {result.returncode}")
                else:
                    self.terminal_panel.write_error(f"Exit code: {result.returncode}")
                    
        except Exception as e:
            self.terminal_panel.write_error(str(e))
    
    def _process_ai_suggestions_worker(
        self, file_path: str, file_content: str
    ) -> None:
        """Process AI suggestions (runs in worker thread)."""
        try:
            # Log to chat display (thread-safe)
            self.call_later(lambda: self.chat_display.write(f"[dim][AI] Processing {Path(file_path).name}...[/]"))
            
            # Build prompt from file context
            prompt = f"""Please suggest improvements to this file:

File: {file_path}
Language: {Path(file_path).suffix[1:].lower()}

Analyze for:
- Code quality issues
- Security vulnerabilities
- Performance improvements
- Best practices
- Readability

Only suggest changes that are clearly beneficial."""

            # Run async processing
            self.call_later(lambda: self.chat_display.write(f"[dim][AI] Calling AI workflow manager...[/]"))
            
            # Helper to write to background log
            def on_progress_callback(msg: str):
                self._write_background_log(msg)
            
            # Create new event loop for this thread
            try:
                suggestion = asyncio.run(
                    self.ai_workflow_manager.process_user_prompt(
                        prompt=prompt,
                        file_context=file_content,
                        current_file_path=file_path,
                        on_progress=on_progress_callback,
                    )
                )
            except RuntimeError as e:
                if "asyncio.run() cannot be called from a running event loop" in str(e):
                    # Already in event loop, call directly
                    self.call_later(lambda: self.chat_display.write(f"[yellow][AI] Using fallback async mode[/]"))
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            asyncio.run,
                            self.ai_workflow_manager.process_user_prompt(
                                prompt=prompt,
                                file_context=file_content,
                                current_file_path=file_path,
                                on_progress=on_progress_callback,
                            )
                        )
                        suggestion = future.result(timeout=30)
                else:
                    raise
            
            if suggestion:
                self._current_ai_suggestion = suggestion
                self.call_later(lambda: self.chat_display.write(f"[green]✓ AI suggestions generated ({len(suggestion.approval_session.hunks)} hunks)[/]"))
                self.call_later(lambda: self._write_background_log(f"DEBUG: About to show approval modal"))
                # Show approval modal on main thread
                self.call_later(self._show_ai_approval_modal)
            else:
                self.call_later(lambda: self.chat_display.write(f"[yellow]⊘ AI returned no suggestions[/]"))
        except Exception as e:
            import traceback
            self.call_later(lambda: self.chat_display.write(f"[bold red]✗ AI Error: {str(e)}[/]"))
            self.call_later(lambda: self.chat_display.write(f"[dim]{traceback.format_exc()}[/]"))
    
    def _show_ai_approval_modal(self) -> None:
        """Show AI approval modal for current suggestion."""
        self._write_background_log(f"DEBUG: _show_ai_approval_modal called, suggestion: {self._current_ai_suggestion is not None}")
        
        if not self._current_ai_suggestion:
            self._write_background_log(f"DEBUG: No suggestion set, returning")
            return
        
        try:
            self._write_background_log(f"DEBUG: Creating ApprovalModal with {len(self._current_ai_suggestion.approval_session.hunks)} hunks")
            modal = ApprovalModal(self._current_ai_suggestion.approval_session)
            self._write_background_log(f"DEBUG: Pushing modal to screen")
            self.app.push_screen(modal, callback=self._on_ai_approval_result)
            self._write_background_log(f"DEBUG: Modal pushed")
        except Exception as e:
            self._write_background_log(f"DEBUG: Modal error: {e}")
            import traceback
            self._write_background_log(traceback.format_exc())
    
    def _on_ai_approval_result(self, approved_session) -> None:
        """Handle AI approval result."""
        if approved_session is None:
            self.chat_display.write("[dim]⋯ AI suggestions cancelled[/]\n")
            return
        
        if not self._current_ai_suggestion:
            return
        
        suggestion = self._current_ai_suggestion
        
        # Build new content from approved changes
        new_content_lines = suggestion.original_content.split("\n")
        
        # Apply each approved hunk
        for hunk in suggestion.approval_session.hunks:
            from kicli_code_assist.approval_workflow import HunkStatus
            if hunk.status in (HunkStatus.APPROVED, HunkStatus.PARTIAL):
                for line in hunk.lines:
                    if line.status == HunkStatus.APPROVED:
                        idx = line.line_number - 1
                        if 0 <= idx < len(new_content_lines):
                            new_content_lines[idx] = line.modified_line
        
        new_content = "\n".join(new_content_lines)
        
        # Show diff viewer modal before applying
        def on_diff_result(applied_content):
            if applied_content is None:
                self.chat_display.write("[yellow]⊘ Changes rejected by user[/]\n")
                return
            
            # Apply to editor
            def apply_to_editor():
                for tab in self.open_edit_tabs.values():
                    if hasattr(tab, 'editor_pane') and tab.editor_pane.file_path == suggestion.file_path:
                        if hasattr(tab.editor_pane, 'editor') and tab.editor_pane.editor:
                            tab.editor_pane.editor.text = applied_content
                        break
            
            apply_to_editor()
            
            # Get summary
            summary = suggestion.approval_session.get_summary()
            self.chat_display.write(f"""[green]✓ Changes Applied[/green]
[dim]Approved: {summary['approved']}/{summary['total_hunks']} hunks
File: {suggestion.file_path}[/dim]
""")
            self._current_ai_suggestion = None
        
        # Show diff viewer
        modal = DiffViewerModal(
            original_content=suggestion.original_content,
            new_content=new_content,
            file_path=suggestion.file_path,
        )
        self.app.push_screen(modal, callback=on_diff_result)

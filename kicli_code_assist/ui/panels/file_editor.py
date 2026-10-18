"""File editor pane with Vi/Vim editing support and syntax highlighting."""

from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.reactive import Reactive
from textual.widgets import Button, Label, Static, Checkbox
from textual.widget import Widget
from textual.message import Message
from textual_vim_textarea import VimTextArea

# Import parent app class for type hints
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from kicli_code_assist.ui.app import CodeAssistantApp


class FileEditorPane(Container):
    """Editable file content with Vi/Vim support, syntax highlighting, and dirty state tracking.
    
    Uses event-driven mode updates via VimTextArea.ModeChanged messages for smooth, responsive
    mode indicator updates. No polling needed.
    """
    
    DEFAULT_CSS = """
    FileEditorPane {
        height: 1fr;
        layout: vertical;
    }
    
    FileEditorPane > #editor-header {
        height: 1;
        dock: top;
        background: $surface;
        border-bottom: solid $primary;
        layout: horizontal;
    }
    
    FileEditorPane > #editor-header #editor-title {
        text-align: left;
        width: 1fr;
        padding-left: 1;
    }
    
    FileEditorPane > #editor-header #editor-mode-indicator {
        text-align: right;
        width: auto;
        padding-right: 2;
    }
    
    FileEditorPane > #editor-buttons {
        height: auto;
        dock: bottom;
        background: $surface;
        border-top: solid $primary;
        layout: horizontal;
    }
    
    FileEditorPane > #editor-buttons > Button {
        margin: 0 1;
        height: auto;
    }
    
    FileEditorPane > #editor-buttons > Checkbox {
        margin: 0 1;
        height: auto;
    }
    
    FileEditorPane VimTextArea {
        height: 1fr;
    }
    """
    
    file_path: Reactive[str] = Reactive("")
    content: Reactive[str] = Reactive("")
    is_dirty: Reactive[bool] = Reactive(False)
    ai_suggestions_enabled: Reactive[bool] = Reactive(False)
    vim_mode: Reactive[str] = Reactive("NORMAL")
    
    def __init__(self, file_path: str, content: str, name: str | None = None, id: str | None = None):
        """Initialize file editor.
        
        Args:
            file_path: Full path to file
            content: Initial file content
            name: Widget name
            id: Widget ID (typically filename for tab use)
        """
        super().__init__(name=name, id=id)
        self.file_path = file_path
        self.content = content
        self._original_content = content
        self.editor: VimTextArea | None = None
        self.ai_checkbox: Checkbox | None = None
        self.mode_indicator: Label | None = None
        self._ai_in_progress = False
        self._auto_save_timer = None
    
    def compose(self) -> ComposeResult:
        """Create editor layout."""
        with Horizontal(id="editor-header"):
            yield Label(f"📝 {Path(self.file_path).name}", id="editor-title")
            self.mode_indicator = Label("NORMAL", id="editor-mode-indicator")
            yield self.mode_indicator
        
        # VimTextArea for Vi/Vim editing
        self.editor = VimTextArea(
            text=self.content,
            language=self._detect_language(),
            id="file-textarea"
        )
        yield self.editor
        
        with Horizontal(id="editor-buttons"):
            yield Button("💾 Save", id="btn-save", variant="primary")
            yield Button("↶ Discard", id="btn-discard")
            self.ai_checkbox = Checkbox("🤖 AI Suggestions", id="btn-ai-suggestions")
            yield self.ai_checkbox
    
    def on_mount(self) -> None:
        """Setup after mount."""
        if self.editor:
            self.editor.focus()
            # Update initial mode display
            self._update_mode_indicator()
    
    def _get_code_assistant_app(self) -> "CodeAssistantApp":
        """Get the CodeAssistantApp widget from the screen."""
        # FileEditorPane is nested in LeftPanel -> CodeAssistantApp
        # CodeAssistantApp is on the current screen
        try:
            from kicli_code_assist.ui.app import CodeAssistantApp
            return self.screen.query_one(CodeAssistantApp)
        except Exception:
            raise RuntimeError("Could not find CodeAssistantApp in widget hierarchy")
    
    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checkbox value change directly via message."""
        if event.control.id == "btn-ai-suggestions":
            self.ai_suggestions_enabled = event.value
            # Log directly to app's chat display
            msg = f"[dim][AI] Checkbox {'checked' if event.value else 'unchecked'}[/]"
            code_app = self._get_code_assistant_app()
            code_app.chat_display.write(msg)
    
    def _update_mode_indicator(self) -> None:
        """Update mode indicator from current VimTextArea state.
        
        Called on mount and via ModeChanged messages from VimTextArea.
        """
        if not self.editor or not self.mode_indicator:
            return
        
        try:
            mode = "NORMAL"
            
            # Get mode from VimTextArea._vim_state
            if hasattr(self.editor, '_vim_state') and self.editor._vim_state:
                vim_mode = self.editor._vim_state.mode
                # Use .name property of Mode enum
                if hasattr(vim_mode, 'name'):
                    mode = vim_mode.name
                else:
                    mode = str(vim_mode).upper()
            
            # Create mode display with icon and background color
            mode_icons = {
                'NORMAL': '◆',
                'INSERT': '✏',
                'VISUAL': '▢',
                'VISUAL_LINE': '▬',
                'COMMAND': ':',
            }
            
            icon = mode_icons.get(mode, '●')
            
            # Use Textual color names that are definitely visible
            color_map = {
                'NORMAL': 'bright_cyan on navy_blue',
                'INSERT': 'bright_green on navy_blue',
                'VISUAL': 'bright_yellow on navy_blue',
                'VISUAL_LINE': 'bright_yellow on navy_blue',
                'COMMAND': 'bright_magenta on navy_blue',
            }
            
            style = color_map.get(mode, 'white on navy_blue')
            # Very visible: bold + color + background
            display_text = f"[{style} bold]{icon} {mode}[/{style} bold]"
            self.mode_indicator.update(display_text)
            self.vim_mode = mode
        except Exception:
            # Silently ignore errors during mode updates
            pass
    
    def on_vim_text_area_mode_changed(self, message: VimTextArea.ModeChanged) -> None:
        """Handle mode change events from VimTextArea."""
        self._update_mode_indicator()
    
    def on_vim_text_area_status_changed(self, message: VimTextArea.StatusChanged) -> None:
        """Handle status change events from VimTextArea.
        
        This is called on every vim keystroke, including in command mode.
        Use this to update any command-line indicator if needed.
        """
        # Status already shown in editor, just update mode if needed
        self._update_mode_indicator()
    
    def _detect_language(self) -> str:
        """Detect language from file extension."""
        path = Path(self.file_path)
        ext_map = {
            '.py': 'python',
            '.sh': 'bash',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'jsx',
            '.tsx': 'tsx',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.md': 'markdown',
            '.go': 'go',
            '.rs': 'rust',
            '.cpp': 'cpp',
            '.c': 'c',
            '.java': 'java',
        }
        return ext_map.get(path.suffix.lower(), 'text')
    
    def watch_is_dirty(self, is_dirty: bool) -> None:
        """Update title when dirty state changes."""
        if self.query_one("#editor-title", Label):
            label = self.query_one("#editor-title", Label)
            filename = Path(self.file_path).name
            label.update(f"📝 {filename}{'*' if is_dirty else ''}")
    
    def watch_ai_suggestions_enabled(self, enabled: bool) -> None:
        """Handle AI suggestions checkbox change."""
        code_app = self._get_code_assistant_app()
        if enabled and not self._ai_in_progress:
            self._ai_in_progress = True
            # Show feedback in Chat tab - direct write
            code_app.chat_display.write(f"[yellow][AI] Starting analysis of {Path(self.file_path).name}...[/]")
            # Show notification overlay
            self.app.notify(f"🤖 Analyzing code with AI...", timeout=5)
            # Trigger AI processing
            self.post_message(self._AISuggestionsRequested(self.file_path, self.editor.text))
        elif not enabled:
            # User unchecked
            self._ai_in_progress = False
            code_app.chat_display.write(f"[dim][AI] Analysis cancelled[/]")
    
    def on_text_area_changed(self) -> None:
        """Track content changes for dirty state and auto-save."""
        if self.editor:
            current_content = self.editor.text
            self.is_dirty = current_content != self._original_content
            
            # Schedule auto-save after 2 seconds of inactivity
            if self.is_dirty:
                # Cancel previous timer if exists
                if self._auto_save_timer:
                    self._auto_save_timer.stop()
                
                # Schedule new auto-save
                self._auto_save_timer = self.set_timer(2.0, lambda: self._do_auto_save())
    
    def action_save(self) -> bool:
        """Save file to disk.
        
        Returns:
            True if save successful, False otherwise
        """
        if not self.editor:
            return False
        
        # Cancel auto-save timer if running
        if self._auto_save_timer:
            self._auto_save_timer.stop()
            self._auto_save_timer = None
        
        try:
            Path(self.file_path).write_text(self.editor.text)
            self._original_content = self.editor.text
            self.is_dirty = False
            return True
        except Exception as e:
            self.app.notify(f"Error saving file: {e}", severity="error")
            return False
    
    def _do_auto_save(self) -> None:
        """Auto-save after inactivity."""
        if self.is_dirty:
            self.action_save()
            self.app.notify(f"💾 {Path(self.file_path).name} auto-saved", timeout=1)
    
    def action_discard(self) -> None:
        """Reload from disk and discard changes."""
        if self.editor:
            try:
                content = Path(self.file_path).read_text()
                self.editor.text = content
                self._original_content = content
                self.is_dirty = False
            except Exception as e:
                self.app.notify(f"Error loading file: {e}", severity="error")
    
    def apply_changes(self, new_content: str) -> None:
        """Apply AI-suggested changes to editor.
        
        Args:
            new_content: New file content with changes applied
        """
        if self.editor:
            self.editor.text = new_content
            self.is_dirty = True
        self._ai_in_progress = False
        if self.ai_checkbox:
            self.ai_checkbox.value = False
    
    def on_vim_text_area_save_requested(self, message: VimTextArea.SaveRequested) -> None:
        """Handle ':w' command from vim - disabled in favor of Ctrl+S button."""
        # :w saves are handled via button clicks instead
        pass
    
    def on_vim_text_area_quit_requested(self, message: VimTextArea.QuitRequested) -> None:
        """Handle ':q' command from vim.
        
        In a full vim-like app, this would close the editor tab.
        For now, we just save if dirty.
        """
        if self.is_dirty:
            self.action_save()
        # Could close tab here: self.parent.remove_child(self)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "btn-save":
            self.action_save()
        elif event.button.id == "btn-discard":
            self.action_discard()
    
    class _AISuggestionsRequested(Message):
        """Posted when AI suggestions are requested."""
        def __init__(self, file_path: str, content: str) -> None:
            self.file_path = file_path
            self.content = content
            super().__init__()

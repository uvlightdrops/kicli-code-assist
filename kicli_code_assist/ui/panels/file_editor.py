"""File editor pane with Vi/Vim editing support and syntax highlighting."""

from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.reactive import Reactive
from textual.widgets import Button, Label, Static, Checkbox
from textual.widget import Widget
from textual.message import Message
from textual_vim_textarea import VimTextArea


class FileEditorPane(Container):
    """Editable file content with Vi/Vim support, syntax highlighting, and dirty state tracking."""
    
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
    }
    
    FileEditorPane > #editor-header > Label {
        text-align: left;
        width: 1fr;
    }
    
    FileEditorPane > #editor-mode-indicator {
        width: 1fr;
        text-align: right;
        padding-right: 1;
    }
    
    FileEditorPane > #editor-buttons {
        height: 1;
        dock: bottom;
        background: $surface;
        border-top: solid $primary;
    }
    
    FileEditorPane > #editor-buttons > Button {
        margin: 0 1;
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
            # Start monitoring vim mode changes
            self.set_interval(0.1, self._update_vim_mode)
    
    def _update_vim_mode(self) -> None:
        """Update mode indicator based on VimTextArea state."""
        if self.editor and self.mode_indicator:
            # Get current mode from VimTextArea
            mode = "NORMAL"
            if hasattr(self.editor, '_vim_state'):
                vim_mode = self.editor._vim_state.mode
                mode_map = {
                    'normal': 'NORMAL',
                    'insert': 'INSERT',
                    'visual': 'VISUAL',
                    'command': 'COMMAND',
                }
                mode = mode_map.get(vim_mode, vim_mode.upper())
            
            # Color the mode indicator
            color_map = {
                'NORMAL': 'cyan',
                'INSERT': 'green',
                'VISUAL': 'yellow',
                'COMMAND': 'magenta',
            }
            color = color_map.get(mode, 'white')
            self.mode_indicator.update(f"[{color}]{mode}[/{color}]")
            self.vim_mode = mode
    
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
        if enabled and not self._ai_in_progress:
            self._ai_in_progress = True
            # Trigger AI processing
            self.app.post_message(self._AISuggestionsRequested(self.file_path, self.editor.text))
    
    def on_text_area_changed(self) -> None:
        """Track content changes for dirty state."""
        if self.editor:
            current_content = self.editor.text
            self.is_dirty = current_content != self._original_content
    
    def action_save(self) -> bool:
        """Save file to disk.
        
        Returns:
            True if save successful, False otherwise
        """
        if not self.editor:
            return False
        
        try:
            Path(self.file_path).write_text(self.editor.text)
            self._original_content = self.editor.text
            self.is_dirty = False
            return True
        except Exception as e:
            self.app.notify(f"Error saving file: {e}", severity="error")
            return False
    
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

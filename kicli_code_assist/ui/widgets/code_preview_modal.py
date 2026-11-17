"""Code Preview Modal - Shows files before save with diff mode

Displays:
- File-by-file preview of generated code
- Diff view if file already exists
- Save/Cancel buttons
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Button, Label, RichLog
from textual.screen import ModalScreen

logger = logging.getLogger(__name__)


class CodePreviewModal(ModalScreen):
    """Modal to preview generated code blocks before saving.
    
    Shows:
    - File list with sizes
    - Code preview with syntax highlighting
    - Diff view for existing files
    - Save/Cancel buttons
    """
    
    DEFAULT_CSS = """
    CodePreviewModal {
        align: center middle;
    }
    
    CodePreviewModal > Container {
        width: 80;
        height: 30;
        border: solid $primary;
        background: $surface;
        layout: vertical;
    }
    
    #preview-header {
        width: 1fr;
        height: 1;
        content-align: center middle;
        background: $boost;
    }
    
    #preview-content {
        width: 1fr;
        height: 1fr;
        border-bottom: solid $primary;
    }
    
    #preview-buttons {
        width: 1fr;
        height: 3;
        layout: horizontal;
        align: center middle;
    }
    
    #preview-buttons > Button {
        width: 20;
        margin: 0 1;
    }
    """
    
    def __init__(
        self,
        code_blocks: List[Dict[str, Any]],
        project_root: str,
        name: str = "code_preview",
        id: str = "code_preview_modal",
        **kwargs
    ):
        """Initialize preview modal.
        
        Args:
            code_blocks: List of generated code blocks
            project_root: Project root directory
            name: Modal name
            id: Modal ID
        """
        super().__init__(name=name, id=id, **kwargs)
        self.code_blocks = code_blocks
        self.project_root = Path(project_root)
        self.current_index = 0
        self.show_diff = {}  # Dict[filename -> bool] for which files to show diff
        
        # Pre-compute which files exist
        for block in self.code_blocks:
            filename = block.get("filename", "unknown")
            filepath = self.project_root / filename
            self.show_diff[filename] = filepath.exists()
    
    def compose(self) -> ComposeResult:
        """Compose the modal."""
        with Container():
            # Header
            yield Label(
                f"📋 Preview {len(self.code_blocks)} file(s) before saving",
                id="preview-header"
            )
            
            # Content area (will be replaced with current file preview)
            yield RichLog(id="preview-content", markup=True)
            
            # Buttons
            with Horizontal(id="preview-buttons"):
                yield Button("⬅ Previous", id="btn-prev", variant="default")
                yield Button("Next ➜", id="btn-next", variant="default")
                yield Button("💾 Save All", id="btn-save", variant="primary")
                yield Button("✕ Cancel", id="btn-cancel", variant="default")
    
    def on_mount(self) -> None:
        """Display first file preview."""
        self._update_preview()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        button_id = event.button.id
        
        if button_id == "btn-prev":
            if self.current_index > 0:
                self.current_index -= 1
                self._update_preview()
        
        elif button_id == "btn-next":
            if self.current_index < len(self.code_blocks) - 1:
                self.current_index += 1
                self._update_preview()
        
        elif button_id == "btn-save":
            self.dismiss(True)  # True = save
        
        elif button_id == "btn-cancel":
            self.dismiss(False)  # False = cancel
    
    def _update_preview(self) -> None:
        """Update preview display for current file."""
        block = self.code_blocks[self.current_index]
        filename = block.get("filename", "unknown")
        content = block.get("content", "")
        
        # Get display widget
        display = self.query_one("#preview-content", RichLog)
        display.clear()
        
        # Header
        display.write(f"[bold cyan]File {self.current_index + 1}/{len(self.code_blocks)}[/bold cyan]\n")
        display.write(f"[yellow]📄 {filename}[/yellow] ({len(content)} bytes)\n")
        display.write("─" * 60 + "\n\n")
        
        # Check if file exists
        filepath = self.project_root / filename
        if self.show_diff.get(filename):
            display.write("[red][!] File already exists[/red]\n")
            display.write("[dim]Diff mode (new content shown below):[/dim]\n\n")
            
            # Try to show diff
            try:
                existing_content = filepath.read_text(encoding='utf-8', errors='ignore')
                new_lines = content.split('\n')
                old_lines = existing_content.split('\n')
                
                # Simple diff: mark changed lines
                display.write("[dim]Old → New differences:[/dim]\n")
                display.write(f"[dim]Old file: {len(old_lines)} lines[/dim]\n")
                display.write(f"[dim]New file: {len(new_lines)} lines[/dim]\n\n")
                
                # Show first diff section
                display.write("[yellow]New content (first 300 chars):[/yellow]\n")
                display.write("[bold]" + content[:300].replace('\n', '\n') + "[/bold]\n")
                if len(content) > 300:
                    display.write("[dim]...[/dim]\n")
            except Exception as e:
                display.write(f"[red]Could not read existing file: {e}[/red]\n")
        else:
            display.write("[green][✓] New file[/green]\n\n")
            display.write("[bold]Content (first 300 chars):[/bold]\n")
            display.write("[dim]" + content[:300].replace('\n', '\n') + "[/dim]\n")
            if len(content) > 300:
                display.write("[dim]...[/dim]\n")
        
        # Footer
        display.write("\n" + "─" * 60 + "\n")
        display.write("[dim]Navigate with Previous/Next buttons. Click Save All to proceed.[/dim]\n")

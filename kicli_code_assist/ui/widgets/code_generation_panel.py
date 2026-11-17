"""Code Generation Chat Panel - Phase I3

Chat interface for generating code in empty projects.
User types requirements → Agent generates code iteratively.

Layout:
- Top: Chat display (RichLog)
- Bottom: Input field + Send button
"""

import logging
from typing import Optional
from pathlib import Path
from textual.widgets import Static, RichLog, Button
from textual.containers import Vertical, Horizontal
from textual.app import ComposeResult
from textual import work

from ..panels.chat_display import SelectableRichLog
from ..input.chat_input import ChatInput

logger = logging.getLogger(__name__)


class CodeGenerationPanel(Static):
    """Chat panel for code generation.
    
    Allows user to:
    1. Describe what code to generate
    2. See generated code in chat
    3. Ask for refinements
    """
    
    DEFAULT_CSS = """
    CodeGenerationPanel {
        width: 1fr;
        height: 1fr;
        border: solid $primary;
        background: $surface;
        layout: vertical;
    }
    
    CodeGenerationPanel > Vertical {
        width: 1fr;
        height: 1fr;
        layout: vertical;
    }
    
    #code-gen-display {
        width: 1fr;
        height: 1fr;
        border: none;
    }
    
    #code-gen-input-container {
        width: 1fr;
        height: 6;
        border-top: solid $primary;
        background: $boost;
        layout: vertical;
    }
    
    #code-gen-input-container > Horizontal {
        width: 1fr;
        height: auto;
        layout: horizontal;
    }
    
    #code-gen-input-container > Horizontal > ChatInput {
        width: 1fr;
        height: 3;
    }
    
    #code-gen-send-btn {
        width: 12;
        height: auto;
        margin: 0 1;
    }
    
    #code-gen-save-btn {
        width: 12;
        height: auto;
        margin: 0 1;
    }
    """
    
    def __init__(self, project_root: Optional[str] = None, **kwargs):
        """Initialize code generation panel.
        
        Args:
            project_root: Root directory for code generation
        """
        super().__init__(**kwargs)
        self.project_root = project_root or str(Path.cwd())
        self.chat_display: Optional[SelectableRichLog] = None
        self.input_field: Optional[ChatInput] = None
        self.is_generating = False
        self.conversation_id: Optional[str] = None
        self.backend_client = None
    
    def compose(self) -> ComposeResult:
        """Compose the panel."""
        with Vertical():
            # Chat display
            self.chat_display = SelectableRichLog(
                highlight=False, 
                markup=True,
                id="code-gen-display"
            )
            yield self.chat_display
            
            # Input area with Send button
            with Vertical(id="code-gen-input-container"):
                with Horizontal():
                    self.input_field = ChatInput(
                        self, 
                        id="code-gen-input", 
                        language="markdown",
                        on_send_callback=self._on_send_message
                    )
                    yield self.input_field
                    
                    # Send button
                    yield Button("↵ Send", id="code-gen-send-btn", variant="primary")
                    
                    # Save button
                    yield Button("💾 Save", id="code-gen-save-btn", variant="success")
    
    def on_mount(self) -> None:
        """Setup after mount."""
        from ..http_client import get_backend_client
        self.backend_client = get_backend_client()
        
        # Show welcome message
        welcome = """[bold cyan]🤖 Code Generation Assistant[/bold cyan]

Describe what code you want to generate. You can:
- Request new files or modules
- Ask for refinements
- Add features iteratively

Example: "Create a Python FastAPI server with a health check endpoint"
"""
        self.chat_display.write(welcome)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "code-gen-send-btn":
            # Trigger send on input field
            if self.input_field:
                self.input_field.send_message()
        elif event.button.id == "code-gen-save-btn":
            # Trigger save
            self._save_code()
    
    def _on_send_message(self, message: str) -> None:
        """Handle message send from input.
        
        Args:
            message: User message
        """
        if not message.strip():
            return
        
        if self.is_generating:
            self.chat_display.write("[yellow]⏳ Generation in progress...[/yellow]\n")
            return
        
        # Add user message to display
        self.chat_display.write(f"[green]You:[/green] {message}\n")
        
        # Trigger async generation
        self.is_generating = True
        self._generate_code(message)
    
    @work(thread=False)
    async def _generate_code(self, message: str) -> None:
        """Generate code based on user message.
        
        Args:
            message: User requirement description
        """
        try:
            # Call backend /api/code/generate
            response = self.backend_client.generate_code(
                message=message,
                project_root=self.project_root,
                conversation_id=self.conversation_id
            )
            
            if response.get("success"):
                # Store conversation ID for multi-turn
                self.conversation_id = response.get("conversation_id")
                
                # Display agent response
                agent_response = response.get("response", "No response")
                self.chat_display.write(f"[cyan]Agent:[/cyan] {agent_response}\n")
                
                # Display code blocks if any
                code_blocks = response.get("code_blocks", [])
                if code_blocks:
                    self.chat_display.write("[bold]Generated Code:[/bold]\n")
                    for block in code_blocks:
                        filename = block.get("filename", "unknown.py")
                        content = block.get("content", "")
                        self.chat_display.write(f"[yellow]📄 {filename}[/yellow]\n")
                        self.chat_display.write(f"[dim]{content[:200]}...[/dim]\n\n")
            else:
                error = response.get("error", "Unknown error")
                self.chat_display.write(f"[red]❌ Error: {error}[/red]\n")
        
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            self.chat_display.write(f"[red]❌ Error: {e}[/red]\n")
        finally:
            self.is_generating = False
    
    def _save_code(self) -> None:
        """Save generated code to files.
        
        Calls POST /api/code/save with current conversation_id.
        First attempt ohne overwrite, dann mit overwrite=true falls Files existieren.
        """
        if not self.conversation_id:
            self.chat_display.write("[yellow]⚠️  No code generated yet. Generate code first.[/yellow]\n")
            return
        
        try:
            self.chat_display.write("[cyan]💾 Saving code files...[/cyan]\n")
            
            # First attempt: try without overwrite
            response = self.backend_client.save_code(
                conversation_id=self.conversation_id,
                project_root=self.project_root,
                overwrite=False
            )
            
            # If files exist, ask to overwrite
            if not response.get("success") and response.get("errors"):
                errors = response.get("errors", [])
                if any("already exists" in err for err in errors):
                    self.chat_display.write("[yellow]⚠️  Some files exist. Overwriting...[/yellow]\n")
                    # Retry with overwrite
                    response = self.backend_client.save_code(
                        conversation_id=self.conversation_id,
                        project_root=self.project_root,
                        overwrite=True
                    )
            
            # Display results
            if response.get("success") or response.get("written", 0) > 0:
                written = response.get("written", 0)
                total = response.get("total", 0)
                files = response.get("files", [])
                
                self.chat_display.write(f"[green]✅ Saved {written}/{total} files[/green]\n")
                
                for file_result in files:
                    if file_result.get("success"):
                        filepath = file_result.get("filepath", "")
                        size = file_result.get("size", 0)
                        filename = file_result.get("filename", "")
                        self.chat_display.write(f"  [green]✓[/green] {filename} ({size} bytes)\n")
                    else:
                        filename = file_result.get("filename", "")
                        error = file_result.get("error", "Unknown error")
                        self.chat_display.write(f"  [red]✗[/red] {filename}: {error}\n")
            else:
                error = response.get("error", "Unknown error")
                self.chat_display.write(f"[red]❌ Save failed: {error}[/red]\n")
        
        except Exception as e:
            logger.error(f"Save failed: {e}")
            self.chat_display.write(f"[red]❌ Save error: {e}[/red]\n")

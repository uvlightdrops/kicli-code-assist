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
from .conversation_browser_modal import ConversationBrowserModal
from .debug_modal import DebugModal

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
        self.last_code_blocks: list = []  # Store code blocks from last generation
    
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
                    
                    # History button
                    yield Button("📋 History", id="code-gen-history-btn", variant="default")
    
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
        elif event.button.id == "code-gen-history-btn":
            # Show conversation history browser
            self._show_history_browser()
    
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
                self.chat_display.write(f"[cyan]Agent:[/cyan]\n")
                # Truncate very long responses but keep format
                display_response = agent_response
                if len(display_response) > 500:
                    # Find last newline before 500 chars
                    display_response = agent_response[:500]
                    last_newline = display_response.rfind('\n')
                    if last_newline > 0:
                        display_response = agent_response[:last_newline]
                    display_response += "\n[dim]...[/dim]"
                self.chat_display.write(f"{display_response}\n")
                
                # Display code blocks if any
                code_blocks = response.get("code_blocks", [])
                self.last_code_blocks = code_blocks  # Store for save operation
                
                if code_blocks:
                    # Show summary
                    total_size = sum(len(block.get("content", "")) for block in code_blocks)
                    self.chat_display.write(f"\n[bold cyan]📁 Generated {len(code_blocks)} file(s) ({total_size} bytes total):[/bold cyan]\n")
                    
                    # List each file
                    for i, block in enumerate(code_blocks, 1):
                        filename = block.get("filename", "unknown.py")
                        content = block.get("content", "")
                        file_size = len(content)
                        
                        # Show file info
                        self.chat_display.write(f"\n  [{i}] [yellow]📄 {filename}[/yellow] ({file_size} bytes)\n")
                        
                        # Show preview (first 150 chars)
                        preview = content[:150].replace('\n', ' ')
                        if len(content) > 150:
                            preview += "..."
                        self.chat_display.write(f"      [dim]{preview}[/dim]\n")
            else:
                error = response.get("error", "Unknown error")
                self.chat_display.write(f"[red]❌ Error: {error}[/red]\n")
        
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            self.chat_display.write(f"[red]❌ Error: {e}[/red]\n")
        finally:
            self.is_generating = False
    
    def _debug_widget_tree(self) -> str:
        """Debug: show widget tree structure."""
        lines = []
        try:
            # Show all widgets on screen
            from kicli_code_assist.ui.panels.tabbed_editor_pane import TabbedEditorPane
            from kicli_code_assist.ui.app import CodeAssistantApp
            from kicli_code_assist.ui.panels.left_panel import LeftPanel
            
            all_widgets = self.screen.query("*")
            tabbedpane_widgets = self.screen.query("TabbedEditorPane")
            codeassistant_widgets = self.screen.query(CodeAssistantApp)
            left_panels = self.screen.query(LeftPanel)
            
            lines.append(f"Total widgets: {len(all_widgets)}")
            lines.append(f"CodeAssistantApp count: {len(codeassistant_widgets)}")
            lines.append(f"LeftPanel count: {len(left_panels)}")
            lines.append(f"TabbedEditorPane count: {len(tabbedpane_widgets)}")
            
            if left_panels:
                for i, lp in enumerate(left_panels):
                    lines.append(f"\n  LeftPanel[{i}]:")
                    lines.append(f"    tabbed_content: {lp.tabbed_content}")
            
            # Show hierarchy
            lines.append("\nWidget types on screen:")
            widget_types = {}
            for w in all_widgets:
                wtype = type(w).__name__
                widget_types[wtype] = widget_types.get(wtype, 0) + 1
            for wtype, count in sorted(widget_types.items())[:15]:
                lines.append(f"  {wtype}: {count}")
                
        except Exception as ex:
            lines.append(f"Debug error: {ex}")
        
        return "\n".join(lines)
    
    def _save_code(self) -> None:
        """Save generated code to files.
        
        Shows preview modal first, then saves with auto-retry on conflict.
        """
        if not self.conversation_id:
            self.chat_display.write("[yellow]⚠️  No code generated yet. Generate code first.[/yellow]\n")
            return
        
        if not self.last_code_blocks:
            self.chat_display.write("[yellow]⚠️  No code blocks to save.[/yellow]\n")
            return
        
        # Get tabbed editor from widget hierarchy using screen query
        try:
            # Query up the widget tree to find TabbedEditorPane
            from kicli_code_assist.ui.panels.tabbed_editor_pane import TabbedEditorPane
            tabbed_editor = self.screen.query_one(TabbedEditorPane, expect_type=TabbedEditorPane)
        except Exception as e:
            # Diagnostic info with modal
            debug_msg = f"""Error: {type(e).__name__}: {e}

Screen: {self.screen}
Screen ID: {self.screen.id if hasattr(self.screen, 'id') else 'N/A'}
Parent: {self.parent}

Available widgets:
{self._debug_widget_tree()}"""
            
            # Show in debug modal
            modal = DebugModal(
                title="Editor Not Available - Debug Info",
                content=debug_msg
            )
            self.app.push_screen(modal)
            return
        
        # Add each code block as a tab
        for block in self.last_code_blocks:
            filepath = block.get('filepath', 'unknown')
            content = block.get('content', '')
            
            # Determine status: new or modified
            status = "new"  # Could check if file exists in project
            
            # Add to tabbed editor
            tabbed_editor.add_file_tab(
                filepath=filepath,
                content=content,
                status=status
            )
            self.chat_display.write(f"[cyan]📄 Added: {filepath}[/cyan]\n")
        
        # Trigger auto-save via agent
        self._do_save_code()
    
    def _do_save_code(self) -> None:
        """Actually save code to files (called after preview modal).
        
        Implements auto-retry logic for file conflicts.
        """
        try:
            self.chat_display.write("[cyan]💾 Saving code files...[/cyan]\n")
            
            # First attempt: try without overwrite
            response = self.backend_client.save_code(
                conversation_id=self.conversation_id,
                project_root=self.project_root,
                code_blocks=self.last_code_blocks,
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
                        code_blocks=self.last_code_blocks,
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
                
                # Refresh FileTree to show newly saved files
                self._refresh_file_tree()
            else:
                error = response.get("error", "Unknown error")
                self.chat_display.write(f"[red]❌ Save failed: {error}[/red]\n")
        
        except Exception as e:
            logger.error(f"Save failed: {e}")
            self.chat_display.write(f"[red]❌ Save error: {e}[/red]\n")
    
    def _show_history_browser(self) -> None:
        """Show conversation history browser modal.
        
        Fetches list of past conversations and shows browser.
        When user selects one, loads it for continued editing.
        """
        try:
            self.chat_display.write("[cyan]📋 Loading conversation history...[/cyan]\n")
            
            # Fetch conversations from backend
            response = self.backend_client.list_conversations(project_root=self.project_root)
            
            if not response.get("success"):
                error = response.get("error", "Failed to load history")
                self.chat_display.write(f"[red]❌ Error: {error}[/red]\n")
                return
            
            conversations = response.get("conversations", [])
            
            if not conversations:
                self.chat_display.write("[yellow]⚠️  No conversation history yet.[/yellow]\n")
                return
            
            self.chat_display.write(f"[cyan]Found {len(conversations)} conversation(s).[/cyan]\n")
            
            # Show browser modal
            def _handle_browser_response(result) -> None:
                """Callback when browser modal closes."""
                if result:
                    if isinstance(result, dict) and result.get("action") == "delete":
                        # Handle delete
                        self._delete_conversation(result["conversation"])
                    else:
                        # Load selected conversation
                        self._load_conversation(result)
            
            modal = ConversationBrowserModal(conversations=conversations)
            self.app.push_screen(modal, callback=_handle_browser_response)
        
        except Exception as e:
            logger.error(f"Show history browser failed: {e}")
            self.chat_display.write(f"[red]❌ Error: {e}[/red]\n")
    
    def _load_conversation(self, conversation: dict) -> None:
        """Load a saved conversation for continued editing.
        
        Args:
            conversation: Conversation metadata dict
        """
        try:
            conversation_id = conversation.get("conversation_id")
            self.conversation_id = conversation_id
            
            self.chat_display.write(f"\n[cyan]📂 Loaded conversation: {conversation_id[:8]}[/cyan]\n")
            self.chat_display.write(f"[dim]Created: {conversation.get('created_at', 'unknown')}[/dim]\n")
            self.chat_display.write(f"[dim]Messages: {conversation.get('message_count', 0)}[/dim]\n")
            self.chat_display.write("[cyan]You can now continue generating or refining code...[/cyan]\n\n")
        
        except Exception as e:
            logger.error(f"Load conversation failed: {e}")
            self.chat_display.write(f"[red]❌ Error loading conversation: {e}[/red]\n")
    
    def _delete_conversation(self, conversation: dict) -> None:
        """Delete a conversation from history.
        
        Args:
            conversation: Conversation metadata dict
        """
        try:
            conversation_id = conversation.get("conversation_id")
            
            # Call backend to delete
            # (This would need a DELETE endpoint, for now just info message)
            self.chat_display.write(f"[yellow]🗑️  To delete: {conversation_id[:8]}[/yellow]\n")
            self.chat_display.write("[dim](Delete functionality can be added later)[/dim]\n")
        
        except Exception as e:
            logger.error(f"Delete conversation failed: {e}")
            self.chat_display.write(f"[red]❌ Error: {e}[/red]\n")
    
    def _refresh_file_tree(self) -> None:
        """Refresh FileTree to show newly saved files."""
        try:
            # Find FileTree widget anywhere on screen
            from .file_browser import FileTree
            
            file_trees = self.screen.query(FileTree)
            if file_trees:
                file_tree = file_trees.first()
                file_tree.scan_project()
                logger.info("FileTree refreshed after save")
            else:
                logger.debug("FileTree not found on screen")
        except Exception as e:
            logger.warning(f"Could not refresh FileTree: {e}")

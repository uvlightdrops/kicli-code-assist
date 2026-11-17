"""Conversation History Browser Modal - Browse and load past conversations

Displays:
- List of all saved conversations
- Metadata: created_at, updated_at, message_count
- Select to load and continue editing
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Button, Label, ListItem, ListView
from textual.screen import ModalScreen

logger = logging.getLogger(__name__)


class ConversationListItem(ListItem):
    """Single conversation item in the list."""
    
    def __init__(self, conversation: Dict[str, Any], id: str = None, **kwargs):
        """Initialize list item.
        
        Args:
            conversation: Conversation metadata dict
            id: Optional item ID
        """
        self.conversation = conversation
        conv_id = conversation.get("conversation_id", "unknown")[:8]
        created = conversation.get("created_at", "unknown")[:10]
        msg_count = conversation.get("message_count", 0)
        project = conversation.get("project_path", "unknown").split("/")[-1]
        
        # Format: ID | Created | Messages | Project
        label = f"[cyan]{conv_id}[/cyan] | {created} | {msg_count} msgs | {project}"
        
        # Prefix ID with 'conv-' to avoid starting with a number
        item_id = id or f"conv-{conv_id}"
        super().__init__(Label(label), id=item_id, **kwargs)


class ConversationBrowserModal(ModalScreen):
    """Modal to browse and load past conversations."""
    
    DEFAULT_CSS = """
    ConversationBrowserModal {
        align: center middle;
    }
    
    ConversationBrowserModal > Container {
        width: 100;
        height: 32;
        border: solid $primary;
        background: $surface;
        layout: vertical;
    }
    
    #browser-header {
        width: 1fr;
        height: 1;
        content-align: center middle;
        background: $boost;
    }
    
    #browser-list {
        width: 1fr;
        height: 1fr;
        border-bottom: solid $primary;
    }
    
    #browser-buttons {
        width: 1fr;
        height: 3;
        layout: horizontal;
        align: center middle;
    }
    
    #browser-buttons > Button {
        width: 20;
        margin: 0 1;
    }
    
    #browser-info {
        width: 1fr;
        height: auto;
        background: $boost;
        padding: 0 1;
        content-align: left middle;
    }
    """
    
    def __init__(
        self,
        conversations: List[Dict[str, Any]],
        name: str = "conversation_browser",
        id: str = "conversation_browser_modal",
        **kwargs
    ):
        """Initialize browser modal.
        
        Args:
            conversations: List of conversation metadata
            name: Modal name
            id: Modal ID
        """
        super().__init__(name=name, id=id, **kwargs)
        self.conversations = conversations
        self.selected_conversation: Optional[Dict[str, Any]] = None
    
    def compose(self) -> ComposeResult:
        """Compose the modal."""
        with Container():
            # Header
            yield Label(
                f"📋 Browse {len(self.conversations)} conversation(s)",
                id="browser-header"
            )
            
            # List view
            list_view = ListView(id="browser-list")
            for conv in self.conversations:
                list_view.append(ConversationListItem(conv))
            yield list_view
            
            # Info line
            yield Label(
                "[dim]Select a conversation and click Load to continue editing[/dim]",
                id="browser-info"
            )
            
            # Buttons
            with Horizontal(id="browser-buttons"):
                yield Button("📂 Load", id="btn-load", variant="primary")
                yield Button("🗑️  Delete", id="btn-delete", variant="warning")
                yield Button("✕ Cancel", id="btn-cancel", variant="default")
    
    def on_mount(self) -> None:
        """Select first item by default."""
        list_view = self.query_one("#browser-list", ListView)
        if len(list_view) > 0:
            list_view.index = 0
            self._update_selection()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        button_id = event.button.id
        
        if button_id == "btn-load":
            # Get selected conversation
            list_view = self.query_one("#browser-list", ListView)
            if list_view.index >= 0:
                selected_item = list_view.children[list_view.index]
                if isinstance(selected_item, ConversationListItem):
                    self.selected_conversation = selected_item.conversation
                    self.dismiss(self.selected_conversation)  # Return selected conversation
            else:
                self.dismiss(None)  # No selection
        
        elif button_id == "btn-delete":
            # Return with delete flag
            list_view = self.query_one("#browser-list", ListView)
            if list_view.index >= 0:
                selected_item = list_view.children[list_view.index]
                if isinstance(selected_item, ConversationListItem):
                    self.selected_conversation = selected_item.conversation
                    # Mark for deletion by returning negative (hack: we'll handle in callback)
                    self.dismiss({"action": "delete", "conversation": self.selected_conversation})
            else:
                self.dismiss(None)
        
        elif button_id == "btn-cancel":
            self.dismiss(None)
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Update when selection changes."""
        self._update_selection()
    
    def _update_selection(self) -> None:
        """Update info display for selected item."""
        list_view = self.query_one("#browser-list", ListView)
        if list_view.index >= 0 and list_view.index < len(self.conversations):
            selected = self.conversations[list_view.index]
            info_line = self.query_one("#browser-info", Label)
            
            msg_count = selected.get("message_count", 0)
            updated = selected.get("updated_at", "unknown")
            info_line.update(
                f"[cyan]{selected.get('conversation_id', 'unknown')[:8]}[/cyan] | "
                f"Last updated: {updated} | {msg_count} messages in conversation"
            )

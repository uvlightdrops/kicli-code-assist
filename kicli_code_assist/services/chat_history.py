"""Chat History Service - Persistent conversation storage

Manages:
- Conversation persistence (JSON files)
- Message tracking (user + assistant)
- File generation tracking (what was saved where)
- History browsing and filtering
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from uuid import uuid4

logger = logging.getLogger(__name__)


class ChatHistoryManager:
    """Manages persistent chat conversation history"""
    
    def __init__(self, storage_root: str = None):
        """Initialize chat history manager
        
        Args:
            storage_root: Base directory for storing chat history
                         Defaults to ~/.dev_data/kicli-code-assist/chat-history/
        """
        if storage_root is None:
            storage_root = Path.home() / "dev_data" / "kicli-code-assist" / "chat-history"
        
        self.storage_root = Path(storage_root).resolve()
        self.storage_root.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"ChatHistoryManager initialized at {self.storage_root}")
    
    def _get_conversation_path(self, conversation_id: str) -> Path:
        """Get file path for conversation
        
        Args:
            conversation_id: Unique conversation ID
            
        Returns:
            Path to conversation JSON file
        """
        return self.storage_root / f"{conversation_id}.json"
    
    def create_conversation(self, project_path: str) -> str:
        """Create new conversation
        
        Args:
            project_path: Path to project being worked on
            
        Returns:
            conversation_id (UUID)
        """
        conversation_id = str(uuid4())
        
        conversation = {
            "conversation_id": conversation_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "project_path": project_path,
            "messages": []
        }
        
        self._save_conversation(conversation_id, conversation)
        logger.info(f"Created conversation {conversation_id} for project {project_path}")
        
        return conversation_id
    
    def add_message(
        self,
        conversation_id: str,
        role: str,  # "user" or "assistant"
        content: str,
        files_generated: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """Add message to conversation
        
        Args:
            conversation_id: ID of conversation
            role: "user" or "assistant"
            content: Message content
            files_generated: List of generated files (for assistant messages)
                           Each file dict: {filename, size, saved, saved_path}
        """
        conversation = self.load_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation not found: {conversation_id}")
        
        message = {
            "id": f"msg-{len(conversation['messages']) + 1:03d}",
            "role": role,
            "timestamp": datetime.now().isoformat(),
            "content": content
        }
        
        if files_generated:
            message["files_generated"] = files_generated
        
        conversation["messages"].append(message)
        conversation["updated_at"] = datetime.now().isoformat()
        
        self._save_conversation(conversation_id, conversation)
        logger.debug(f"Added {role} message to conversation {conversation_id}")
    
    def load_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Load conversation from disk
        
        Args:
            conversation_id: ID of conversation
            
        Returns:
            Conversation dict or None if not found
        """
        filepath = self._get_conversation_path(conversation_id)
        
        if not filepath.exists():
            logger.warning(f"Conversation not found: {conversation_id}")
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load conversation {conversation_id}: {e}")
            return None
    
    def _save_conversation(self, conversation_id: str, conversation: Dict[str, Any]) -> None:
        """Save conversation to disk
        
        Args:
            conversation_id: ID of conversation
            conversation: Conversation dict to save
        """
        filepath = self._get_conversation_path(conversation_id)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(conversation, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save conversation {conversation_id}: {e}")
            raise
    
    def list_conversations(self, project_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all conversations, optionally filtered by project
        
        Args:
            project_path: If provided, filter to this project only
            
        Returns:
            List of conversation metadata (without full message history)
        """
        conversations = []
        
        for json_file in self.storage_root.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    conv = json.load(f)
                
                if project_path and conv.get("project_path") != project_path:
                    continue
                
                # Return metadata only (not full messages)
                conversations.append({
                    "conversation_id": conv["conversation_id"],
                    "created_at": conv["created_at"],
                    "updated_at": conv["updated_at"],
                    "project_path": conv["project_path"],
                    "message_count": len(conv.get("messages", []))
                })
            except Exception as e:
                logger.warning(f"Failed to read conversation file {json_file}: {e}")
        
        # Sort by updated_at (most recent first)
        conversations.sort(key=lambda x: x["updated_at"], reverse=True)
        return conversations
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation from storage
        
        Args:
            conversation_id: ID of conversation
            
        Returns:
            True if deleted, False if not found
        """
        filepath = self._get_conversation_path(conversation_id)
        
        if not filepath.exists():
            return False
        
        try:
            filepath.unlink()
            logger.info(f"Deleted conversation {conversation_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete conversation {conversation_id}: {e}")
            return False

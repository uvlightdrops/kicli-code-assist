"""Chat session management with project context integration."""

import os
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime

from ki_core import Config
from kicli_code_assist.context import ProjectContextManager, ProjectInfo
from kicli_code_assist.chat_history import ChatHistory
from kicli_code_assist.prompts import SystemPrompts, PromptRole


@dataclass
class ChatMessage:
    """Single chat message with metadata."""

    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    project_context_included: bool = False

    def to_dict(self):
        """Convert to dict for LLM API."""
        return {"role": self.role, "content": self.content}


class ChatSession:
    """Manages chat session with project context awareness."""

    def __init__(self, project_root: Optional[str] = None, session_name: str = "default", role: PromptRole | str = PromptRole.CODE_ASSISTANT):
        """Initialize chat session.

        Args:
            project_root: Root directory to analyze. Defaults to current directory.
            session_name: Name for this chat session (for persistence)
            role: LLM role/persona (code_assistant, architect, debugger, etc.)
        """
        self.project_root = project_root or os.getcwd()
        self.config = Config.from_env()
        self.messages: list[ChatMessage] = []
        self.project_info: Optional[ProjectInfo] = None
        self.context_loaded = False
        self.session_name = session_name
        self.role = role if isinstance(role, PromptRole) else PromptRole(role)

        # Initialize context manager
        self.context_manager = ProjectContextManager(self.project_root)
        
        # Initialize chat history (persistence)
        self.history = ChatHistory(session_name)
        self.messages = [ChatMessage(role=msg["role"], content=msg["content"]) for msg in self.history.messages]

    def load_project_context(self, force_reload: bool = False) -> ProjectInfo:
        """Load and analyze project context.

        Args:
            force_reload: If True, ignore cached context and re-scan.

        Returns:
            ProjectInfo object with complete project analysis.
        """
        if self.project_info and not force_reload:
            return self.project_info

        self.project_info = self.context_manager.build_context()
        self.context_loaded = True
        return self.project_info

    def get_system_prompt(self) -> str:
        """Generate system prompt using configured role and project context.

        Returns:
            System prompt string for LLM.
        """
        project_context = ""
        if self.context_loaded and self.project_info:
            project_context = self.project_info.to_context_string(max_tokens=3000)

        return SystemPrompts.get_prompt(self.role, project_context)

    def add_message(self, role: str, content: str, include_context: bool = False) -> ChatMessage:
        """Add message to chat history and persist to disk.

        Args:
            role: "user" or "assistant"
            content: Message content
            include_context: If True, project context is included with this message

        Returns:
            The ChatMessage that was added.
        """
        message = ChatMessage(role=role, content=content, project_context_included=include_context)
        self.messages.append(message)
        
        # Persist to disk
        metadata = {"context_included": include_context} if include_context else None
        self.history.add_message(role, content, metadata)
        
        return message

    def get_messages_for_api(self) -> list[dict]:
        """Get messages in format ready for LLM API.

        Returns:
            List of {"role": ..., "content": ...} dicts.
        """
        # Add system prompt
        api_messages = [{"role": "system", "content": self.get_system_prompt()}]

        # Add conversation history
        for msg in self.messages:
            api_messages.append(msg.to_dict())

        return api_messages

    def get_summary(self) -> str:
        """Get summary of chat session.

        Returns:
            Summary string with message count and context status.
        """
        context_status = "✓ Loaded" if self.context_loaded else "✗ Not loaded"
        return (
            f"Chat Session Summary:\n"
            f"  Messages: {len(self.messages)}\n"
            f"  Project Context: {context_status}\n"
            f"  Project: {self.project_info.name if self.project_info else 'unknown'}\n"
            f"  Language: {self.project_info.language if self.project_info else 'unknown'}"
        )

    def get_context_status(self) -> str:
        """Get readable status of project context.

        Returns:
            Status string like "📊 23 files, 82.1 KB loaded"
        """
        if not self.context_loaded or not self.project_info:
            return "❌ No context loaded"

        files = self.project_info.total_files
        size_kb = self.project_info.total_size / 1024
        return f"📊 {files} files, {size_kb:.1f} KB loaded"

    def clear_context(self):
        """Clear loaded project context."""
        self.project_info = None
        self.context_loaded = False

    def clear_history(self):
        """Clear chat message history (local and persistent)."""
        self.messages = []
        self.history.clear()

    def set_role(self, role: PromptRole | str) -> None:
        """Change the LLM role/persona for this session.
        
        Args:
            role: New role (code_assistant, architect, debugger, etc.)
        """
        self.role = role if isinstance(role, PromptRole) else PromptRole(role)

    @staticmethod
    def list_sessions() -> list[dict]:
        """List all available chat sessions.
        
        Returns:
            List of session info dicts
        """
        return ChatHistory.list_sessions()

    @staticmethod
    def load_session(session_name: str, project_root: Optional[str] = None) -> "ChatSession":
        """Load an existing chat session.
        
        Args:
            session_name: Name of session to load
            project_root: Optional project root
            
        Returns:
            New ChatSession instance with loaded history
        """
        session = ChatSession(project_root, session_name)
        return session

    def export_session(self, format_type: str = "markdown") -> str:
        """Export this session to string format.
        
        Args:
            format_type: "json" or "markdown"
            
        Returns:
            Formatted session content
        """
        return self.history.export_session(self.session_name, format_type)

    def __repr__(self) -> str:
        """String representation."""
        return f"ChatSession(project={self.project_info.name if self.project_info else 'unknown'}, messages={len(self.messages)})"

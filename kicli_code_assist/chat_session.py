"""Chat session management with project context integration."""

import os
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime

from ki_core import Config
from kicli_code_assist.context import ProjectContextManager, ProjectInfo


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

    def __init__(self, project_root: Optional[str] = None):
        """Initialize chat session.

        Args:
            project_root: Root directory to analyze. Defaults to current directory.
        """
        self.project_root = project_root or os.getcwd()
        self.config = Config.from_env()
        self.messages: list[ChatMessage] = []
        self.project_info: Optional[ProjectInfo] = None
        self.context_loaded = False

        # Initialize context manager
        self.context_manager = ProjectContextManager(self.project_root)

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
        """Generate system prompt with or without project context.

        Returns:
            System prompt string for LLM.
        """
        base_prompt = (
            "You are a helpful code assistant. Answer questions clearly and concisely. "
            "Provide code examples when relevant. Ask for clarification if needed."
        )

        if not self.context_loaded or not self.project_info:
            return base_prompt

        # Build project context part
        project_context = self.project_info.to_context_string(max_tokens=3000)

        return f"""{base_prompt}

# PROJECT CONTEXT

You are assisting with the following project:

{project_context}

Use this project context to provide relevant and accurate answers to the user's questions."""

    def add_message(self, role: str, content: str, include_context: bool = False) -> ChatMessage:
        """Add message to chat history.

        Args:
            role: "user" or "assistant"
            content: Message content
            include_context: If True, project context is included with this message

        Returns:
            The ChatMessage that was added.
        """
        message = ChatMessage(role=role, content=content, project_context_included=include_context)
        self.messages.append(message)
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
        """Clear chat message history."""
        self.messages = []

    def __repr__(self) -> str:
        """String representation."""
        return f"ChatSession(project={self.project_info.name if self.project_info else 'unknown'}, messages={len(self.messages)})"

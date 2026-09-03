"""Chat history persistence and session management."""

import json
from datetime import datetime
from pathlib import Path

from ki_core import Config


def get_cache_dir() -> Path:
    """Get the cache directory for kicli-code-assist from ki-core Config.
    
    Returns:
        Path to cache directory from config, or default: $HOME/dev_data/kicli-code-assist/
    """
    config = Config.from_env()
    
    # Get cache dir from config, with fallback
    cache_dir_str = config.kicli_cache_dir or os.path.expanduser("~/dev_data/kicli-code-assist")
    cache_dir = Path(cache_dir_str).expanduser()
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_chat_history_dir() -> Path:
    """Get the chat history directory from ki-core Config.
    
    Returns:
        Path to chat history directory, or default: $cache_dir/chat_history/
    """
    config = Config.from_env()

    # Older ki-core builds may not expose this field yet.
    chat_history_dir = getattr(config, "kicli_chat_history_dir", "")
    if chat_history_dir:
        history_dir = Path(chat_history_dir).expanduser()
    else:
        history_dir = get_cache_dir() / "chat_history"

    history_dir.mkdir(parents=True, exist_ok=True)
    return history_dir


class ChatHistory:
    """Manages chat session history persistence."""

    def __init__(self, session_name: str = "default"):
        """Initialize chat history manager.
        
        Args:
            session_name: Name of this chat session
        """
        self.session_name = session_name
        self.history_dir = get_chat_history_dir()
        self.session_file = self.history_dir / f"{session_name}.json"
        self.messages = []
        self._load_history()

    def _load_history(self) -> None:
        """Load chat history from disk."""
        if self.session_file.exists():
            try:
                with open(self.session_file, "r") as f:
                    data = json.load(f)
                    self.messages = data.get("messages", [])
            except (json.JSONDecodeError, IOError):
                self.messages = []

    def save(self) -> None:
        """Save chat history to disk."""
        data = {
            "session_name": self.session_name,
            "created": self.session_file.stat().st_ctime if self.session_file.exists() else datetime.now().timestamp(),
            "updated": datetime.now().timestamp(),
            "message_count": len(self.messages),
            "messages": self.messages,
        }
        with open(self.session_file, "w") as f:
            json.dump(data, f, indent=2)

    def add_message(self, role: str, content: str, metadata: dict | None = None) -> None:
        """Add a message to history.
        
        Args:
            role: "user" or "assistant"
            content: Message content
            metadata: Optional metadata (e.g., file context, tokens used)
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
        if metadata:
            message["metadata"] = metadata
        self.messages.append(message)
        self.save()

    def get_messages(self, limit: int | None = None) -> list[dict]:
        """Get chat messages.
        
        Args:
            limit: Maximum number of recent messages to return
            
        Returns:
            List of message dicts with role, content, timestamp
        """
        if limit:
            return self.messages[-limit:]
        return self.messages

    def clear(self) -> None:
        """Clear this session's history."""
        self.messages = []
        if self.session_file.exists():
            self.session_file.unlink()

    @staticmethod
    def list_sessions() -> list[dict]:
        """List all available chat sessions.
        
        Returns:
            List of session info dicts with name, created, updated, message_count
        """
        history_dir = get_cache_dir() / "chat_history"
        if not history_dir.exists():
            return []

        sessions = []
        for session_file in history_dir.glob("*.json"):
            try:
                with open(session_file, "r") as f:
                    data = json.load(f)
                    sessions.append({
                        "name": session_file.stem,
                        "message_count": data.get("message_count", 0),
                        "updated": datetime.fromtimestamp(data.get("updated", 0)).isoformat(),
                    })
            except (json.JSONDecodeError, IOError):
                continue

        return sorted(sessions, key=lambda x: x["updated"], reverse=True)

    @staticmethod
    def load_session(session_name: str) -> "ChatHistory":
        """Load an existing chat session.
        
        Args:
            session_name: Name of session to load
            
        Returns:
            ChatHistory instance with messages loaded
        """
        return ChatHistory(session_name)

    @staticmethod
    def export_session(session_name: str, format_type: str = "json") -> str:
        """Export session to string format.
        
        Args:
            session_name: Name of session to export
            format_type: "json" or "markdown"
            
        Returns:
            Formatted session content
        """
        history = ChatHistory.load_session(session_name)
        
        if format_type == "markdown":
            lines = [f"# Chat Session: {session_name}\n"]
            for msg in history.messages:
                role = msg["role"].upper()
                lines.append(f"## {role}\n")
                lines.append(f"{msg['content']}\n")
            return "\n".join(lines)
        else:  # json
            return json.dumps({
                "session_name": session_name,
                "messages": history.messages,
            }, indent=2)

    def to_api_messages(self) -> list[dict]:
        """Convert chat history to API message format for LLM.
        
        Returns:
            List of messages formatted for API (role + content only)
        """
        return [{"role": msg["role"], "content": msg["content"]} for msg in self.messages]

"""Tests for chat history persistence and LLM prompts."""

import json
from types import SimpleNamespace
from pathlib import Path
import pytest

from kicli_code_assist.chat_history import ChatHistory, get_chat_history_dir
from kicli_code_assist.chat_session import ChatSession
from kicli_code_assist.prompts import SystemPrompts, PromptRole, PromptTemplates


class TestChatHistory:
    """Test chat history persistence."""

    def test_create_new_session(self):
        """Test creating a new chat session."""
        history = ChatHistory("test-session")
        assert history.session_name == "test-session"
        assert history.messages == []

    def test_add_message(self):
        """Test adding messages to history."""
        history = ChatHistory("test-session-2")
        
        history.add_message("user", "Hello")
        history.add_message("assistant", "Hi there!")
        
        assert len(history.messages) == 2
        assert history.messages[0]["role"] == "user"
        assert history.messages[0]["content"] == "Hello"

    def test_save_and_load(self):
        """Test saving and loading chat history."""
        history1 = ChatHistory("test-session-3")
        history1.add_message("user", "Test message")
        history1.save()
        
        # Load in new instance
        history2 = ChatHistory("test-session-3")
        assert len(history2.messages) == 1
        assert history2.messages[0]["content"] == "Test message"

    def test_list_sessions(self):
        """Test listing available sessions."""
        history1 = ChatHistory("session-a")
        history1.add_message("user", "Message A")
        history1.save()
        
        history2 = ChatHistory("session-b")
        history2.add_message("user", "Message B")
        history2.save()
        
        sessions = ChatHistory.list_sessions()
        session_names = [s["name"] for s in sessions]
        
        # Should contain our test sessions
        assert any("session-a" in name or "session-b" in name for name in session_names)

    def test_export_json(self):
        """Test exporting session to JSON."""
        history = ChatHistory("test-export")
        history.add_message("user", "Question")
        history.add_message("assistant", "Answer")
        history.save()
        
        json_str = ChatHistory.export_session("test-export", "json")
        data = json.loads(json_str)
        
        assert data["session_name"] == "test-export"
        assert len(data["messages"]) == 2

    def test_export_markdown(self):
        """Test exporting session to Markdown."""
        history = ChatHistory("test-md")
        history.add_message("user", "How does this work?")
        history.add_message("assistant", "It works like this...")
        history.save()
        
        md_str = ChatHistory.export_session("test-md", "markdown")
        
        assert "test-md" in md_str
        assert "USER" in md_str
        assert "ASSISTANT" in md_str
        assert "How does this work?" in md_str

    def test_clear_session(self):
        """Test clearing a session."""
        history = ChatHistory("test-clear")
        history.add_message("user", "Test")
        history.save()
        
        history.clear()
        assert len(history.messages) == 0

    def test_message_metadata(self):
        """Test adding metadata to messages."""
        history = ChatHistory("test-meta")
        metadata = {"context_included": True, "tokens_used": 250}
        
        history.add_message("user", "Question", metadata)
        
        assert history.messages[0]["metadata"] == metadata

    def test_chat_history_dir_falls_back_when_config_field_missing(self, monkeypatch, tmp_path):
        """Use cache dir fallback when ki-core config lacks chat history field."""
        config = SimpleNamespace(kicli_cache_dir=str(tmp_path))
        monkeypatch.setattr(
            "kicli_code_assist.chat_history.Config.from_env",
            lambda: config,
        )

        history_dir = get_chat_history_dir()

        assert history_dir == tmp_path / "chat_history"


class TestSystemPrompts:
    """Test LLM system prompts."""

    def test_base_rules(self):
        """Test base behavioral rules."""
        rules = SystemPrompts.get_base_rules()
        assert "Accuracy & Confidence" in rules
        assert "Response Format" in rules
        assert "Error Handling" in rules

    def test_code_assistant_prompt(self):
        """Test code assistant prompt generation."""
        prompt = SystemPrompts.get_code_assistant_prompt()
        assert "code assistant" in prompt.lower()
        assert "working code examples" in prompt.lower()
        assert "best practices" in prompt.lower()

    def test_architect_prompt(self):
        """Test architect prompt generation."""
        prompt = SystemPrompts.get_architect_prompt()
        assert "architect" in prompt.lower()
        assert "system design" in prompt.lower()
        assert "trade-off" in prompt.lower() or "trade-offs" in prompt.lower()

    def test_debugger_prompt(self):
        """Test debugger prompt generation."""
        prompt = SystemPrompts.get_debugger_prompt()
        assert "debug" in prompt.lower()
        assert "root cause" in prompt.lower()
        assert "reproduce" in prompt.lower()

    def test_reviewer_prompt(self):
        """Test code reviewer prompt generation."""
        prompt = SystemPrompts.get_reviewer_prompt()
        assert "review" in prompt.lower()
        assert "correctness" in prompt.lower()
        assert "pull request" in prompt.lower()

    def test_explainer_prompt(self):
        """Test explainer prompt generation."""
        prompt = SystemPrompts.get_explainer_prompt()
        assert "explain" in prompt.lower()
        assert "concept" in prompt.lower()
        assert "analogies" in prompt.lower() or "analogy" in prompt.lower()

    def test_prompt_with_context(self):
        """Test prompt generation with project context."""
        context = "Project: MyApp\nLanguage: Python\nType: Web Framework"
        prompt = SystemPrompts.get_code_assistant_prompt(context)
        
        assert context in prompt
        assert "Project Context" in prompt

    def test_get_prompt_by_role(self):
        """Test getting prompt by role enum."""
        for role in PromptRole:
            prompt = SystemPrompts.get_prompt(role)
            assert isinstance(prompt, str)
            assert len(prompt) > 100

    def test_get_all_prompts(self):
        """Test getting all prompts."""
        prompts = SystemPrompts.get_all_prompts()
        
        assert len(prompts) == 5
        assert PromptRole.CODE_ASSISTANT.value in prompts
        assert PromptRole.ARCHITECT.value in prompts
        assert PromptRole.DEBUGGER.value in prompts
        assert PromptRole.REVIEWER.value in prompts
        assert PromptRole.EXPLAINER.value in prompts


class TestPromptTemplates:
    """Test prompt templates for common tasks."""

    def test_refactor_template(self):
        """Test code refactoring template."""
        template = PromptTemplates.refactor_request(
            code="def old(): pass",
            goals="Improve performance"
        )
        
        assert "refactor" in template.lower()
        assert "def old(): pass" in template
        assert "Improve performance" in template

    def test_bug_report_template(self):
        """Test bug report template."""
        template = PromptTemplates.bug_report(
            error_message="IndexError: list index out of range",
            context="Processing user data"
        )
        
        assert "bug" in template.lower() or "debug" in template.lower()
        assert "IndexError" in template
        assert "Processing user data" in template

    def test_architecture_review_template(self):
        """Test architecture review template."""
        template = PromptTemplates.architecture_review(
            current_design="Monolithic app",
            concerns="Scaling issues"
        )
        
        assert "architecture" in template.lower() or "design" in template.lower()
        assert "Monolithic app" in template
        assert "Scaling issues" in template

    def test_code_review_template(self):
        """Test code review template."""
        template = PromptTemplates.code_review(
            code="new implementation",
            context="Feature: Auth"
        )
        
        assert "review" in template.lower()
        assert "new implementation" in template
        assert "Feature: Auth" in template


class TestChatSessionIntegration:
    """Test ChatSession with history and prompts."""

    def test_session_with_role(self):
        """Test creating session with specific role."""
        session = ChatSession(role=PromptRole.ARCHITECT)
        assert session.role == PromptRole.ARCHITECT

    def test_session_role_string(self):
        """Test creating session with role as string."""
        session = ChatSession(role="debugger")
        assert session.role == PromptRole.DEBUGGER

    def test_change_role(self):
        """Test changing session role."""
        session = ChatSession(role=PromptRole.CODE_ASSISTANT)
        session.set_role(PromptRole.DEBUGGER)
        assert session.role == PromptRole.DEBUGGER

    def test_system_prompt_uses_role(self):
        """Test that system prompt respects session role."""
        session_assistant = ChatSession(role=PromptRole.CODE_ASSISTANT)
        session_architect = ChatSession(role=PromptRole.ARCHITECT)
        
        prompt_assistant = session_assistant.get_system_prompt()
        prompt_architect = session_architect.get_system_prompt()
        
        assert prompt_assistant != prompt_architect
        assert "code assistant" in prompt_assistant.lower()
        assert "architect" in prompt_architect.lower()

    def test_add_message_persists(self):
        """Test that adding message persists to history."""
        session = ChatSession(session_name="persist-test")
        session.add_message("user", "Hello")
        
        # Load in new session
        session2 = ChatSession(session_name="persist-test")
        assert len(session2.messages) == 1
        assert session2.messages[0].content == "Hello"

    def test_list_sessions_static(self):
        """Test listing sessions through ChatSession."""
        session = ChatSession(session_name="list-test")
        session.add_message("user", "Test")
        session.history.save()
        
        sessions = ChatSession.list_sessions()
        assert len(sessions) > 0

    def test_load_session_static(self):
        """Test loading session through static method."""
        # Create session first
        session1 = ChatSession(session_name="load-test")
        session1.add_message("user", "Original message")
        session1.history.save()
        
        # Load with static method
        session2 = ChatSession.load_session("load-test")
        assert len(session2.messages) == 1
        assert session2.messages[0].content == "Original message"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

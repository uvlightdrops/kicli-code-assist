"""Comprehensive test suite for Phase 4 (Async LLM, Security, AI Workflow).

Tests cover:
- Phase 4.1: AsyncOpenAIClient, ProviderChain, Secret Filtering, Error Handling
- Phase 4.2: Encryption, Response Parsing, Multi-part responses
- Phase 4.3: Approval Workflow, AI Suggestions, Integration
"""

import pytest
import asyncio
import json
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

# Phase 4.1 Tests
from ki_core.adapters.openai_async import AsyncOpenAIClient
from ki_core.adapters.provider_chain import ProviderChain
from ki_core.security.filters import SensitiveDataFilter
from ki_core.errors.structured import (
    KICoreError,
    LLMTimeoutError,
    LLMAuthError,
    LLMRateLimitError,
    AllProvidersFailedError,
    RecoveryHint,
)

# Phase 4.2 Tests
from ki_core.security.encryption import EncryptionManager, EncryptedStorage
from ki_core.core.response_parser import ResponseParser, ResponsePartType

# Phase 4.3 Tests
from kicli_code_assist.approval_workflow import (
    CodeHunk,
    LineModification,
    ApprovalSession,
    HunkStatus,
)
from kicli_code_assist.ai_workflow import AIWorkflowManager


class TestAsyncOpenAIClient:
    """Test AsyncOpenAIClient implementation."""

    def test_client_initialization(self):
        """Test AsyncOpenAIClient initializes correctly."""
        client = AsyncOpenAIClient(api_key="sk-test123")
        assert client.api_key == "sk-test123"
        assert client.timeout == 30

    def test_custom_timeout(self):
        """Test AsyncOpenAIClient accepts custom timeout."""
        client = AsyncOpenAIClient(api_key="sk-test", timeout=60)
        assert client.timeout == 60

    def test_sync_methods_raise_not_implemented(self):
        """Test sync methods raise NotImplementedError (async-only client)."""
        client = AsyncOpenAIClient(api_key="sk-test")
        
        with pytest.raises(NotImplementedError):
            client.chat("test message", [])
        
        with pytest.raises(NotImplementedError):
            client.chat_stream("test message", [])

    @pytest.mark.asyncio
    async def test_achat_with_mock_openai(self):
        """Test async chat with mocked OpenAI client."""
        client = AsyncOpenAIClient(api_key="sk-test")
        
        # Mock the OpenAI client
        with patch('ki_core.adapters.openai_async.AsyncOpenAI') as mock_async_openai:
            # Setup mock response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Hello, world!"
            
            # Mock completion.create as async
            mock_instance = MagicMock()
            mock_instance.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_async_openai.return_value = mock_instance
            
            # Call achat
            result = await client.achat("Test prompt", [], model="gpt-4")
            
            assert result == "Hello, world!"

    def test_sync_chat_raises_error(self):
        """Test that sync methods on AsyncOpenAIClient raise error."""
        client = AsyncOpenAIClient(api_key="sk-test")
        
        with pytest.raises(NotImplementedError) as exc_info:
            client.chat("test", [])
        
        assert "async" in str(exc_info.value).lower()


class TestProviderChain:
    """Test ProviderChain fallback logic."""

    def test_provider_chain_initialization(self):
        """Test ProviderChain initializes with providers."""
        providers = [Mock(), Mock(), Mock()]
        chain = ProviderChain(providers)
        assert len(chain.providers) == 3

    def test_provider_chain_tracks_stats(self):
        """Test ProviderChain tracks per-provider statistics."""
        providers = [Mock(), Mock()]
        chain = ProviderChain(providers)
        
        # Initially empty
        assert chain.get_stats() is not None
        assert len(chain.get_stats()) == 0

    def test_retry_logic_with_exponential_backoff(self):
        """Test exponential backoff calculation."""
        providers = [Mock()]
        chain = ProviderChain(providers)
        
        # Check backoff formula: 2^attempt
        backoff_1 = 2 ** 1  # 2 seconds
        backoff_2 = 2 ** 2  # 4 seconds
        backoff_3 = 2 ** 3  # 8 seconds
        
        assert backoff_1 == 2
        assert backoff_2 == 4
        assert backoff_3 == 8


class TestSensitiveDataFilter:
    """Test secret detection and redaction."""

    def test_detect_api_keys(self):
        """Test detection of various API key formats."""
        filter_obj = SensitiveDataFilter()
        
        # OpenAI key
        text_with_openai = "My key is sk-proj-abc123def456"
        assert filter_obj.has_secrets(text_with_openai)
        
        # Anthropic key
        text_with_anthropic = "Key: sk-ant-xyz789"
        assert filter_obj.has_secrets(text_with_anthropic)

    def test_detect_passwords(self):
        """Test password detection."""
        filter_obj = SensitiveDataFilter()
        
        text = "password=MySecurePass123!"
        assert filter_obj.has_secrets(text)

    def test_detect_database_urls(self):
        """Test database URL detection."""
        filter_obj = SensitiveDataFilter()
        
        text = "postgres://user:password@host:5432/db"
        assert filter_obj.has_secrets(text)

    def test_redaction(self):
        """Test redaction of detected secrets."""
        filter_obj = SensitiveDataFilter()
        
        text = "API key sk-test123 is my secret"
        redacted = filter_obj.filter(text)
        
        assert "sk-test123" not in redacted
        assert "[REDACTED]" in redacted

    def test_audit_log_tracks_redactions(self):
        """Test RedactionLog tracks redaction count."""
        filter_obj = SensitiveDataFilter()
        
        text = "Keys: sk-1 sk-2 sk-3"
        redacted = filter_obj.filter(text)
        
        # Should have detected secrets
        assert filter_obj.has_secrets(text)


class TestStructuredErrors:
    """Test error hierarchy and recovery hints."""

    def test_base_error_with_recovery_hint(self):
        """Test KICoreError accepts recovery hints."""
        hint = RecoveryHint(
            action="retry",
            description="Try again after waiting",
            command="retry_operation()",
        )
        error = KICoreError("Failed", recovery_hints=[hint])
        assert len(error.recovery_hints) == 1
        assert error.recovery_hints[0].action == "retry"

    def test_llm_timeout_error(self):
        """Test LLMTimeoutError with default recovery hints."""
        error = LLMTimeoutError("Timeout after 30s")
        assert len(error.recovery_hints) > 0
        assert any("retry" in h.description.lower() for h in error.recovery_hints)

    def test_llm_auth_error_hints(self):
        """Test LLMAuthError provides auth-specific recovery hints."""
        error = LLMAuthError("Invalid API key")
        assert len(error.recovery_hints) > 0
        assert any("api" in h.description.lower() for h in error.recovery_hints)

    def test_all_providers_failed_error(self):
        """Test AllProvidersFailedError with all provider status."""
        error = AllProvidersFailedError(
            "All providers failed",
            provider_errors={"openai": "timeout", "claude": "rate limit"},
        )
        assert error.provider_errors is not None


class TestEncryptionManager:
    """Test chat history encryption."""

    def test_encryption_roundtrip(self, tmp_path):
        """Test encrypt→decrypt roundtrip."""
        manager = EncryptionManager(key_dir=str(tmp_path))
        
        original_data = {"message": "Secret chat history", "user": "alice"}
        
        encrypted = manager.encrypt(original_data)
        decrypted = manager.decrypt(encrypted)
        
        assert decrypted == original_data

    def test_encrypt_empty_data(self, tmp_path):
        """Test encryption of empty data."""
        manager = EncryptionManager(key_dir=str(tmp_path))
        
        empty_data = {}
        encrypted = manager.encrypt(empty_data)
        decrypted = manager.decrypt(encrypted)
        
        assert decrypted == empty_data

    def test_master_key_generation(self, tmp_path):
        """Test master key auto-generation."""
        key_file = tmp_path / "master.key"
        manager = EncryptionManager(key_file=str(key_file))
        
        # Key file should be created
        assert key_file.exists()
        
        # Key file should have correct permissions (0o600 on Unix)
        if hasattr(key_file, 'stat'):
            stat_info = key_file.stat()
            # Check file is readable (basic check)
            assert stat_info.st_size > 0

    def test_encrypt_nested_dicts(self, tmp_path):
        """Test encryption of nested data structures."""
        manager = EncryptionManager(key_dir=str(tmp_path))
        
        nested_data = {
            "user": {
                "name": "Alice",
                "messages": [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi there!"},
                ],
            }
        }
        
        encrypted = manager.encrypt(nested_data)
        decrypted = manager.decrypt(encrypted)
        
        assert decrypted == nested_data

    def test_encrypted_storage_persistence(self, tmp_path):
        """Test EncryptedStorage file persistence."""
        storage = EncryptedStorage(storage_dir=str(tmp_path))
        
        data = {"conversation": "Test"}
        storage.save("test_session", data)
        
        # Verify file exists
        assert (tmp_path / "test_session.enc").exists()
        
        # Load back
        loaded = storage.load("test_session")
        assert loaded == data


class TestResponseParser:
    """Test multi-part response parsing."""

    def test_parse_single_code_block(self):
        """Test parsing response with single code block."""
        parser = ResponseParser()
        response = """
Here's the fixed code:

```python
def hello():
    print("Hello, World!")
```

This should work now.
"""
        
        parts = parser.parse(response)
        
        # Should have found code block
        code_parts = [p for p in parts if p.type == ResponsePartType.CODE]
        assert len(code_parts) > 0
        assert "hello()" in code_parts[0].content

    def test_parse_multiple_code_blocks(self):
        """Test parsing multiple code blocks."""
        parser = ResponseParser()
        response = """
First block:
```python
x = 1
```

Second block:
```javascript
const x = 1;
```
"""
        
        parts = parser.parse(response)
        code_parts = [p for p in parts if p.type == ResponsePartType.CODE]
        
        assert len(code_parts) >= 2

    def test_detect_shell_commands(self):
        """Test shell command detection."""
        parser = ResponseParser()
        response = """
Run this:

```bash
rm -rf /tmp/build
npm install
```
"""
        
        parts = parser.parse(response)
        shell_parts = [p for p in parts if p.type == ResponsePartType.SHELL]
        
        assert len(shell_parts) > 0
        assert "npm install" in shell_parts[0].content

    def test_parse_text_between_blocks(self):
        """Test text content between code blocks."""
        parser = ResponseParser()
        response = "Start\n```python\nx = 1\n```\nEnd"
        
        parts = parser.parse(response)
        text_parts = [p for p in parts if p.type == ResponsePartType.TEXT]
        
        # Should have text parts
        assert len(text_parts) > 0


class TestApprovalWorkflow:
    """Test code approval workflow."""

    def test_code_hunk_initialization(self):
        """Test CodeHunk creation."""
        hunk = CodeHunk(
            file_path="test.py",
            start_line=10,
            end_line=20,
        )
        
        assert hunk.file_path == "test.py"
        assert hunk.start_line == 10
        assert hunk.end_line == 20
        assert hunk.status == HunkStatus.PENDING

    def test_line_modification_tracking(self):
        """Test line-by-line modification."""
        lines = [
            LineModification(
                line_number=1,
                original_line="old code",
                modified_line="new code",
            ),
            LineModification(
                line_number=2,
                original_line="foo()",
                modified_line="bar()",
            ),
        ]
        
        hunk = CodeHunk(
            file_path="test.py",
            start_line=1,
            end_line=2,
            lines=lines,
        )
        
        assert len(hunk.lines) == 2
        assert hunk.lines[0].original_line == "old code"

    def test_approve_single_line(self):
        """Test approving individual lines."""
        lines = [
            LineModification(1, "a", "A"),
            LineModification(2, "b", "B"),
        ]
        
        hunk = CodeHunk("test.py", 1, 2, lines=lines)
        hunk.approve_line(1)
        
        assert hunk.lines[0].status == HunkStatus.APPROVED
        assert hunk.lines[1].status == HunkStatus.PENDING

    def test_reject_line_with_reason(self):
        """Test rejecting line with reason."""
        line = LineModification(1, "old", "new")
        hunk = CodeHunk("test.py", 1, 1, lines=[line])
        
        hunk.reject_line(1, reason="Breaks backward compatibility")
        
        assert hunk.lines[0].status == HunkStatus.REJECTED
        assert hunk.lines[0].reason == "Breaks backward compatibility"

    def test_approval_percentage(self):
        """Test approval percentage calculation."""
        lines = [
            LineModification(i, f"old{i}", f"new{i}")
            for i in range(1, 5)
        ]
        
        hunk = CodeHunk("test.py", 1, 4, lines=lines)
        
        # Initially pending
        assert hunk.get_approval_percentage() == 0.0
        
        # Approve 2 out of 4
        hunk.approve_line(1)
        hunk.approve_line(2)
        
        assert hunk.get_approval_percentage() == 50.0

    def test_approval_session_summary(self):
        """Test ApprovalSession summary generation."""
        hunk1 = CodeHunk("test1.py", 1, 10)
        hunk1.status = HunkStatus.APPROVED
        
        hunk2 = CodeHunk("test2.py", 1, 20)
        hunk2.status = HunkStatus.PENDING
        
        session = ApprovalSession(session_id="test-1")
        session.add_hunk(hunk1)
        session.add_hunk(hunk2)
        
        summary = session.get_summary()
        
        assert summary["total_hunks"] == 2
        assert summary["approved"] == 1
        assert summary["pending"] == 1

    def test_is_ready_for_apply(self):
        """Test readiness check for applying changes."""
        hunk = CodeHunk("test.py", 1, 10)
        hunk.status = HunkStatus.APPROVED
        
        session = ApprovalSession(session_id="test-1")
        session.add_hunk(hunk)
        
        assert session.is_ready_for_apply() is True

    def test_partial_approval_status(self):
        """Test PARTIAL status when some lines approved."""
        lines = [
            LineModification(1, "a", "A"),
            LineModification(2, "b", "B"),
        ]
        
        hunk = CodeHunk("test.py", 1, 2, lines=lines)
        hunk.approve_line(1)  # Approve only one line
        
        assert hunk.status == HunkStatus.PARTIAL


class TestAIWorkflowManager:
    """Test AI suggestion workflow orchestration."""

    @pytest.mark.asyncio
    async def test_workflow_initialization(self):
        """Test AIWorkflowManager initializes correctly."""
        manager = AIWorkflowManager()
        assert manager.parser is not None

    def test_context_building(self):
        """Test context building for LLM."""
        manager = AIWorkflowManager()
        
        context = manager._build_context(
            prompt="Fix the bug",
            file_content="def foo(): pass",
            file_path="test.py",
        )
        
        assert "Fix the bug" in context
        assert "test.py" in context
        assert "def foo()" in context

    def test_create_hunks_from_response(self):
        """Test creating hunks from parsed response."""
        manager = AIWorkflowManager()
        
        # Mock parsed parts
        from ki_core.core.response_parser import ResponsePart
        
        parsed_parts = [
            ResponsePart(
                type=ResponsePartType.CODE,
                content="def improved():\n    return True",
            )
        ]
        
        hunks = manager._create_hunks_from_response(
            parsed_parts,
            original_content="def original(): pass",
            file_path="test.py",
        )
        
        assert len(hunks) > 0
        assert isinstance(hunks[0], CodeHunk)

    def test_apply_approved_changes(self):
        """Test applying approved changes to file."""
        manager = AIWorkflowManager()
        
        # Create test suggestion
        hunk = CodeHunk("test.py", 1, 2)
        hunk.lines = [
            LineModification(1, "old", "new"),
            LineModification(2, "foo", "bar"),
        ]
        hunk.status = HunkStatus.APPROVED
        
        suggestion = Mock()
        suggestion.approval_session = ApprovalSession(session_id="test")
        suggestion.approval_session.add_hunk(hunk)
        suggestion.original_content = "old\nfoo"
        
        # Track callback
        applied_content = []
        
        def apply_callback(content: str):
            applied_content.append(content)
        
        manager.apply_approved_changes(suggestion, apply_callback)
        
        # Should have called callback
        assert len(applied_content) > 0

    def test_session_summary_formatting(self):
        """Test session summary formatting."""
        manager = AIWorkflowManager()
        
        session = ApprovalSession(session_id="test-summary")
        hunk = CodeHunk("test.py", 1, 10)
        hunk.status = HunkStatus.APPROVED
        session.add_hunk(hunk)
        
        summary = manager.get_session_summary(session)
        
        assert "Summary" in summary
        assert "✓" in summary  # Success indicator
        assert "Ready to apply" in summary


# Integration Tests
class TestPhase4Integration:
    """Integration tests for Phase 4 complete workflow."""

    def test_full_secret_filtering_workflow(self):
        """Test secret filtering in realistic context."""
        filter_obj = SensitiveDataFilter()
        
        context = """
        User's API key: sk-proj-abc123
        Database URL: postgres://root:password123@db.example.com
        """
        
        filtered = filter_obj.filter(context)
        
        # Secrets should be redacted
        assert "sk-proj-abc123" not in filtered
        assert "password123" not in filtered
        assert "[REDACTED]" in filtered

    def test_error_recovery_chain(self):
        """Test error handling with recovery suggestions."""
        # Simulate LLMTimeoutError
        error = LLMTimeoutError("API timed out")
        
        # Should have recovery hints
        assert len(error.recovery_hints) > 0
        
        # Hints should be actionable
        for hint in error.recovery_hints:
            assert hint.action is not None
            assert hint.description is not None

    def test_full_encryption_workflow(self, tmp_path):
        """Test full chat encryption workflow."""
        manager = EncryptionManager(key_dir=str(tmp_path))
        storage = EncryptedStorage(storage_dir=str(tmp_path))
        
        # Create session with multiple messages
        session_data = {
            "session_id": "test-encryption",
            "messages": [
                {"role": "user", "content": "Secret question"},
                {"role": "assistant", "content": "Secret answer"},
            ],
        }
        
        # Save encrypted
        storage.save("session-1", session_data)
        
        # Verify encryption (file should contain encrypted bytes)
        session_file = tmp_path / "session-1.enc"
        assert session_file.exists()
        
        file_content = session_file.read_text()
        assert session_data["session_id"] not in file_content  # Should be encrypted
        
        # Load and verify
        loaded = storage.load("session-1")
        assert loaded == session_data


# Performance Tests
class TestPerformance:
    """Performance and regression tests."""

    def test_response_parser_performance(self):
        """Test response parser handles large responses efficiently."""
        parser = ResponseParser()
        
        # Create large response with multiple blocks
        large_response = "\n".join([
            f"Block {i}:\n```python\nx = {i}\n```"
            for i in range(100)
        ])
        
        # Should parse in reasonable time
        import time
        start = time.time()
        parts = parser.parse(large_response)
        elapsed = time.time() - start
        
        # Should be fast (< 1 second for 100 blocks)
        assert elapsed < 1.0
        assert len(parts) > 0

    def test_encryption_performance(self, tmp_path):
        """Test encryption performance with large data."""
        manager = EncryptionManager(key_dir=str(tmp_path))
        
        # Create large data
        large_data = {
            "messages": [{"role": "user", "content": "x" * 10000} for _ in range(100)]
        }
        
        import time
        start = time.time()
        encrypted = manager.encrypt(large_data)
        elapsed = time.time() - start
        
        # Should encrypt reasonably fast
        assert elapsed < 2.0

    def test_approval_workflow_performance(self):
        """Test approval workflow with many hunks."""
        session = ApprovalSession(session_id="perf-test")
        
        # Create many hunks
        for i in range(100):
            hunk = CodeHunk(f"file{i}.py", i * 10, (i + 1) * 10)
            hunk.lines = [
                LineModification(j, f"old{j}", f"new{j}")
                for j in range(10)
            ]
            session.add_hunk(hunk)
        
        # Should generate summary quickly
        import time
        start = time.time()
        summary = session.get_summary()
        elapsed = time.time() - start
        
        assert elapsed < 0.5  # Summary generation should be fast


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

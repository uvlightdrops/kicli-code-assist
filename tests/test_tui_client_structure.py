"""Tests for TUI client structure."""

import pytest
from pathlib import Path
from kicli_code_assist.ui.tui_client import CodeAssistantTUIApp
from kicli_code_assist.ui.tui_config import TUIConfig
from kicli_code_assist.ui.tui_agent_client import TUIAgentClient


def test_tui_config_creation():
    """Test TUIConfig initialization."""
    config = TUIConfig()
    assert config.api_base_url == "http://localhost:8000"
    assert config.ws_base_url == "ws://localhost:8000"
    assert config.max_output_lines == 500


def test_tui_config_from_env(monkeypatch):
    """Test TUIConfig loads from environment."""
    monkeypatch.setenv("TUI_API_URL", "http://prod.example.com:8000")
    config = TUIConfig.from_env()
    assert config.api_base_url == "http://prod.example.com:8000"


def test_agent_client_initialization():
    """Test TUIAgentClient creation."""
    client = TUIAgentClient("http://localhost:8000")
    assert client.base_url == "http://localhost:8000"
    assert client.ws_url == "ws://localhost:8000"

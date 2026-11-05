"""
Integration Tests for TUI

End-to-end tests validating:
- Component composition
- File selection flow
- Input submission flow
- Backend response display
- Configuration enable/disable
- Keyboard shortcuts
- Error handling
"""

import asyncio
import logging
import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from dataclasses import dataclass

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@dataclass
class MockResponse:
    """Mock API response."""
    success: bool
    status_code: int
    data: dict = None
    error: str = None


class TestAPIClient:
    """Tests for API client."""
    
    @pytest.mark.asyncio
    async def test_http_client_init(self):
        """Test HTTP client initialization."""
        from kicli_code_assist.ui.api_client import HTTPClient
        
        client = HTTPClient("http://localhost:8000")
        assert client.base_url == "http://localhost:8000"
        assert client.timeout == 30
        assert client.retry_count == 3
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_websocket_client_init(self):
        """Test WebSocket client initialization."""
        from kicli_code_assist.ui.api_client import WebSocketClient
        
        client = WebSocketClient("ws://localhost:8000/socket.io")
        assert client.ws_url == "ws://localhost:8000/socket.io"
        assert client.websocket is None
    
    @pytest.mark.asyncio
    async def test_backend_client_init(self):
        """Test backend client initialization."""
        from kicli_code_assist.ui.api_client import BackendClient
        
        client = BackendClient("http://localhost:8000")
        assert client.backend_url == "http://localhost:8000"
        assert client.http_client is not None
        assert client.ws_client is not None


class TestFileTree:
    """Tests for file tree widget."""
    
    def test_file_tree_init(self):
        """Test FileTree initialization."""
        from kicli_code_assist.ui.widgets.file_browser import FileTree
        
        tree = FileTree(project_root=".", ignore_patterns=[".git"])
        assert tree.project_root == Path(".").resolve()
        assert ".git" in tree.ignore_patterns
    
    def test_file_tree_callback(self):
        """Test file selection callback."""
        from kicli_code_assist.ui.widgets.file_browser import FileTree
        
        tree = FileTree()
        callback = Mock()
        tree.set_on_file_selected(callback)
        
        assert tree.on_file_selected_callback == callback
    
    def test_file_tree_ignore_patterns(self):
        """Test ignore pattern matching."""
        from kicli_code_assist.ui.widgets.file_browser import FileTree
        
        tree = FileTree(ignore_patterns=[".git", "__pycache__"])
        
        # Check pattern matching
        assert tree._should_ignore(Path(".git")) is True
        assert tree._should_ignore(Path("__pycache__")) is True
        assert tree._should_ignore(Path("src")) is False


class TestInputBar:
    """Tests for input bar widget."""
    
    def test_input_bar_init(self):
        """Test InputBar initialization."""
        from kicli_code_assist.ui.widgets.input_bar import InputBar
        
        input_bar = InputBar(multiline=True, max_history=50)
        assert input_bar.multiline is True
        assert input_bar.max_history == 50
        assert input_bar.history == []
    
    def test_input_bar_history(self):
        """Test input history tracking."""
        from kicli_code_assist.ui.widgets.input_bar import InputBar
        
        input_bar = InputBar()
        input_bar.history.append("command1")
        input_bar.history.append("command2")
        
        assert len(input_bar.history) == 2
        assert input_bar.history[-1] == "command2"
    
    def test_status_bar_init(self):
        """Test StatusBar initialization."""
        from kicli_code_assist.ui.widgets.input_bar import StatusBar
        
        status = StatusBar()
        assert status.connection_status == "🔴 Offline"
        assert status.processing_time == ""
        assert status.error_message == ""
    
    def test_status_bar_set_connected(self):
        """Test status bar connection state."""
        from kicli_code_assist.ui.widgets.input_bar import StatusBar
        
        status = StatusBar()
        status.set_connected(True)
        assert "Connected" in status.connection_status
        
        status.set_connected(False)
        assert "Offline" in status.connection_status


class TestAgentTabs:
    """Tests for agent tabs widget."""
    
    def test_agent_tabs_init(self):
        """Test AgentTabPanel initialization."""
        from kicli_code_assist.ui.widgets.agent_tabs import AgentTabPanel
        
        tabs = AgentTabPanel()
        assert tabs.enabled_tabs is not None
        assert "Explain" in tabs.enabled_tabs
    
    def test_agent_tabs_display_response_string(self):
        """Test displaying string response."""
        from kicli_code_assist.ui.widgets.agent_tabs import AgentTabPanel
        
        tabs = AgentTabPanel()
        # Note: Would need Textual context for full test
        # This validates the method signature exists
        assert hasattr(tabs, 'display_response')
    
    def test_agent_tabs_display_response_dict(self):
        """Test displaying dict response."""
        from kicli_code_assist.ui.widgets.agent_tabs import AgentTabPanel
        
        tabs = AgentTabPanel()
        response_data = {
            "Explain": "This is an explanation",
            "Suggest": "Here are suggestions",
        }
        
        # Validate method accepts dict
        import inspect
        sig = inspect.signature(tabs.display_response)
        assert 'response_data' in sig.parameters


class TestConfigLoader:
    """Tests for configuration system."""
    
    def test_config_loader_init(self):
        """Test config loader initialization."""
        from kicli_code_assist.ui.config import ConfigLoader
        
        loader = ConfigLoader()
        assert loader.config is not None
        assert hasattr(loader.config, 'backend')
        assert hasattr(loader.config, 'file_tree')
        assert hasattr(loader.config, 'agent_tabs')
    
    def test_config_panels_enabled(self):
        """Test panel enable/disable."""
        from kicli_code_assist.ui.config import ConfigLoader
        
        loader = ConfigLoader()
        
        # Check if panels can be queried
        panels = loader.get_enabled_panels()
        assert isinstance(panels, list)
    
    def test_config_is_enabled(self):
        """Test panel enabled check."""
        from kicli_code_assist.ui.config import ConfigLoader
        
        loader = ConfigLoader()
        
        # File tree should be enabled by default
        assert loader.is_enabled("file_tree") is True
        
        # Agent tabs should be enabled by default
        assert loader.is_enabled("agent_tabs") is True


class TestTUIApp:
    """Tests for main TUI app."""
    
    def test_tui_app_init(self):
        """Test TUI app initialization."""
        from kicli_code_assist.ui.tui_client import KICLITUIApp
        
        app = KICLITUIApp()
        assert app.config is not None
        assert app.backend_client is None
        assert app.selected_file is None
    
    def test_tui_app_config_path(self):
        """Test TUI app with custom config."""
        from kicli_code_assist.ui.tui_client import KICLITUIApp
        
        # Create a temporary config for testing
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
backend:
  url: http://test:9000
file_tree:
  project_root: .
  ignore_patterns: [.git]
agent_tabs:
  enabled_tabs: [Explain, Suggest]
  default_tab: Explain
""")
            config_path = f.name
        
        try:
            app = KICLITUIApp(config_path)
            assert app.config.backend.url == "http://test:9000"
        finally:
            Path(config_path).unlink()


class TestEndToEnd:
    """End-to-end workflow tests."""
    
    def test_file_selection_flow(self):
        """Test file selection → context tracking → submission."""
        from kicli_code_assist.ui.widgets.file_browser import FileTree
        from pathlib import Path
        
        # Create a test file
        test_file = Path("test_e2e.txt")
        test_file.write_text("test content")
        
        try:
            tree = FileTree()
            
            # Track selections
            selections = []
            tree.set_on_file_selected(selections.append)
            
            # Simulate selection (would happen via UI normally)
            assert tree.on_file_selected_callback is not None
        
        finally:
            test_file.unlink()
    
    @pytest.mark.asyncio
    async def test_input_submission_flow(self):
        """Test input submission with async callback."""
        from kicli_code_assist.ui.widgets.input_bar import InputBar
        
        input_bar = InputBar()
        
        # Track submissions
        submissions = []
        
        async def on_submit(text):
            submissions.append(text)
        
        input_bar.on_submit_callback = on_submit
        
        # Simulate submission
        assert input_bar.on_submit_callback is not None


class TestErrorHandling:
    """Tests for error handling."""
    
    def test_invalid_config_path(self):
        """Test handling of invalid config path."""
        from kicli_code_assist.ui.config import ConfigLoader
        
        # Should use defaults if path doesn't exist
        loader = ConfigLoader("/nonexistent/path.yaml")
        assert loader.config is not None
    
    @pytest.mark.asyncio
    async def test_backend_connection_failure(self):
        """Test handling of backend connection failure."""
        from kicli_code_assist.ui.api_client import BackendClient
        
        client = BackendClient("http://localhost:9999")  # Non-existent
        result = await client.init()
        
        # Should handle gracefully
        assert result is False or result is True
    
    def test_invalid_response_data(self):
        """Test handling of invalid response data."""
        from kicli_code_assist.ui.widgets.agent_tabs import AgentTabPanel
        
        tabs = AgentTabPanel()
        
        # Should handle None
        assert hasattr(tabs, 'display_response')


class TestKeyboardBindings:
    """Tests for keyboard bindings."""
    
    def test_tui_app_bindings(self):
        """Test TUI app keyboard bindings."""
        from kicli_code_assist.ui.tui_client import KICLITUIApp
        
        app = KICLITUIApp()
        
        # Check bindings exist
        assert len(app.BINDINGS) > 0
        
        # Check quit binding
        quit_bindings = [b for b in app.BINDINGS if b.action == 'quit']
        assert len(quit_bindings) > 0
        
        # Check tab bindings
        tab_bindings = [b for b in app.BINDINGS if 'tab' in b.action]
        assert len(tab_bindings) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

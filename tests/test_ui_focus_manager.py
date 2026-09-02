"""Tests for focus manager."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from kicli_code_assist.ui.focus_manager import FocusManager, FocusMode


class MockTUI:
    """Mock TUI application."""

    def __init__(self):
        self.components = {
            "#file-browser": Mock(focus=Mock()),
            "#file-preview": Mock(focus=Mock()),
            "#chat-history": Mock(focus=Mock()),
            "#input-box": Mock(focus=Mock()),
            "#diff-viewer": Mock(focus=Mock()),
            "#title-bar": Mock(update=Mock()),
        }

    def query_one(self, selector, expect_type=None):
        if selector not in self.components:
            raise Exception(f"Component not found: {selector}")
        return self.components[selector]


class TestFocusMode:
    """Test FocusMode enum."""

    def test_all_modes_defined(self):
        """Test all focus modes exist."""
        modes = list(FocusMode)
        assert len(modes) == 5
        assert FocusMode.FILE_BROWSER in modes
        assert FocusMode.FILE_PREVIEW in modes
        assert FocusMode.CHAT_HISTORY in modes
        assert FocusMode.INPUT_FIELD in modes
        assert FocusMode.DIFF_VIEWER in modes

    def test_mode_values(self):
        """Test mode values."""
        assert FocusMode.FILE_BROWSER.value == "browser"
        assert FocusMode.FILE_PREVIEW.value == "preview"
        assert FocusMode.CHAT_HISTORY.value == "chat"
        assert FocusMode.INPUT_FIELD.value == "input"
        assert FocusMode.DIFF_VIEWER.value == "diff"


class TestFocusManager:
    """Test FocusManager class."""

    def test_initialization(self):
        """Test manager initialization."""
        tui = MockTUI()
        manager = FocusManager(tui)

        assert manager.tui is tui
        assert manager.current_mode == FocusMode.INPUT_FIELD
        assert manager.previous_mode == FocusMode.INPUT_FIELD
        assert len(manager.mode_bindings) == 5
        assert len(manager.mode_to_component) == 5
        assert len(manager.mode_to_label) == 5

    def test_keybindings_mapped(self):
        """Test all keybindings are mapped."""
        tui = MockTUI()
        manager = FocusManager(tui)

        bindings = manager.mode_bindings
        assert bindings["ctrl+f"] == FocusMode.FILE_PREVIEW
        assert bindings["ctrl+b"] == FocusMode.FILE_BROWSER
        assert bindings["ctrl+c"] == FocusMode.CHAT_HISTORY
        assert bindings["ctrl+i"] == FocusMode.INPUT_FIELD
        assert bindings["ctrl+d"] == FocusMode.DIFF_VIEWER

    def test_set_focus_file_preview(self):
        """Test setting focus to file preview."""
        tui = MockTUI()
        manager = FocusManager(tui)

        manager.set_focus(FocusMode.FILE_PREVIEW)

        assert manager.current_mode == FocusMode.FILE_PREVIEW
        assert manager.previous_mode == FocusMode.INPUT_FIELD
        tui.components["#file-preview"].focus.assert_called_once()

    def test_set_focus_file_browser(self):
        """Test setting focus to file browser."""
        tui = MockTUI()
        manager = FocusManager(tui)

        manager.set_focus(FocusMode.FILE_BROWSER)

        assert manager.current_mode == FocusMode.FILE_BROWSER
        tui.components["#file-browser"].focus.assert_called_once()

    def test_set_focus_chat_history(self):
        """Test setting focus to chat history."""
        tui = MockTUI()
        manager = FocusManager(tui)

        manager.set_focus(FocusMode.CHAT_HISTORY)

        assert manager.current_mode == FocusMode.CHAT_HISTORY
        tui.components["#chat-history"].focus.assert_called_once()

    def test_set_focus_input_field(self):
        """Test setting focus to input field."""
        tui = MockTUI()
        manager = FocusManager(tui)
        manager.current_mode = FocusMode.FILE_PREVIEW

        manager.set_focus(FocusMode.INPUT_FIELD)

        assert manager.current_mode == FocusMode.INPUT_FIELD
        assert manager.previous_mode == FocusMode.FILE_PREVIEW
        tui.components["#input-box"].focus.assert_called_once()

    def test_set_focus_diff_viewer(self):
        """Test setting focus to diff viewer."""
        tui = MockTUI()
        manager = FocusManager(tui)

        manager.set_focus(FocusMode.DIFF_VIEWER)

        assert manager.current_mode == FocusMode.DIFF_VIEWER
        tui.components["#diff-viewer"].focus.assert_called_once()

    def test_handle_focus_key_ctrl_f(self):
        """Test handling Ctrl+F key."""
        tui = MockTUI()
        manager = FocusManager(tui)

        result = manager.handle_focus_key("ctrl+f")

        assert result is True
        assert manager.current_mode == FocusMode.FILE_PREVIEW

    def test_handle_focus_key_ctrl_d(self):
        """Test handling Ctrl+D key."""
        tui = MockTUI()
        manager = FocusManager(tui)

        result = manager.handle_focus_key("ctrl+d")

        assert result is True
        assert manager.current_mode == FocusMode.DIFF_VIEWER

    def test_handle_focus_key_unmapped(self):
        """Test handling unmapped key."""
        tui = MockTUI()
        manager = FocusManager(tui)
        initial_mode = manager.current_mode

        result = manager.handle_focus_key("ctrl+x")

        assert result is False
        assert manager.current_mode == initial_mode

    def test_highlight_title(self):
        """Test title highlighting."""
        tui = MockTUI()
        manager = FocusManager(tui)

        manager.highlight_title(FocusMode.FILE_PREVIEW)

        tui.components["#title-bar"].update.assert_called()
        call_args = tui.components["#title-bar"].update.call_args
        assert "File Preview [F]" in call_args[0][0]

    def test_highlight_title_orange(self):
        """Test title is highlighted in orange."""
        tui = MockTUI()
        manager = FocusManager(tui)

        manager.highlight_title(FocusMode.CHAT_HISTORY)

        call_args = tui.components["#title-bar"].update.call_args
        text = call_args[0][0]
        assert "[orange" in text
        assert "Chat History [C]" in text

    def test_toggle_focus(self):
        """Test toggling between modes."""
        tui = MockTUI()
        manager = FocusManager(tui)

        manager.set_focus(FocusMode.FILE_PREVIEW)
        assert manager.current_mode == FocusMode.FILE_PREVIEW
        assert manager.previous_mode == FocusMode.INPUT_FIELD

        manager.toggle_focus()
        assert manager.current_mode == FocusMode.INPUT_FIELD

    def test_get_current_mode(self):
        """Test getting current mode."""
        tui = MockTUI()
        manager = FocusManager(tui)

        mode = manager.get_current_mode()
        assert mode == FocusMode.INPUT_FIELD

        manager.set_focus(FocusMode.CHAT_HISTORY)
        mode = manager.get_current_mode()
        assert mode == FocusMode.CHAT_HISTORY

    def test_get_current_label(self):
        """Test getting current mode label."""
        tui = MockTUI()
        manager = FocusManager(tui)

        label = manager.get_current_label()
        assert "Input" in label

        manager.set_focus(FocusMode.FILE_BROWSER)
        label = manager.get_current_label()
        assert "Browser" in label

    def test_is_mode_available(self):
        """Test checking if mode is available."""
        tui = MockTUI()
        manager = FocusManager(tui)

        assert manager.is_mode_available(FocusMode.FILE_BROWSER) is True
        assert manager.is_mode_available(FocusMode.INPUT_FIELD) is True

    def test_get_available_modes(self):
        """Test getting list of available modes."""
        tui = MockTUI()
        manager = FocusManager(tui)

        modes = manager.get_available_modes()
        assert len(modes) == 5
        assert FocusMode.INPUT_FIELD in modes
        assert FocusMode.FILE_PREVIEW in modes

    def test_reset_to_input(self):
        """Test resetting focus to input."""
        tui = MockTUI()
        manager = FocusManager(tui)

        manager.set_focus(FocusMode.DIFF_VIEWER)
        assert manager.current_mode == FocusMode.DIFF_VIEWER

        manager.reset_to_input()
        assert manager.current_mode == FocusMode.INPUT_FIELD

    def test_focus_mode_tracking(self):
        """Test tracking previous focus mode."""
        tui = MockTUI()
        manager = FocusManager(tui)

        manager.set_focus(FocusMode.FILE_PREVIEW)
        assert manager.previous_mode == FocusMode.INPUT_FIELD

        manager.set_focus(FocusMode.CHAT_HISTORY)
        assert manager.previous_mode == FocusMode.FILE_PREVIEW

        manager.set_focus(FocusMode.DIFF_VIEWER)
        assert manager.previous_mode == FocusMode.CHAT_HISTORY

    def test_focus_same_mode_no_change(self):
        """Test setting same focus doesn't update previous."""
        tui = MockTUI()
        manager = FocusManager(tui)

        manager.set_focus(FocusMode.FILE_PREVIEW)
        first_previous = manager.previous_mode

        # Set to same mode
        manager.set_focus(FocusMode.FILE_PREVIEW)
        # Previous should not change when focusing same mode
        assert manager.previous_mode == first_previous

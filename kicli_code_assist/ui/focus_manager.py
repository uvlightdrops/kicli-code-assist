"""Focus management system for TUI panel navigation."""

from enum import Enum
from typing import Optional, Callable, Dict
from textual.app import ComposeResult
from textual.widgets import Static


class FocusMode(Enum):
    """Available focus modes."""
    FILE_BROWSER = "browser"
    FILE_PREVIEW = "preview"
    CHAT_HISTORY = "chat"
    INPUT_FIELD = "input"
    DIFF_VIEWER = "diff"


class FocusManager:
    """Manage focus between UI panels."""

    def __init__(self, tui: "ChatUI"):
        """Initialize focus manager.

        Args:
            tui: ChatUI application instance
        """
        self.tui = tui
        self.current_mode = FocusMode.INPUT_FIELD
        self.previous_mode = FocusMode.INPUT_FIELD

        # Keybinding to mode mapping
        self.mode_bindings: Dict[str, FocusMode] = {
            "ctrl+f": FocusMode.FILE_PREVIEW,
            "ctrl+b": FocusMode.FILE_BROWSER,
            "ctrl+c": FocusMode.CHAT_HISTORY,
            "ctrl+i": FocusMode.INPUT_FIELD,
            "ctrl+d": FocusMode.DIFF_VIEWER,
        }

        # Mode to component ID mapping
        self.mode_to_component: Dict[FocusMode, str] = {
            FocusMode.FILE_BROWSER: "#file-browser",
            FocusMode.FILE_PREVIEW: "#file-preview",
            FocusMode.CHAT_HISTORY: "#chat-history",
            FocusMode.INPUT_FIELD: "#input-box",
            FocusMode.DIFF_VIEWER: "#diff-viewer",
        }

        # Mode to display name mapping
        self.mode_to_label: Dict[FocusMode, str] = {
            FocusMode.FILE_BROWSER: "File Browser [B]",
            FocusMode.FILE_PREVIEW: "File Preview [F]",
            FocusMode.CHAT_HISTORY: "Chat History [C]",
            FocusMode.INPUT_FIELD: "Input [I]",
            FocusMode.DIFF_VIEWER: "Diff Viewer [D]",
        }

    def handle_focus_key(self, key: str) -> bool:
        """Handle focus-related keypress.

        Args:
            key: Key pressed

        Returns:
            True if key was handled, False otherwise
        """
        if key in self.mode_bindings:
            mode = self.mode_bindings[key]
            self.set_focus(mode)
            return True
        return False

    def set_focus(self, mode: FocusMode) -> None:
        """Change focus to specified mode.

        Args:
            mode: FocusMode to focus
        """
        # Store previous mode for navigation back
        if self.current_mode != mode:
            self.previous_mode = self.current_mode
            self.current_mode = mode

        # Get component ID
        component_id = self.mode_to_component.get(mode)
        if not component_id:
            return

        try:
            # Find and focus component
            component = self.tui.query_one(component_id)
            component.focus()

            # Update title bar with focus highlight
            self.highlight_title(mode)
        except Exception:
            # Component not found or not focusable
            pass

    def toggle_focus(self) -> None:
        """Toggle between current and previous focus mode."""
        self.set_focus(self.previous_mode)

    def highlight_title(self, mode: FocusMode) -> None:
        """Highlight title bar to show current focus.

        Args:
            mode: Current focus mode
        """
        try:
            title_bar = self.tui.query_one("#title-bar", expect_type=Static)
            label = self.mode_to_label.get(mode, "Unknown")
            title_bar.update(f"[orange bold]{label}[/orange bold]")
        except Exception:
            # Title bar not found
            pass

    def get_current_mode(self) -> FocusMode:
        """Get current focus mode.

        Returns:
            Current FocusMode
        """
        return self.current_mode

    def get_current_label(self) -> str:
        """Get display label for current mode.

        Returns:
            Display label string
        """
        return self.mode_to_label.get(self.current_mode, "Unknown")

    def is_mode_available(self, mode: FocusMode) -> bool:
        """Check if focus mode is available.

        Args:
            mode: FocusMode to check

        Returns:
            True if available, False otherwise
        """
        component_id = self.mode_to_component.get(mode)
        if not component_id:
            return False

        try:
            component = self.tui.query_one(component_id)
            return component is not None
        except Exception:
            return False

    def get_available_modes(self) -> list[FocusMode]:
        """Get list of available focus modes.

        Returns:
            List of available FocusModes
        """
        return [mode for mode in FocusMode if self.is_mode_available(mode)]

    def reset_to_input(self) -> None:
        """Reset focus back to input field."""
        self.set_focus(FocusMode.INPUT_FIELD)

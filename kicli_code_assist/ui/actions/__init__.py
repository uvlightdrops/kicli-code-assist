"""Textual action handlers for CLI command dispatch.

Textual actions are methods prefixed with 'action_' on a widget.
They can be bound to keyboard shortcuts or called from the command palette.
This module provides centralized action handlers for kicli-code-assist TUI.

Typical action pattern:
    - User presses Ctrl+Q in TUI
    - Textual routes to action_quit() handler
    - Handler updates state and returns (or calls self.app.exit())
"""

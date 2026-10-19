"""UI components for kicli-code-assist TUI.

Main entry point: textual_app.py (CodeAssistantMain - Textual application)
Sub-application: app.py (CodeAssistantApp - main TUI logic)

Submodules:
- app.py: Main TUI widget with composition (chat panel, editor, shell, logging)
- textual_app.py: Textual application entry point (header, footer)
- panels/: Tab panels (chat, diff, logging, shell approval, etc)
- modals/: Dialog widgets (approval, diff viewer, prompts editor)
- widgets/: Reusable components (spinner, shell input, history, etc)
- styles/: CSS styles (textual_app.tcss)
- actions/: Action handlers (CLI command dispatch via Textual actions)
"""

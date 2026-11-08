"""Modern TUI for code assistant using Textual."""

from textual.app import ComposeResult, App
from textual.widgets import Header, Footer
from textual.screen import Screen

from kicli_code_assist.ui.app import CodeAssistantApp
from kicli_code_assist.ui.modals.prompts_modal import PromptsModal


class CodeAssistantMain(Screen):
    """Main screen for the code assistant TUI."""
    
    CSS_PATH = "styles/textual_app.tcss"
    
    BINDINGS = [
        ("tab", "focus_next", "Focus Next"),
        ("shift+tab", "focus_previous", "Focus Previous"),
        ("enter", "select_cursor", "Select / Send"),
        ("up", "cursor_up", "Up"),
        ("down", "cursor_down", "Down"),
        ("pageup", "page_up", "Page Up"),
        ("pagedown", "page_down", "Page Down"),
        ("ctrl+b", "focus_browser", "Browser"),
        ("ctrl+f", "focus_preview", "Preview"),
        ("ctrl+c", "focus_chat", "Chat"),
        ("ctrl+a", "focus_ai_background", "AI Background"),
        ("ctrl+i", "focus_input", "Input"),
        ("ctrl+x", "focus_shell", "Shell"),
        ("ctrl+o", "open_prompts", "Prompts"),
        ("ctrl+s", "save_current_file", "Save File"),
        ("ctrl+l", "load_context", "Load Context"),
        ("ctrl+g", "open_logs", "Logs"),
        ("ctrl+u", "understand_project", "Analyze Project"),
        ("n", "new_file", "New File"),
        ("s", "mark_selection_start", "Mark Start"),
        ("e", "mark_selection_end", "Mark End"),
        ("l", "load_file", "Load File"),
        ("q", "app_quit", "Quit"),
    ]
    
    def compose(self) -> ComposeResult:
        """Create main layout."""
        yield Header()
        yield CodeAssistantApp()
        yield Footer()
    
    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
    
    def action_new_file(self) -> None:
        """Create a new file (delegates to CodeAssistantApp)."""
        try:
            app = self.query_one(CodeAssistantApp)
            app.action_new_file()
        except Exception as e:
            self.notify(f"❌ Error: {e}", severity="error", timeout=5)
    
    def action_save_current_file(self) -> None:
        """Save current file (delegates to CodeAssistantApp)."""
        try:
            app = self.query_one(CodeAssistantApp)
            app.action_save_current_file()
        except Exception as e:
            self.notify(f"❌ Error: {e}", severity="error", timeout=5)
    
    def action_understand_project(self) -> None:
        """Understand project (delegates to CodeAssistantApp)."""
        try:
            app = self.query_one(CodeAssistantApp)
            app.action_understand_project()
        except Exception as e:
            self.notify(f"❌ Error: {e}", severity="error", timeout=5)
    
    def action_focus_next(self) -> None:
        """Focus next (delegates to CodeAssistantApp)."""
        try:
            app = self.query_one(CodeAssistantApp)
            app.action_focus_next()
        except Exception as e:
            pass
    
    def action_focus_previous(self) -> None:
        """Focus previous (delegates to CodeAssistantApp)."""
        try:
            app = self.query_one(CodeAssistantApp)
            app.action_focus_previous()
        except Exception as e:
            pass
    
    def action_select_cursor(self) -> None:
        """Select cursor (delegates to CodeAssistantApp)."""
        try:
            app = self.query_one(CodeAssistantApp)
            app.action_select_cursor()
        except Exception as e:
            pass
    
    def action_cursor_up(self) -> None:
        """Move cursor up (delegates to CodeAssistantApp)."""
        try:
            app = self.query_one(CodeAssistantApp)
            app.action_cursor_up()
        except Exception as e:
            pass
    
    def action_cursor_down(self) -> None:
        """Move cursor down (delegates to CodeAssistantApp)."""
        try:
            app = self.query_one(CodeAssistantApp)
            app.action_cursor_down()
        except Exception as e:
            pass
    
    def action_page_up(self) -> None:
        """Page up (delegates to CodeAssistantApp)."""
        try:
            app = self.query_one(CodeAssistantApp)
            app.action_page_up()
        except Exception as e:
            pass
    
    def action_page_down(self) -> None:
        """Page down (delegates to CodeAssistantApp)."""
        try:
            app = self.query_one(CodeAssistantApp)
            app.action_page_down()
        except Exception as e:
            pass
    
    def action_focus_browser(self) -> None:
        """Focus browser (delegates to CodeAssistantApp)."""
        try:
            app = self.query_one(CodeAssistantApp)
            app.action_focus_browser()
        except Exception as e:
            pass
    
    def action_focus_preview(self) -> None:
        """Focus preview (delegates to CodeAssistantApp)."""
        try:
            app = self.query_one(CodeAssistantApp)
            app.action_focus_preview()
        except Exception as e:
            pass
    
    def action_focus_chat(self) -> None:
        """Focus chat (delegates to CodeAssistantApp)."""
        try:
            app = self.query_one(CodeAssistantApp)
            app.action_focus_chat()
        except Exception as e:
            pass
    
    def action_focus_ai_background(self) -> None:
        """Focus AI background (delegates to CodeAssistantApp)."""
        try:
            app = self.query_one(CodeAssistantApp)
            app.action_focus_ai_background()
        except Exception as e:
            pass
    
    def action_focus_input(self) -> None:
        """Focus input (delegates to CodeAssistantApp)."""
        try:
            app = self.query_one(CodeAssistantApp)
            app.action_focus_input()
        except Exception as e:
            pass
    
    def action_focus_shell(self) -> None:
        """Focus shell (delegates to CodeAssistantApp)."""
        try:
            app = self.query_one(CodeAssistantApp)
            app.action_focus_shell()
        except Exception as e:
            pass
    
    def action_open_prompts(self) -> None:
        """Open prompts (delegates to CodeAssistantApp)."""
        try:
            app = self.query_one(CodeAssistantApp)
            app.action_open_prompts()
        except Exception as e:
            self.notify(f"❌ Error: {e}", severity="error", timeout=5)
    
    def action_load_context(self) -> None:
        """Load context (delegates to CodeAssistantApp)."""
        try:
            app = self.query_one(CodeAssistantApp)
            app.action_load_context()
        except Exception as e:
            self.notify(f"❌ Error: {e}", severity="error", timeout=5)
    
    def action_open_logs(self) -> None:
        """Open logs (delegates to CodeAssistantApp)."""
        try:
            app = self.query_one(CodeAssistantApp)
            app.action_open_logs()
        except Exception as e:
            self.notify(f"❌ Error: {e}", severity="error", timeout=5)
    
    def action_mark_selection_start(self) -> None:
        """Mark selection start (delegates to CodeAssistantApp)."""
        try:
            app = self.query_one(CodeAssistantApp)
            app.action_mark_selection_start()
        except Exception as e:
            pass
    
    def action_mark_selection_end(self) -> None:
        """Mark selection end (delegates to CodeAssistantApp)."""
        try:
            app = self.query_one(CodeAssistantApp)
            app.action_mark_selection_end()
        except Exception as e:
            pass
    
    def action_load_file(self) -> None:
        """Load file (delegates to CodeAssistantApp)."""
        try:
            app = self.query_one(CodeAssistantApp)
            app.action_load_file()
        except Exception as e:
            self.notify(f"❌ Error: {e}", severity="error", timeout=5)
    
    def action_app_quit(self) -> None:
        """Quit app (delegates to CodeAssistantApp)."""
        try:
            app = self.query_one(CodeAssistantApp)
            app.action_app_quit()
        except Exception as e:
            self.app.exit()


class CodeAssistantTUI(App):
    """Main Textual application."""
    
    def on_mount(self) -> None:
        """Install main screen."""
        self.push_screen(CodeAssistantMain())


def main() -> None:
    """Entry point for TUI."""
    app = CodeAssistantTUI()
    app.run()

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
        ("q", "quit", "Quit"),
    ]
    
    def compose(self) -> ComposeResult:
        """Create main layout."""
        yield Header()
        yield CodeAssistantApp()
        yield Footer()
    
    def action_quit(self) -> None:
        """Quit the application."""
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

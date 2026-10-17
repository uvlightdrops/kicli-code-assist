"""Command palette widget for shell command suggestions."""

from textual.widgets import Static, OptionList
from textual.containers import Vertical, Container
from textual.widgets.option_list import Option
from textual.reactive import reactive


class CommandPalette(Vertical):
    """Dropdown command palette with shell command suggestions."""
    
    DEFAULT_CSS = """
    CommandPalette {
        height: auto;
        width: 100%;
        offset: 0 0;
        border: solid $primary;
        background: $panel;
        display: none;
    }
    
    CommandPalette > OptionList {
        height: auto;
        max-height: 10;
        width: 100%;
        background: $panel;
        color: $text;
    }
    
    CommandPalette.visible {
        display: block;
    }
    """
    
    # Common shell commands grouped by category
    COMMANDS = {
        "file": {
            "ls": "List directory contents",
            "cat": "Display file contents",
            "cp": "Copy files or directories",
            "mv": "Move or rename files",
            "rm": "Remove files",
            "mkdir": "Create directory",
            "pwd": "Print working directory",
            "find": "Search for files",
            "grep": "Search text patterns",
            "sed": "Stream editor",
            "awk": "Text processing",
            "head": "Show first lines",
            "tail": "Show last lines",
            "wc": "Word/line count",
        },
        "system": {
            "ps": "List running processes",
            "top": "Monitor system resources",
            "df": "Show disk usage",
            "du": "Show directory size",
            "free": "Show memory usage",
            "uname": "System information",
            "whoami": "Current user",
            "date": "Show current date/time",
            "echo": "Print text",
            "chmod": "Change permissions",
            "chown": "Change owner",
            "sudo": "Execute as superuser",
        },
        "network": {
            "ping": "Test network connectivity",
            "curl": "Download files/test URLs",
            "wget": "Download files",
            "ssh": "Secure shell",
            "scp": "Secure copy",
            "netstat": "Network statistics",
            "ifconfig": "Network config",
        },
        "git": {
            "git status": "Show repository status",
            "git add": "Stage files",
            "git commit": "Commit changes",
            "git push": "Push to remote",
            "git pull": "Pull from remote",
            "git log": "Show commit history",
            "git diff": "Show differences",
            "git branch": "Manage branches",
            "git checkout": "Switch branches",
            "git clone": "Clone repository",
        },
        "dev": {
            "python": "Run Python interpreter",
            "pip": "Python package manager",
            "npm": "Node package manager",
            "docker": "Container management",
            "make": "Build automation",
            "npm run": "Run npm scripts",
            "yarn": "Yarn package manager",
        }
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.all_commands = self._flatten_commands()
        self.selected_index = 0
        self.visible = False
        
    def _flatten_commands(self) -> list[tuple[str, str]]:
        """Flatten commands dict into [(name, description), ...] list."""
        result = []
        for category in self.COMMANDS.values():
            for cmd, desc in category.items():
                result.append((cmd, f"{cmd} - {desc}"))
        return sorted(result, key=lambda x: x[0])
    
    def compose(self):
        """Compose the palette."""
        self.option_list = OptionList(*[
            Option(desc, id=cmd) for cmd, desc in self.all_commands
        ])
        yield self.option_list
    
    def on_mount(self) -> None:
        """Setup after mount."""
        self.option_list.focus()
    
    def filter_commands(self, query: str) -> None:
        """Filter commands by query string and show palette."""
        if not query.strip():
            self.hide()
            return
        
        query_lower = query.lower()
        filtered = [
            (cmd, desc) for cmd, desc in self.all_commands
            if cmd.startswith(query_lower) or query_lower in cmd
        ]
        
        if filtered:
            # Update options
            self.option_list.clear_options()
            for cmd, desc in filtered[:10]:  # Max 10 suggestions
                self.option_list.add_option(Option(desc, id=cmd))
            
            self.selected_index = 0
            self.option_list.highlighted = 0
            self.show()
        else:
            self.hide()
    
    def show(self) -> None:
        """Show the palette."""
        if not self.visible:
            self.visible = True
            self.add_class("visible")
            self.display = True
    
    def hide(self) -> None:
        """Hide the palette."""
        if self.visible:
            self.visible = False
            self.remove_class("visible")
            self.display = False
    
    def get_selected_command(self) -> str | None:
        """Get the currently selected command."""
        if self.option_list.option_list:
            highlighted = self.option_list.highlighted
            if 0 <= highlighted < len(self.option_list.option_list):
                return self.option_list.option_list[highlighted].id
        return None
    
    def select_up(self) -> None:
        """Move selection up."""
        if self.visible and self.option_list.option_list:
            current = self.option_list.highlighted
            if current > 0:
                self.option_list.highlighted = current - 1
    
    def select_down(self) -> None:
        """Move selection down."""
        if self.visible and self.option_list.option_list:
            current = self.option_list.highlighted
            if current < len(self.option_list.option_list) - 1:
                self.option_list.highlighted = current + 1

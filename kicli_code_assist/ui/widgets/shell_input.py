"""Shell input widget with command history and current directory display."""

from textual.widgets import TextArea, Static
from textual.containers import Horizontal, Vertical
from textual.events import Key
from textual.reactive import reactive
from .command_history import CommandHistory
from .command_palette import CommandPalette
from .shell_prompt import ShellPrompt
import os


class CurrentDirectory(Static):
    """Display current working directory."""
    
    DEFAULT_CSS = """
    CurrentDirectory {
        height: 1;
        width: 100%;
        background: $boost;
        color: $text;
        border-bottom: solid $primary;
        padding: 0 1;
        content-align: left middle;
    }
    """
    
    cwd = reactive(os.getcwd())
    
    def render(self) -> str:
        """Render current directory."""
        home = os.path.expanduser("~")
        display_cwd = self.cwd.replace(home, "~")
        return f"📁 {display_cwd}"
    
    def update_cwd(self, new_cwd: str) -> None:
        """Update current working directory."""
        self.cwd = new_cwd
    
    def watch_cwd(self) -> None:
        """Update display when cwd changes."""
        self.update()


class ShellInput(TextArea):
    """Shell command input with history and command palette."""
    
    DEFAULT_CSS = """
    ShellInput {
        border: solid $primary;
        background: $panel;
        color: $text;
        min-height: 3;
    }
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.command_history = CommandHistory(max_items=100)
        self.language = "bash"  # Syntax highlighting for bash
        self.palette = None  # Will be set by parent
        self.prompt = None  # Will be set by parent
        self.palette_active = False
    
    def on_key(self, event: Key) -> None:
        """Handle key events for history navigation and palette."""
        # If palette is visible, handle arrow keys for navigation
        if self.palette and self.palette.visible:
            if event.key == "up":
                event.prevent_default()
                event.stop()
                self.palette.select_up()
                return
            elif event.key == "down":
                event.prevent_default()
                event.stop()
                self.palette.select_down()
                return
            elif event.key == "enter":
                # Select from palette
                event.prevent_default()
                event.stop()
                selected = self.palette.get_selected_command()
                if selected:
                    self.text = selected + " "
                    self.cursor_location = (0, len(self.text))
                    self.palette.hide()
                return
            elif event.key == "escape":
                # Close palette
                event.prevent_default()
                event.stop()
                self.palette.hide()
                return
        
        # Otherwise, normal history navigation
        if event.key == "up":
            # Check if we're at the beginning of input
            cursor_location = self.cursor_location
            if cursor_location[0] == 0:  # First line
                current_input = self.text
                previous = self.command_history.up(current_input)
                if previous is not None:
                    event.prevent_default()
                    event.stop()
                    self.text = previous
                    # Move cursor to end
                    self.cursor_location = (len(previous.split('\n')) - 1, len(previous.split('\n')[-1]))
                    return
        
        elif event.key == "down":
            # Check if we're at the end of input
            lines = self.text.split('\n')
            cursor_location = self.cursor_location
            if cursor_location[0] == len(lines) - 1:  # Last line
                next_cmd = self.command_history.down()
                if next_cmd is not None:
                    event.prevent_default()
                    event.stop()
                    self.text = next_cmd
                    # Move cursor to end
                    lines = next_cmd.split('\n')
                    self.cursor_location = (len(lines) - 1, len(lines[-1]))
                    return
        
        # Update palette filter as user types
        if self.palette and not event.key in ("up", "down", "enter", "escape"):
            self._update_palette()
    
    def _update_palette(self) -> None:
        """Update palette based on current input."""
        # Get first word of input (command)
        text = self.text.strip()
        first_word = text.split()[0] if text else ""
        
        # Filter palette
        if first_word:
            self.palette.filter_commands(first_word)
        else:
            self.palette.hide()
    
    def submit_command(self) -> str:
        """Submit command and return it."""
        command = self.text.strip()
        if command:
            self.command_history.add(command)
            self.text = ""
            if self.palette:
                self.palette.hide()
        return command
    
    def get_text(self) -> str:
        """Get current input text."""
        return self.text


class ShellPanel(Vertical):
    """Shell panel with input, history, current directory, and command palette."""
    
    DEFAULT_CSS = """
    ShellPanel {
        height: 100%;
        width: 100%;
    }
    
    ShellPanel > #shell_input_container {
        height: auto;
        width: 100%;
    }
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cwd_display = None
        self.input = None
        self.palette = None
        self.prompt = None
    
    def compose(self):
        """Compose the shell panel."""
        self.cwd_display = CurrentDirectory()
        yield self.cwd_display
        
        # Create container for palette
        with Vertical(id="shell_input_container"):
            self.palette = CommandPalette(id="command_palette")
            yield self.palette
            
            # Shell input line with prompt
            with Horizontal(id="shell_input_line"):
                self.prompt = ShellPrompt(id="shell_prompt")
                yield self.prompt
                
                self.input = ShellInput(id="shell_input", language="bash")
                self.input.palette = self.palette  # Link palette to input
                self.input.prompt = self.prompt  # Link prompt to input
                yield self.input
    
    def on_mount(self) -> None:
        """Setup after mount."""
        self.input.focus()
    
    def update_cwd(self, new_cwd: str) -> None:
        """Update current working directory."""
        if self.cwd_display:
            self.cwd_display.update_cwd(new_cwd)
    
    def get_command(self) -> str:
        """Get current command from input."""
        if self.input:
            return self.input.get_text()
        return ""
    
    def submit_command(self) -> str:
        """Submit command."""
        if self.input:
            return self.input.submit_command()
        return ""
    
    def set_command_waiting(self) -> None:
        """Set prompt to waiting state."""
        if self.prompt:
            self.prompt.set_waiting()
    
    def set_command_error(self) -> None:
        """Set prompt to error state."""
        if self.prompt:
            self.prompt.set_error()
    
    def set_command_ready(self) -> None:
        """Set prompt to ready state."""
        if self.prompt:
            self.prompt.set_ready()


"""Reusable command history manager for shell-like interfaces."""


class CommandHistory:
    """Manages history of submitted commands for shell-like interfaces."""
    
    def __init__(self, max_items: int = 100):
        """Initialize history manager.
        
        Args:
            max_items: Maximum number of commands to keep in history
        """
        self.commands = []
        self.max_items = max_items
        self.index = -1  # -1 means new input, 0+ means browsing history
        self.pending_input = ""  # Store input while browsing
    
    def add(self, command: str) -> None:
        """Add command to history.
        
        Args:
            command: Command string to add
        """
        if command.strip():
            # Remove duplicate if exists (put it at end)
            if command in self.commands:
                self.commands.remove(command)
            
            self.commands.append(command)
            
            # Trim history if too large
            if len(self.commands) > self.max_items:
                self.commands = self.commands[-self.max_items:]
        
        # Reset index when adding
        self.index = -1
        self.pending_input = ""
    
    def up(self, current_input: str = "") -> str | None:
        """Get previous command from history.
        
        Args:
            current_input: Current input to save as pending
            
        Returns:
            Previous command, or None if at start of history
        """
        if not self.commands:
            return None
        
        # Save current input if we're starting to browse
        if self.index == -1:
            self.pending_input = current_input
        
        # Move back in history
        if self.index < len(self.commands) - 1:
            self.index += 1
            return self.commands[-(self.index + 1)]
        
        return None
    
    def down(self) -> str | None:
        """Get next command from history (or restore pending input).
        
        Returns:
            Next command, or pending input if at end of history
        """
        if not self.commands or self.index == -1:
            return None
        
        # Move forward in history
        if self.index > 0:
            self.index -= 1
            return self.commands[-(self.index + 1)]
        else:
            # Back to pending input
            self.index = -1
            return self.pending_input
    
    def get_last(self) -> str | None:
        """Get last command (without browsing)."""
        if self.commands:
            return self.commands[-1]
        return None
    
    def clear(self) -> None:
        """Clear all history."""
        self.commands.clear()
        self.index = -1
        self.pending_input = ""

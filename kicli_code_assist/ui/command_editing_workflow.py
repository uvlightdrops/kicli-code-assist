"""Integration handlers for command editing and manual entry in TUI.

Bridges ShellCommandEditor modals with TUI chat application.
"""

from typing import Optional, Callable
from kicli_code_assist.executor.shell_execution import ShellCommandBatch, ShellCommand


class CommandEditingWorkflow:
    """Manages the command editing workflow in TUI.
    
    Coordinates:
    1. Show approval modal with Edit button
    2. User clicks Edit → show CommandEditor for selected command
    3. User saves edits → update batch
    4. Show updated batch in modal
    5. User can continue editing or approve
    """
    
    def __init__(self):
        self.current_batch: Optional[ShellCommandBatch] = None
        self.editing_index: int = 0
    
    def set_batch(self, batch: ShellCommandBatch) -> None:
        """Store batch for editing.
        
        Args:
            batch: Current batch to edit
        """
        self.current_batch = batch
    
    def get_edited_batch(self) -> Optional[ShellCommandBatch]:
        """Get the current (possibly edited) batch.
        
        Returns:
            Current batch or None if not set
        """
        return self.current_batch
    
    def update_command_at_index(self, index: int, edited_command: ShellCommand) -> bool:
        """Replace command at index with edited version.
        
        Args:
            index: Index of command to replace
            edited_command: New command
            
        Returns:
            True if successful
        """
        if not self.current_batch or index >= len(self.current_batch.commands):
            return False
        
        self.current_batch.commands[index] = edited_command
        return True
    
    def add_command(self, command: ShellCommand) -> bool:
        """Add new command to batch.
        
        Args:
            command: Command to add
            
        Returns:
            True if successful
        """
        if not self.current_batch:
            return False
        
        self.current_batch.commands.append(command)
        return True
    
    def add_commands(self, commands: list[ShellCommand]) -> bool:
        """Add multiple commands to batch.
        
        Args:
            commands: Commands to add
            
        Returns:
            True if successful
        """
        if not self.current_batch:
            return False
        
        self.current_batch.commands.extend(commands)
        return True
    
    def remove_command_at_index(self, index: int) -> bool:
        """Remove command at index.
        
        Args:
            index: Index to remove
            
        Returns:
            True if successful
        """
        if not self.current_batch or len(self.current_batch.commands) <= 1:
            return False
        
        if index >= len(self.current_batch.commands):
            return False
        
        self.current_batch.commands.pop(index)
        return True
    
    def move_command(self, from_index: int, to_index: int) -> bool:
        """Move command from one index to another.
        
        Args:
            from_index: Current index
            to_index: Target index
            
        Returns:
            True if successful
        """
        if not self.current_batch:
            return False
        
        if from_index >= len(self.current_batch.commands):
            return False
        
        if to_index >= len(self.current_batch.commands) or to_index < 0:
            return False
        
        cmd = self.current_batch.commands.pop(from_index)
        self.current_batch.commands.insert(to_index, cmd)
        return True


class ManualCommandEntry:
    """Handles manual command entry from user.
    
    Supports:
    - Single-line commands
    - Multi-line scripts
    - Comment filtering
    - Risk preview
    """
    
    @staticmethod
    def parse_command_input(text: str) -> Optional[ShellCommandBatch]:
        """Parse user input into command batch.
        
        Supports:
        - One command per line
        - Multi-line scripts
        - Comments (# prefix, ignored)
        - Empty lines (ignored)
        
        Args:
            text: Raw user input
            
        Returns:
            ShellCommandBatch or None if no commands found
        """
        if not text or not text.strip():
            return None
        
        commands = []
        lines = text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            cmd = ShellCommand(
                command=line,
                description="Manually entered command"
            )
            commands.append(cmd)
        
        if not commands:
            return None
        
        return ShellCommandBatch(commands=commands)
    
    @staticmethod
    def format_for_display(batch: ShellCommandBatch) -> str:
        """Format batch for display with risks.
        
        Args:
            batch: Command batch
            
        Returns:
            Formatted string for display
        """
        lines = ["[bold cyan]📝 Entered Commands:[/]"]
        
        for i, cmd in enumerate(batch.commands, 1):
            risk_emoji = {
                "low": "🟢",
                "medium": "🟡",
                "high": "🟠",
                "critical": "🔴",
            }.get(cmd.get_risk_level().value, "⚪")
            
            lines.append(f"[{i}] {risk_emoji} [cyan]{cmd.command}[/]")
        
        return "\n".join(lines)


class CommandEditorUI:
    """Handler for showing and managing command editor dialogs in TUI."""
    
    def __init__(self, on_edit_complete: Optional[Callable] = None):
        """Initialize editor UI handler.
        
        Args:
            on_edit_complete: Callback when edit is done
        """
        self.on_edit_complete = on_edit_complete
        self.editing_index = 0
    
    def show_editor_for_command(self, command: ShellCommand, index: int) -> None:
        """Show editor modal for a command.
        
        Args:
            command: Command to edit
            index: Index in batch
        """
        self.editing_index = index
        # In TUI context: self.app.push_screen(CommandEditor(command))
    
    def show_manual_entry_dialog(self) -> None:
        """Show manual command entry dialog.
        
        In TUI context: self.app.push_screen(CommandManualEntryDialog())
        """
        pass


class CommandBatchInteractiveEditor:
    """Full interactive editing session for a command batch.
    
    Workflow:
    1. User opens editor
    2. Can view all commands in batch
    3. Can edit individual commands
    4. Can add new commands
    5. Can remove commands
    6. Can reorder commands
    7. Changes reflected in approval modal
    """
    
    def __init__(self, initial_batch: ShellCommandBatch):
        """Initialize batch editor.
        
        Args:
            initial_batch: Batch to edit
        """
        self.batch = initial_batch
        self.original_batch = ShellCommandBatch(
            commands=[
                ShellCommand(
                    command=cmd.command,
                    description=cmd.description,
                    cwd=cmd.cwd,
                    timeout=cmd.timeout,
                    env_vars=cmd.env_vars.copy() if cmd.env_vars else {}
                )
                for cmd in initial_batch.commands
            ]
        )
        self.workflow = CommandEditingWorkflow()
        self.workflow.set_batch(self.batch)
    
    def get_changes_summary(self) -> dict:
        """Get summary of changes made.
        
        Returns:
            Dict with added, removed, modified, reordered counts
        """
        original_cmds = {cmd.command for cmd in self.original_batch.commands}
        current_cmds = {cmd.command for cmd in self.batch.commands}
        
        return {
            "added": len(current_cmds - original_cmds),
            "removed": len(original_cmds - current_cmds),
            "total_current": len(self.batch.commands),
            "total_original": len(self.original_batch.commands),
        }
    
    def reset_to_original(self) -> None:
        """Reset all changes and return to original batch."""
        self.batch.commands = [
            ShellCommand(
                command=cmd.command,
                description=cmd.description,
                cwd=cmd.cwd,
                timeout=cmd.timeout,
                env_vars=cmd.env_vars.copy() if cmd.env_vars else {}
            )
            for cmd in self.original_batch.commands
        ]
    
    def format_commands_for_approval_modal(self) -> str:
        """Format current batch for display in approval modal.
        
        Returns:
            Formatted string ready for display
        """
        lines = ["[bold cyan]Commands (After Edits):[/]"]
        
        for i, cmd in enumerate(self.batch.commands, 1):
            risk_emoji = {
                "low": "🟢",
                "medium": "🟡",
                "high": "🟠",
                "critical": "🔴",
            }.get(cmd.get_risk_level().value, "⚪")
            
            lines.append(f"{i}. {risk_emoji} {cmd.command}")
        
        changes = self.get_changes_summary()
        if changes["added"] > 0 or changes["removed"] > 0:
            lines.append("")
            lines.append(
                f"[dim]Changes: +{changes['added']}, -{changes['removed']} "
                f"(Total: {changes['total_current']} commands)[/]"
            )
        
        return "\n".join(lines)

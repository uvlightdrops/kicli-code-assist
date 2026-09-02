"""Diff viewer for code changes."""
import difflib
from dataclasses import dataclass
from typing import Optional
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.table import Table


@dataclass
class CodeChange:
    """Represents a code change (diff)."""
    filepath: str
    original: str
    modified: str
    language: str = "python"
    
    def get_diff_lines(self) -> list[str]:
        """Generate unified diff."""
        orig_lines = self.original.splitlines(keepends=True)
        mod_lines = self.modified.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            orig_lines,
            mod_lines,
            fromfile=self.filepath,
            tofile=self.filepath,
            lineterm=''
        )
        return list(diff)
    
    def get_side_by_side(self) -> tuple[str, str]:
        """Get original and modified code for side-by-side display."""
        return self.original, self.modified


class DiffViewer:
    """Display code diffs in rich format."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
    
    def show_diff(self, change: CodeChange) -> None:
        """Display diff in terminal."""
        diff_lines = change.get_diff_lines()
        
        # Build colored diff
        colored_output = []
        for line in diff_lines:
            if line.startswith('+++') or line.startswith('---'):
                colored_output.append(f"[bold blue]{line}[/bold blue]")
            elif line.startswith('+'):
                colored_output.append(f"[green]{line}[/green]")
            elif line.startswith('-'):
                colored_output.append(f"[red]{line}[/red]")
            elif line.startswith('@@'):
                colored_output.append(f"[cyan]{line}[/cyan]")
            else:
                colored_output.append(line)
        
        # Display
        panel = Panel(
            "\n".join(colored_output),
            title=f"[bold]{change.filepath}[/bold]",
            expand=False
        )
        self.console.print(panel)
    
    def show_side_by_side(self, change: CodeChange) -> None:
        """Display original and modified code side-by-side."""
        orig, mod = change.get_side_by_side()
        
        # Create table
        table = Table(title=f"Changes in {change.filepath}")
        table.add_column("Original", style="red", width=40)
        table.add_column("Modified", style="green", width=40)
        
        orig_lines = orig.splitlines()
        mod_lines = mod.splitlines()
        max_lines = max(len(orig_lines), len(mod_lines))
        
        for i in range(max_lines):
            orig_line = orig_lines[i] if i < len(orig_lines) else ""
            mod_line = mod_lines[i] if i < len(mod_lines) else ""
            table.add_row(orig_line, mod_line)
        
        self.console.print(table)
    
    def show_code(self, code: str, language: str = "python") -> None:
        """Display code with syntax highlighting."""
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        self.console.print(syntax)

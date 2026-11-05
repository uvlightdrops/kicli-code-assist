"""Unified agent output panel - displays results from all agent modes."""

from textual.widgets import Static
from textual.containers import Container
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from typing import Dict, Any, Optional
import json


class AgentOutputPanel(Container):
    """Display results: Explain, Suggest, Reason, Refactor, Metrics, etc."""
    
    DEFAULT_CSS = """
    AgentOutputPanel {
        width: 1fr;
        height: 1fr;
        border: solid $accent;
        overflow: auto;
    }
    
    AgentOutputPanel > Static {
        width: 100%;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.output = Static(id="output-text")
        self.console = Console(record=True)
    
    def compose(self):
        """Create output display."""
        yield self.output
    
    def render_event(self, event: Dict[str, Any]) -> None:
        """Render agent event to output panel."""
        event_type = event.get("event_type", "unknown")
        
        if event_type == "error":
            self._render_error(event.get("message", "Unknown error"))
        
        elif event_type == "reasoning_start":
            self._render_reasoning_start(event)
        
        elif event_type == "reasoning_step":
            self._render_reasoning_step(event)
        
        elif event_type == "explain_result":
            self._render_explain(event)
        
        elif event_type == "refactor_result":
            self._render_refactor(event)
        
        elif event_type == "metrics_result":
            self._render_metrics(event)
        
        elif event_type == "raw_text":
            self._render_text(event.get("text", ""))
        
        elif event_type == "loading":
            self._render_loading(event.get("message", "Processing..."))
        
        else:
            self._render_text(f"[dim]{event_type}: {json.dumps(event)}[/dim]")
    
    def _render_error(self, message: str) -> None:
        """Render error message."""
        self.console.print(Panel(message, style="red", title="❌ Error"))
        self.output.update(self.console.export_text())
    
    def _render_loading(self, message: str) -> None:
        """Render loading state."""
        self.console.print(f"[yellow]⏳ {message}[/yellow]")
        self.output.update(self.console.export_text())
    
    def _render_reasoning_start(self, event: Dict) -> None:
        """Render start of reasoning trace."""
        title = event.get("title", "Agent Reasoning")
        self.console.print(Panel(f"[cyan]{title}[/cyan]", style="blue"))
    
    def _render_reasoning_step(self, event: Dict) -> None:
        """Render single reasoning step."""
        step_type = event.get("step_type", "")
        content = event.get("content", "")
        
        if step_type == "decision":
            self.console.print(f"[yellow]→ Decision:[/yellow] {content}")
        elif step_type == "action":
            self.console.print(f"[cyan]⚙ Action:[/cyan] {content}")
        elif step_type == "result":
            self.console.print(f"[green]✓ Result:[/green] {content}")
        else:
            self.console.print(f"[dim]{step_type}:[/dim] {content}")
        
        self.output.update(self.console.export_text())
    
    def _render_explain(self, event: Dict) -> None:
        """Render code explanation result."""
        explanation = event.get("explanation", "")
        code_snippet = event.get("code_snippet", "")
        language = event.get("language", "python")
        
        self.console.print(Panel("[bold cyan]Code Explanation[/bold cyan]"))
        self.console.print(explanation)
        
        if code_snippet:
            syntax = Syntax(code_snippet, language, theme="monokai", line_numbers=True)
            self.console.print(syntax)
        
        self.output.update(self.console.export_text())
    
    def _render_refactor(self, event: Dict) -> None:
        """Render refactoring suggestions."""
        suggestions = event.get("suggestions", [])
        
        self.console.print(Panel("[bold cyan]Refactoring Suggestions[/bold cyan]"))
        
        for i, suggestion in enumerate(suggestions, 1):
            title = suggestion.get("title", f"Suggestion {i}")
            description = suggestion.get("description", "")
            before = suggestion.get("before_code", "")
            after = suggestion.get("after_code", "")
            
            self.console.print(f"\n[yellow]{i}. {title}[/yellow]")
            self.console.print(description)
            
            if before:
                self.console.print("[red]Before:[/red]")
                self.console.print(Syntax(before, "python", theme="monokai", line_numbers=True))
            
            if after:
                self.console.print("[green]After:[/green]")
                self.console.print(Syntax(after, "python", theme="monokai", line_numbers=True))
        
        self.output.update(self.console.export_text())
    
    def _render_metrics(self, event: Dict) -> None:
        """Render code metrics."""
        metrics = event.get("metrics", {})
        
        self.console.print(Panel("[bold cyan]Code Metrics[/bold cyan]"))
        
        table = Table(title="Analysis Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in metrics.items():
            table.add_row(key, str(value))
        
        self.console.print(table)
        self.output.update(self.console.export_text())
    
    def _render_text(self, text: str) -> None:
        """Render plain text."""
        self.console.print(text)
        self.output.update(self.console.export_text())
    
    def clear(self) -> None:
        """Clear output."""
        self.console = Console(record=True)
        self.output.update("")

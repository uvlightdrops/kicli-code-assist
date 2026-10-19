"""Debug chat panel for direct OpenAI testing."""

import asyncio
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static, RichLog
from rich.console import Console


class DebugChatPanel(Static):
    """Direct OpenAI chat for debugging."""

    def __init__(self, llm_integration=None, **kwargs):
        super().__init__(**kwargs)
        self.llm_integration = llm_integration
        self.log_display = None
        self.message_count = 0

    def compose(self) -> ComposeResult:
        """Create debug chat UI."""
        with Vertical():
            self.log_display = RichLog(highlight=False, markup=True)
            yield self.log_display

    def on_mount(self) -> None:
        """Initialize on mount."""
        if self.log_display:
            self.log_display.write("[bold cyan]💻 Debug Chat - Direct OpenAI Access[/]\n")
            self.log_display.write("[yellow]Type messages and press Enter to send[/]\n")
            self.log_display.write("─" * 80 + "\n\n")

    async def send_message(self, message: str) -> None:
        """Send message to OpenAI and display response."""
        if not self.llm_integration or not self.llm_integration.provider_chain:
            self.log_display.write("[red]✗ No LLM provider configured[/]\n")
            return

        self.message_count += 1
        self.log_display.write(f"[green]>>> Message #{self.message_count}:[/] {message}\n")
        self.log_display.write("[dim]⏳ Waiting for response...[/]\n")

        try:
            # Query OpenAI asynchronously
            response = await self.llm_integration.query(
                messages=[{"role": "user", "content": message}],
                system_prompt="You are a helpful assistant."
            )

            self.log_display.write(f"[cyan]<<< Response:[/]\n{response}\n")
            self.log_display.write("[dim]" + "─" * 80 + "[/]\n\n")
        except Exception as e:
            self.log_display.write(f"[red]✗ Error: {e}[/]\n")
            self.log_display.write("[dim]" + "─" * 80 + "[/]\n\n")

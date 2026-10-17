"""Processing spinner widget for async LLM operations."""

from textual.widgets import Static
from textual.reactive import reactive


class Spinner(Static):
    """Animated spinner showing processing status."""

    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    
    status = reactive("Processing...", init=False)
    frame_index = reactive(0, init=False)
    visible = reactive(False, init=False)

    def __init__(self, initial_status: str = "Processing..."):
        """Initialize spinner.
        
        Args:
            initial_status: Initial status message
        """
        super().__init__()
        self.status = initial_status

    def render(self) -> str:
        """Render spinner frame."""
        if not self.visible:
            return ""
        
        frame = self.FRAMES[self.frame_index % len(self.FRAMES)]
        return f"{frame} {self.status}"

    def start(self, status: str = "Processing...") -> None:
        """Start the spinner animation.
        
        Args:
            status: Status message to display
        """
        self.status = status
        self.visible = True
        self.frame_index = 0
        self._animate()

    def stop(self) -> None:
        """Stop the spinner animation."""
        self.visible = False

    async def _animate(self) -> None:
        """Animate spinner frames."""
        while self.visible:
            self.frame_index += 1
            self.refresh()
            await self._wait(0.1)  # 100ms per frame

    async def _wait(self, seconds: float) -> None:
        """Async wait helper."""
        import asyncio
        await asyncio.sleep(seconds)

    def update_status(self, status: str) -> None:
        """Update status message.
        
        Args:
            status: New status message
        """
        self.status = status
        self.refresh()

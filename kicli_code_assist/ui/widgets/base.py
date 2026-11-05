"""
Base TUI Widget Class

All TUI widgets inherit from this base class.
"""

from textual.containers import Container
from textual.reactive import reactive
import logging

logger = logging.getLogger(__name__)


class TUIWidget(Container):
    """Base class for all TUI widgets.
    
    Provides common functionality:
    - Configuration
    - State management
    - Error handling
    - Logging
    """
    
    # Observable state
    is_loading = reactive(False)
    error_message = reactive("")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def set_loading(self, loading: bool) -> None:
        """Set loading state."""
        self.is_loading = loading
    
    def set_error(self, message: str) -> None:
        """Set error state and message."""
        self.error_message = message
        self.logger.error(message)
    
    def clear_error(self) -> None:
        """Clear error state."""
        self.error_message = ""
    
    def log_debug(self, message: str) -> None:
        """Log debug message."""
        self.logger.debug(message)
    
    def log_info(self, message: str) -> None:
        """Log info message."""
        self.logger.info(message)

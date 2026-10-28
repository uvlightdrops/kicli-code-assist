"""Server management module for kicli-code-assist.

Handles service registration, lifecycle management, and process tracking.
"""

from .registry import ServiceRegistry
from .detector import ServiceDetector
from .orphan import OrphanDetector

__all__ = ["ServiceRegistry", "ServiceDetector", "OrphanDetector"]

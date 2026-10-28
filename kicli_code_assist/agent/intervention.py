"""Intervention queue for pausing, resuming, and redirecting agent execution.

Handles commands from multiple sources (WebUI, CLI supervisor) with
configurable priority strategies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Any, Dict
from queue import PriorityQueue
import logging

logger = logging.getLogger("kicli-agent-intervention")


class InterventionType(str, Enum):
    """Type of intervention command."""
    PAUSE = "pause"
    RESUME = "resume"
    REDIRECT = "redirect"
    ROLLBACK = "rollback"


class InterventionSource(str, Enum):
    """Source of intervention command."""
    WEBUI = "webui"
    SUPERVISOR = "supervisor"
    INTERNAL = "internal"


class InterventionMode(str, Enum):
    """Strategy for handling conflicting interventions."""
    QUEUE = "queue"              # First-come-first-served
    SUPERVISOR = "supervisor"    # CLI supervisor always wins
    USER_PROMPT = "user_prompt"  # Ask user when conflict occurs


@dataclass
class InterventionCommand:
    """A command to intervene in agent execution."""
    command_id: str
    timestamp: datetime
    intervention_type: InterventionType
    source: InterventionSource
    reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Priority calculation
    # Supervisor commands get priority if mode == "supervisor"
    # Earlier timestamps get priority if mode == "queue"
    def priority_key(self, mode: InterventionMode) -> tuple:
        """Calculate priority key for queue ordering.
        
        Returns:
            Tuple for use with PriorityQueue (lower = higher priority)
        """
        if mode == InterventionMode.SUPERVISOR:
            # Supervisor commands (value 0) before WebUI (value 1)
            source_priority = 0 if self.source == InterventionSource.SUPERVISOR else 1
            return (source_priority, self.timestamp.timestamp())
        else:
            # mode == QUEUE or mode == USER_PROMPT: FIFO
            return (self.timestamp.timestamp(),)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict."""
        return {
            "command_id": self.command_id,
            "timestamp": self.timestamp.isoformat(),
            "intervention_type": self.intervention_type.value,
            "source": self.source.value,
            "reason": self.reason,
            "metadata": self.metadata,
        }


@dataclass
class InterventionConflict:
    """Conflict when multiple commands are pending."""
    primary_command: InterventionCommand
    conflicting_commands: List[InterventionCommand]
    mode: InterventionMode
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict."""
        return {
            "primary_command": self.primary_command.to_dict(),
            "conflicting_commands": [cmd.to_dict() for cmd in self.conflicting_commands],
            "mode": self.mode.value,
        }


class InterventionQueue:
    """Queue for managing intervention commands.
    
    Supports multiple sources (WebUI, CLI supervisor) with configurable
    conflict resolution strategies.
    """
    
    def __init__(self, mode: InterventionMode = InterventionMode.USER_PROMPT):
        """Initialize intervention queue.
        
        Args:
            mode: Strategy for handling conflicting commands
        """
        self.mode = mode
        self._queue: PriorityQueue = PriorityQueue()
        self._command_counter = 0
    
    def enqueue(
        self,
        intervention_type: InterventionType,
        source: InterventionSource,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> InterventionCommand:
        """Add command to queue.
        
        Args:
            intervention_type: Type of intervention
            source: Source of command (WebUI or Supervisor)
            reason: Optional reason for intervention
            metadata: Optional additional data
            
        Returns:
            The created InterventionCommand
        """
        cmd = InterventionCommand(
            command_id=f"cmd-{self._command_counter}",
            timestamp=datetime.now(),
            intervention_type=intervention_type,
            source=source,
            reason=reason,
            metadata=metadata or {},
        )
        self._command_counter += 1
        
        priority_key = cmd.priority_key(self.mode)
        self._queue.put((priority_key, cmd))
        
        logger.debug(
            f"Enqueued {intervention_type.value} from {source.value}: {reason}"
        )
        return cmd
    
    def dequeue(self) -> Optional[InterventionCommand]:
        """Get next command from queue.
        
        Returns:
            Next InterventionCommand or None if queue is empty
        """
        if self._queue.empty():
            return None
        
        _, cmd = self._queue.get()
        logger.debug(f"Dequeued {cmd.intervention_type.value}: {cmd.reason}")
        return cmd
    
    def peek(self) -> Optional[InterventionCommand]:
        """Peek at next command without removing it.
        
        Returns:
            Next InterventionCommand or None if queue is empty
        """
        if self._queue.empty():
            return None
        
        # PriorityQueue doesn't have a direct peek, so we get and re-add
        _, cmd = self._queue.get()
        self._queue.put((cmd.priority_key(self.mode), cmd))
        return cmd
    
    def has_pending(self) -> bool:
        """Check if there are pending commands."""
        return not self._queue.empty()
    
    def pending_count(self) -> int:
        """Get count of pending commands."""
        return self._queue.qsize()
    
    def check_for_conflict(self) -> Optional[InterventionConflict]:
        """Check if there's a conflict in pending commands.
        
        A conflict occurs when:
        - Multiple PAUSE commands from different sources
        - PAUSE and RESUME from different sources
        - REDIRECT and other commands from different sources
        
        Returns:
            InterventionConflict if conflict detected, None otherwise
        """
        if self._queue.qsize() < 2:
            return None
        
        # Collect all commands
        commands = []
        temp_queue = []
        while not self._queue.empty():
            priority, cmd = self._queue.get()
            commands.append(cmd)
            temp_queue.append((priority, cmd))
        
        # Re-add to queue
        for priority, cmd in temp_queue:
            self._queue.put((priority, cmd))
        
        # Check for conflicts
        sources = {cmd.source for cmd in commands}
        if len(sources) > 1:
            # Multiple sources: potential conflict
            primary = commands[0]
            conflicting = commands[1:]
            return InterventionConflict(
                primary_command=primary,
                conflicting_commands=conflicting,
                mode=self.mode,
            )
        
        return None
    
    def set_mode(self, mode: InterventionMode) -> None:
        """Change intervention mode dynamically.
        
        Re-sorts queue according to new mode.
        """
        if mode == self.mode:
            return
        
        old_mode = self.mode
        self.mode = mode
        
        # Re-sort queue
        commands = []
        while not self._queue.empty():
            _, cmd = self._queue.get()
            commands.append(cmd)
        
        for cmd in commands:
            priority_key = cmd.priority_key(self.mode)
            self._queue.put((priority_key, cmd))
        
        logger.info(f"Changed intervention mode: {old_mode.value} → {mode.value}")
    
    def clear(self) -> None:
        """Clear all pending commands."""
        while not self._queue.empty():
            self._queue.get()
        logger.debug("Intervention queue cleared")
    
    def to_dict(self) -> Dict[str, Any]:
        """Get queue state as dict."""
        commands = []
        temp_queue = []
        while not self._queue.empty():
            priority, cmd = self._queue.get()
            commands.append(cmd.to_dict())
            temp_queue.append((priority, cmd))
        
        # Re-add to queue
        for priority, cmd in temp_queue:
            self._queue.put((priority, cmd))
        
        return {
            "mode": self.mode.value,
            "pending_count": len(commands),
            "commands": commands,
        }

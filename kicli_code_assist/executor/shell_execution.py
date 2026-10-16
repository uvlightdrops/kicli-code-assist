"""Shell command execution types and HITL approval workflow.

Implements structured function calling for shell commands with:
- Type safety and schema validation
- Risk classification
- Human-in-the-Loop (HITL) approval gates
- Immutable audit trails
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Literal
from uuid import uuid4
import hashlib


class RiskLevel(str, Enum):
    """Risk classification for shell commands."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalDecision(str, Enum):
    """Approval outcome."""
    APPROVED = "approved"
    REJECTED = "rejected"
    APPROVED_EDITED = "approved_edited"
    PENDING = "pending"


class SessionPermissionLevel(str, Enum):
    """Shell execution permission level for session."""
    NONE = "none"  # No execution allowed
    BATCH = "batch"  # Approve each batch individually
    SESSION = "session"  # Auto-approve all after initial session approval


# Risk pattern definitions (from research doc)
RISK_PATTERNS = {
    RiskLevel.CRITICAL: [
        r"rm\s+-rf\s+/",  # rm -rf /
        r"mkfs\.",  # Format filesystem
        r"dd\s+if=.*of=",  # Dangerous dd operations
        r":\(\)\{:\|:\&\}",  # Fork bomb
        r"chmod\s+000\s+/",  # Remove all permissions from root
    ],
    RiskLevel.HIGH: [
        r"^rm\s+",  # rm in general
        r"^chmod\s+",  # Permission changes
        r"^chown\s+",  # Ownership changes
        r"^dd\s+",  # Disk operations
        r"^fdisk\s+",
        r"^parted\s+",
        r"^mkfs\s+",
        r"^mount\s+",
        r"^umount\s+",
        r">\s*/dev/",  # Write to device
    ],
    RiskLevel.MEDIUM: [
        r"^git\s+(commit|push|pull|rebase)",
        r"^pip\s+install",
        r"^pip\s+uninstall",
        r"^python\s+-m",
        r"^systemctl\s+(start|stop|restart)",
        r"^service\s+",
        r"^make\s+",
    ],
    RiskLevel.LOW: [
        r"^git\s+(status|log|diff|branch|tag)",
        r"^ls",
        r"^pwd",
        r"^cat\s+",
        r"^grep\s+",
        r"^find\s+",
        r"^head\s+",
        r"^tail\s+",
        r"^echo\s+",
        r"^date",
        r"^whoami",
    ],
}


def classify_risk(command: str) -> RiskLevel:
    """Classify shell command by risk level.
    
    Args:
        command: Shell command string
        
    Returns:
        RiskLevel classification
    """
    # Normalize whitespace
    normalized = command.strip()
    
    # Check from highest to lowest risk
    for level in [RiskLevel.CRITICAL, RiskLevel.HIGH, RiskLevel.MEDIUM, RiskLevel.LOW]:
        for pattern in RISK_PATTERNS[level]:
            if re.match(pattern, normalized, re.IGNORECASE):
                return level
    
    return RiskLevel.MEDIUM  # Default to medium if unknown


@dataclass
class ShellCommand:
    """Single shell command with metadata."""
    
    command: str
    description: str = ""
    timeout_seconds: int = 30
    working_dir: Optional[str] = None
    env_vars: Optional[dict] = None
    
    def classify_risk(self) -> RiskLevel:
        """Classify this command's risk level."""
        return classify_risk(self.command)
    
    def to_dict(self) -> dict:
        """Convert to dict for serialization."""
        return {
            "command": self.command,
            "description": self.description,
            "timeout_seconds": self.timeout_seconds,
            "working_dir": self.working_dir,
            "env_vars": self.env_vars,
        }


@dataclass
class ShellCommandBatch:
    """Batch of shell commands proposed by LLM for execution."""
    
    id: str = field(default_factory=lambda: f"batch_{uuid4().hex[:12]}")
    commands: list[ShellCommand] = field(default_factory=list)
    description: str = ""
    estimated_duration_ms: int = 0
    rollback_commands: Optional[list[ShellCommand]] = None
    
    def calculate_risk(self) -> RiskLevel:
        """Calculate highest risk level in batch."""
        if not self.commands:
            return RiskLevel.LOW
        
        risks = [cmd.classify_risk() for cmd in self.commands]
        
        # Return highest risk level
        if RiskLevel.CRITICAL in risks:
            return RiskLevel.CRITICAL
        if RiskLevel.HIGH in risks:
            return RiskLevel.HIGH
        if RiskLevel.MEDIUM in risks:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW
    
    def to_dict(self) -> dict:
        """Convert to dict for serialization."""
        return {
            "id": self.id,
            "commands": [cmd.to_dict() for cmd in self.commands],
            "description": self.description,
            "estimated_duration_ms": self.estimated_duration_ms,
            "rollback_commands": [cmd.to_dict() for cmd in self.rollback_commands] if self.rollback_commands else None,
        }


@dataclass
class ExecutionResult:
    """Result of executing a single command."""
    
    command: str
    success: bool
    stdout: str
    stderr: str
    returncode: int
    execution_time_ms: float
    
    def to_dict(self) -> dict:
        """Convert to dict for serialization."""
        return {
            "command": self.command,
            "success": self.success,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "returncode": self.returncode,
            "execution_time_ms": self.execution_time_ms,
        }


@dataclass
class AuditEntry:
    """Single entry in immutable audit trail."""
    
    timestamp: datetime = field(default_factory=datetime.now)
    action: str = ""  # "proposed" | "reviewed" | "approved" | "executed" | "failed"
    actor: str = ""  # username or "system"
    details: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dict for JSONL serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "action": self.action,
            "actor": self.actor,
            "details": self.details,
        }


@dataclass
class ShellExecutionApproval:
    """HITL approval decision for command batch."""
    
    id: str = field(default_factory=lambda: f"approval_{uuid4().hex[:12]}")
    batch_id: str = ""
    decision: ApprovalDecision = ApprovalDecision.PENDING
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None  # username or "auto"
    reason: Optional[str] = None
    edited_commands: Optional[list[ShellCommand]] = None
    session_permission_level: SessionPermissionLevel = SessionPermissionLevel.BATCH
    
    # Audit trail
    audit_log: list[AuditEntry] = field(default_factory=list)
    
    def add_audit_entry(self, action: str, actor: str, details: Optional[dict] = None) -> None:
        """Add immutable audit entry."""
        self.audit_log.append(
            AuditEntry(
                timestamp=datetime.now(),
                action=action,
                actor=actor,
                details=details or {},
            )
        )
    
    def to_dict(self) -> dict:
        """Convert to dict for serialization."""
        return {
            "id": self.id,
            "batch_id": self.batch_id,
            "decision": self.decision.value,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "approved_by": self.approved_by,
            "reason": self.reason,
            "edited_commands": [cmd.to_dict() for cmd in self.edited_commands] if self.edited_commands else None,
            "session_permission_level": self.session_permission_level.value,
            "audit_log": [entry.to_dict() for entry in self.audit_log],
        }


@dataclass
class ExecutionAuditRecord:
    """Immutable record for compliance and auditability.
    
    All shell execution decisions and results are logged here with:
    - Proposal (what LLM suggested)
    - Approval (who approved, when, why)
    - Execution (what actually happened, output, timing)
    """
    
    id: str = field(default_factory=lambda: f"exec_{uuid4().hex[:12]}")
    timestamp: datetime = field(default_factory=datetime.now)
    session_id: str = ""
    
    # Proposed by LLM
    command_batch: ShellCommandBatch = field(default_factory=ShellCommandBatch)
    proposed_by: str = "gpt-4o"  # model name
    
    # Approval decision
    approval: ShellExecutionApproval = field(default_factory=ShellExecutionApproval)
    
    # Execution results
    execution_results: Optional[list[ExecutionResult]] = None
    execution_timestamp: Optional[datetime] = None
    
    # Hash chain for immutability verification
    previous_hash: Optional[str] = None
    current_hash: Optional[str] = None
    
    def calculate_hash(self) -> str:
        """Calculate SHA256 hash of this record for integrity checking."""
        import json
        
        payload = {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "command_batch": self.command_batch.to_dict(),
            "proposed_by": self.proposed_by,
            "approval": self.approval.to_dict(),
            "execution_results": [r.to_dict() for r in self.execution_results] if self.execution_results else None,
            "execution_timestamp": self.execution_timestamp.isoformat() if self.execution_timestamp else None,
            "previous_hash": self.previous_hash,
        }
        
        payload_str = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(payload_str.encode()).hexdigest()
    
    def finalize(self, previous_hash: Optional[str] = None) -> None:
        """Finalize record and calculate hash chain."""
        self.previous_hash = previous_hash
        self.current_hash = self.calculate_hash()
    
    def to_dict(self) -> dict:
        """Convert to dict for JSONL serialization."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "command_batch": self.command_batch.to_dict(),
            "proposed_by": self.proposed_by,
            "approval": self.approval.to_dict(),
            "execution_results": [r.to_dict() for r in self.execution_results] if self.execution_results else None,
            "execution_timestamp": self.execution_timestamp.isoformat() if self.execution_timestamp else None,
            "previous_hash": self.previous_hash,
            "current_hash": self.current_hash,
        }

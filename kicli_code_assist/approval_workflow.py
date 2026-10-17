"""AI suggestions approval workflow for code modifications.

Implements line-by-line approval of AI-generated code changes.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum


class HunkStatus(str, Enum):
    """Status of a code hunk."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PARTIAL = "partial"  # Some lines approved, some rejected


@dataclass
class LineModification:
    """Single line modification in a hunk."""
    line_number: int
    original_line: str
    modified_line: str
    status: HunkStatus = HunkStatus.PENDING
    reason: Optional[str] = None  # Why user rejected


@dataclass
class CodeHunk:
    """Single hunk of code modifications (like unified diff)."""
    file_path: str
    start_line: int
    end_line: int
    lines: List[LineModification] = field(default_factory=list)
    status: HunkStatus = HunkStatus.PENDING
    
    def approve_all(self) -> None:
        """Approve entire hunk."""
        self.status = HunkStatus.APPROVED
        for line in self.lines:
            line.status = HunkStatus.APPROVED

    def reject_all(self) -> None:
        """Reject entire hunk."""
        self.status = HunkStatus.REJECTED
        for line in self.lines:
            line.status = HunkStatus.REJECTED

    def approve_line(self, line_number: int) -> None:
        """Approve single line."""
        for line in self.lines:
            if line.line_number == line_number:
                line.status = HunkStatus.APPROVED
                break
        self._update_status()

    def reject_line(self, line_number: int, reason: Optional[str] = None) -> None:
        """Reject single line."""
        for line in self.lines:
            if line.line_number == line_number:
                line.status = HunkStatus.REJECTED
                line.reason = reason
                break
        self._update_status()

    def _update_status(self) -> None:
        """Update hunk status based on line statuses."""
        if not self.lines:
            return

        approved = sum(1 for l in self.lines if l.status == HunkStatus.APPROVED)
        rejected = sum(1 for l in self.lines if l.status == HunkStatus.REJECTED)
        total = len(self.lines)

        if rejected == 0:
            self.status = HunkStatus.APPROVED
        elif approved == 0:
            self.status = HunkStatus.REJECTED
        else:
            self.status = HunkStatus.PARTIAL

    def get_approved_lines(self) -> List[str]:
        """Get list of approved modified lines."""
        return [
            line.modified_line
            for line in self.lines
            if line.status == HunkStatus.APPROVED
        ]

    def get_approval_percentage(self) -> float:
        """Get percentage of lines approved."""
        if not self.lines:
            return 0.0
        approved = sum(1 for l in self.lines if l.status == HunkStatus.APPROVED)
        return (approved / len(self.lines)) * 100


@dataclass
class ApprovalSession:
    """Session for approving AI suggestions across multiple hunks."""
    session_id: str
    hunks: List[CodeHunk] = field(default_factory=list)
    approved_at: Optional[str] = None

    def add_hunk(self, hunk: CodeHunk) -> None:
        """Add hunk to approval session."""
        self.hunks.append(hunk)

    def approve_hunk(self, hunk_index: int) -> None:
        """Approve entire hunk by index."""
        if 0 <= hunk_index < len(self.hunks):
            self.hunks[hunk_index].approve_all()

    def reject_hunk(self, hunk_index: int) -> None:
        """Reject entire hunk by index."""
        if 0 <= hunk_index < len(self.hunks):
            self.hunks[hunk_index].reject_all()

    def get_hunks_by_status(self, status: HunkStatus) -> List[CodeHunk]:
        """Get hunks with specific status."""
        return [h for h in self.hunks if h.status == status]

    def get_overall_approval_percentage(self) -> float:
        """Get overall approval percentage across all hunks."""
        if not self.hunks:
            return 0.0
        total_percentage = sum(h.get_approval_percentage() for h in self.hunks)
        return total_percentage / len(self.hunks)

    def is_ready_for_apply(self) -> bool:
        """Check if approved changes can be applied (at least one approved hunk)."""
        return any(h.status in (HunkStatus.APPROVED, HunkStatus.PARTIAL) for h in self.hunks)

    def get_summary(self) -> dict:
        """Get summary of approval session."""
        return {
            "session_id": self.session_id,
            "total_hunks": len(self.hunks),
            "approved": len(self.get_hunks_by_status(HunkStatus.APPROVED)),
            "rejected": len(self.get_hunks_by_status(HunkStatus.REJECTED)),
            "partial": len(self.get_hunks_by_status(HunkStatus.PARTIAL)),
            "pending": len(self.get_hunks_by_status(HunkStatus.PENDING)),
            "overall_approval": f"{self.get_overall_approval_percentage():.1f}%",
        }


class ApprovalResultFormatter:
    """Format approval results for application."""

    @staticmethod
    def format_for_file_modification(hunk: CodeHunk) -> str:
        """Format approved hunk for file modification.
        
        Args:
            hunk: CodeHunk with approval status
            
        Returns:
            Modified content to apply to file
        """
        approved_lines = hunk.get_approved_lines()
        return "\n".join(approved_lines)

    @staticmethod
    def format_approval_report(session: ApprovalSession) -> str:
        """Format approval session report.
        
        Args:
            session: ApprovalSession
            
        Returns:
            Human-readable report
        """
        summary = session.get_summary()
        report = f"""
Approval Report: {summary['session_id']}
{'=' * 60}

Total Hunks: {summary['total_hunks']}
  ✓ Approved: {summary['approved']}
  ✗ Rejected: {summary['rejected']}
  ~ Partial:  {summary['partial']}
  ⋯ Pending:  {summary['pending']}

Overall Approval: {summary['overall_approval']}

Details:
"""
        for i, hunk in enumerate(session.hunks, 1):
            status_emoji = "✓" if hunk.status == HunkStatus.APPROVED else "✗"
            report += f"\n{status_emoji} {hunk.file_path}:{hunk.start_line}-{hunk.end_line} ({hunk.status.value})"
            report += f"  {hunk.get_approval_percentage():.0f}% approved"

        return report

    @staticmethod
    def format_for_diff_display(hunk: CodeHunk) -> str:
        """Format hunk for diff viewer display with status indicators.
        
        Args:
            hunk: CodeHunk to display
            
        Returns:
            Formatted diff with approval status
        """
        diff = f"File: {hunk.file_path}\n"
        diff += f"Lines {hunk.start_line}-{hunk.end_line} ({hunk.status.value})\n"
        diff += "-" * 60 + "\n"

        for line in hunk.lines:
            status_marker = {
                HunkStatus.APPROVED: "✓",
                HunkStatus.REJECTED: "✗",
                HunkStatus.PENDING: "?",
                HunkStatus.PARTIAL: "~",
            }.get(line.status, " ")

            diff += f"{status_marker} {line.line_number}: {line.modified_line}\n"

        return diff

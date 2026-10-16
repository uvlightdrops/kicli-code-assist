"""Integration layer between TUI and shell execution system.

Handles workflow:
1. Parse LLM response for shell commands
2. Show approval modal
3. Execute approved commands
4. Display results in chat
"""

from typing import Optional, Callable
from kicli_code_assist.executor.shell_execution import (
    ShellCommandBatch,
    ShellExecutionApproval,
    ApprovalDecision,
)
from kicli_code_assist.chat_session import ChatSession


class ShellExecutorIntegration:
    """Bridge between TUI chat and shell execution HITL workflow."""

    def __init__(self, chat_session: ChatSession):
        """Initialize integration.
        
        Args:
            chat_session: ChatSession instance for parsing and execution
        """
        self.chat_session = chat_session
        self.last_batch: Optional[ShellCommandBatch] = None
        self.last_approval: Optional[ShellExecutionApproval] = None

    def try_extract_commands(self, llm_response: str) -> Optional[ShellCommandBatch]:
        """Try to extract shell commands from LLM response.
        
        Args:
            llm_response: Raw LLM response text
            
        Returns:
            ShellCommandBatch if commands found, None otherwise
        """
        try:
            batch = self.chat_session.parse_shell_batch_from_response(llm_response)
            if batch:
                self.last_batch = batch
                return batch
        except Exception as e:
            print(f"⚠️  Error parsing shell commands: {e}")
        
        return None

    def format_batch_for_display(self, batch: ShellCommandBatch) -> str:
        """Format command batch for display in chat.
        
        Args:
            batch: ShellCommandBatch to format
            
        Returns:
            Formatted string for display
        """
        lines = [f"[yellow]🔧 Shell Commands Proposed ({len(batch.commands)} command{'s' if len(batch.commands) != 1 else ''}):[/]"]
        
        for i, cmd in enumerate(batch.commands, 1):
            risk_emoji = self._risk_emoji(cmd.get_risk_level())
            lines.append(f"[bold]{i}.[/] {risk_emoji} [cyan]{cmd.command}[/]")
            if cmd.description:
                lines.append(f"   {cmd.description}")
        
        return "\n".join(lines)

    def format_approval_result(self, approval: ShellExecutionApproval, execution_result: dict) -> str:
        """Format execution result for display in chat.
        
        Args:
            approval: ShellExecutionApproval with decision
            execution_result: Result from execute_shell_batch()
            
        Returns:
            Formatted string for display
        """
        if execution_result["status"] == "rejected":
            return f"[yellow]⏭️  Batch skipped:[/] {execution_result['reason']}"
        
        if execution_result["status"] == "completed":
            succeeded = execution_result["commands_succeeded"]
            failed = execution_result["commands_failed"]
            
            lines = [f"[green]✅ Execution Complete:[/]"]
            lines.append(f"   {succeeded} succeeded, {failed} failed")
            
            for result in execution_result.get("results", []):
                status = "[green]✓[/]" if result["success"] else "[red]✗[/]"
                lines.append(f"   {status} {result['command'][:60]}")
                if result["exit_code"] is not None and not result["success"]:
                    lines.append(f"      Exit code: {result['exit_code']}")
            
            return "\n".join(lines)
        
        return "[red]Error processing batch[/]"

    def _risk_emoji(self, risk_level: str) -> str:
        """Return emoji for risk level.
        
        Args:
            risk_level: Risk level string (low, medium, high, critical)
            
        Returns:
            Emoji string
        """
        emojis = {
            "low": "🟢",
            "medium": "🟡",
            "high": "🟠",
            "critical": "🔴",
        }
        return emojis.get(risk_level, "⚪")

    def create_approval_from_modal_result(
        self,
        decision: str,
        edited_batch: Optional[ShellCommandBatch] = None,
        rejection_reason: Optional[str] = None
    ) -> ShellExecutionApproval:
        """Create ShellExecutionApproval from modal result.
        
        Args:
            decision: "approved", "rejected", or "approved_edited"
            edited_batch: Modified batch if decision is "approved_edited"
            rejection_reason: Reason if decision is "rejected"
            
        Returns:
            ShellExecutionApproval instance
        """
        if decision == "approved":
            approval = ShellExecutionApproval(
                decision=ApprovalDecision.APPROVED,
                batch_id=self.last_batch.batch_id if self.last_batch else None,
                approver="user",
            )
        elif decision == "approved_edited":
            approval = ShellExecutionApproval(
                decision=ApprovalDecision.APPROVED_EDITED,
                batch_id=self.last_batch.batch_id if self.last_batch else None,
                approver="user",
                edited_batch=edited_batch,
            )
        else:  # rejected
            approval = ShellExecutionApproval(
                decision=ApprovalDecision.REJECTED,
                batch_id=self.last_batch.batch_id if self.last_batch else None,
                rejection_reason=rejection_reason or "User rejected",
            )
        
        self.last_approval = approval
        return approval

    def execute_and_format(self) -> Optional[str]:
        """Execute last approved batch and return formatted result.
        
        Returns:
            Formatted result string, or None if no approved batch
            
        Raises:
            RuntimeError: If shell execution not initialized in session
        """
        if not self.last_batch or not self.last_approval:
            return None
        
        if self.last_approval.decision != ApprovalDecision.APPROVED:
            return self.format_approval_result(self.last_approval, {
                "status": "rejected",
                "reason": self.last_approval.rejection_reason or "User rejected",
                "commands_attempted": 0,
                "commands_succeeded": 0,
            })
        
        # Execute batch
        batch_to_execute = self.last_approval.edited_batch or self.last_batch
        execution_result = self.chat_session.execute_shell_batch(
            batch_to_execute,
            self.last_approval
        )
        
        return self.format_approval_result(self.last_approval, execution_result)

    def get_session_summary(self) -> dict:
        """Get summary of shell executions in session.
        
        Returns:
            Dict with execution statistics
        """
        return self.chat_session.get_shell_execution_summary()

"""Integrate AI suggestions workflow end-to-end.

This module connects:
1. AsyncLLMIntegration (LLM calls)
2. ResponseParser (parse multi-part responses)
3. ApprovalWorkflow (user approval)
4. FileEditorPane (apply changes)
"""

from typing import Optional, Callable, List
from dataclasses import dataclass
from enum import Enum
import re

from ki_core.core.response_parser import ResponseParser, ResponsePartType
from ki_core.adapters.provider_chain import ProviderChain
from kicli_code_assist.llm_integration import AsyncLLMIntegration
from kicli_code_assist.approval_workflow import (
    CodeHunk,
    LineModification,
    ApprovalSession,
    HunkStatus,
)


class DiffType(str, Enum):
    """Type of diff to generate."""
    UNIFIED = "unified"
    SIDE_BY_SIDE = "side_by_side"
    INLINE = "inline"


@dataclass
class AISuggestion:
    """Single AI suggestion for user approval."""
    session_id: str
    file_path: str
    original_content: str
    llm_response: str  # Raw LLM response
    approval_session: ApprovalSession
    format_type: DiffType = DiffType.UNIFIED

    def get_diff(self) -> str:
        """Generate diff view for approval."""
        lines = []
        for hunk in self.approval_session.hunks:
            lines.append(f"--- {hunk.file_path}")
            lines.append(f"+++ {hunk.file_path}")
            for line in hunk.lines:
                if line.status == HunkStatus.APPROVED:
                    lines.append(f"+ {line.modified_line}")
                elif line.status == HunkStatus.REJECTED:
                    lines.append(f"- {line.modified_line}")
                else:
                    lines.append(f"  {line.modified_line}")
        return "\n".join(lines)


class AIWorkflowManager:
    """Manages complete AI suggestion workflow.

    Flow:
    1. Get user prompt from ChatInput
    2. Call AsyncLLMIntegration.achat_with_context()
    3. Parse response into hunks using ResponseParser
    4. Show ApprovalModal for user approval
    5. Apply approved changes to editor
    """

    def __init__(
        self,
        llm_integration: Optional[AsyncLLMIntegration] = None,
        parser: Optional[ResponseParser] = None,
    ):
        self.llm_integration = llm_integration
        self.parser = parser or ResponseParser()
        self._suggestion_counter = 0

    async def process_user_prompt(
        self,
        prompt: str,
        file_context: Optional[str] = None,
        current_file_path: Optional[str] = None,
        on_progress: Optional[Callable[[str], None]] = None,
    ) -> Optional[AISuggestion]:
        """Process user prompt and return suggestion for approval.

        Args:
            prompt: User's request (e.g., "Fix the login validation")
            file_context: Current file content for context
            current_file_path: Path of current file
            on_progress: Progress callback for UI updates

        Returns:
            AISuggestion if successful, None if cancelled/failed
        """
        if not self.llm_integration:
            if on_progress:
                on_progress("ERROR: LLM integration not initialized")
            return None

        self._suggestion_counter += 1
        session_id = f"ai-suggestion-{self._suggestion_counter}"

        # 1. Get LLM response with file context
        if on_progress:
            on_progress("Sending to LLM...")

        try:
            # Build context as messages for LLM
            system_prompt = "You are a helpful code assistant. Analyze the provided code and provide specific, actionable improvements. Format your response with clear explanations and code examples."
            
            messages = [
                {"role": "user", "content": self._build_context(prompt, file_context, current_file_path)}
            ]
            
            llm_response = await self.llm_integration.query(
                messages=messages,
                system_prompt=system_prompt,
                on_progress=on_progress,
            )
        except Exception as e:
            if on_progress:
                on_progress(f"ERROR: LLM call failed: {e}")
            return None

        if on_progress:
            on_progress("Parsing response...")

        # 2. Parse response into hunks
        parsed_parts = self.parser.parse(llm_response)
        hunks = self._create_hunks_from_response(
            parsed_parts,
            file_context or "",
            current_file_path or "unknown.txt",
        )

        # 3. Create approval session
        approval_session = ApprovalSession(session_id=session_id)
        for hunk in hunks:
            approval_session.add_hunk(hunk)

        if on_progress:
            on_progress(f"Ready for approval: {len(hunks)} changes")

        return AISuggestion(
            session_id=session_id,
            file_path=current_file_path or "unknown.txt",
            original_content=file_context or "",
            llm_response=llm_response,
            approval_session=approval_session,
        )

    def _build_context(
        self,
        prompt: str,
        file_content: Optional[str],
        file_path: Optional[str],
    ) -> str:
        """Build context for LLM with file information."""
        parts = [prompt]

        if file_path:
            parts.append(f"\n# Current file: {file_path}")

        if file_content:
            parts.append(f"\n## Current content:\n```\n{file_content}\n```")

        return "\n".join(parts)

    def _create_hunks_from_response(
        self,
        parsed_parts: List,
        original_content: str,
        file_path: str,
    ) -> List[CodeHunk]:
        """Create CodeHunk objects from parsed response parts."""
        hunks = []

        for part in parsed_parts:
            if part.type == ResponsePartType.CODE or part.type == ResponsePartType.SHELL:
                # Extract code blocks
                hunk = self._parse_code_block_to_hunk(
                    part.content,
                    original_content,
                    file_path,
                )
                if hunk:
                    hunks.append(hunk)

        if not hunks:
            # If no code blocks found, treat entire response as suggestion
            hunk = CodeHunk(
                file_path=file_path,
                start_line=1,
                end_line=len(original_content.split("\n")),
                lines=[
                    LineModification(
                        line_number=i + 1,
                        original_line=line,
                        modified_line=line,
                    )
                    for i, line in enumerate(original_content.split("\n")[:10])
                ],
            )
            hunks.append(hunk)

        return hunks

    def _parse_code_block_to_hunk(
        self,
        code_block: str,
        original_content: str,
        file_path: str,
    ) -> Optional[CodeHunk]:
        """Parse code block into CodeHunk with line-by-line modifications.

        Tries to find similar lines in original content and create diff hunks.
        """
        new_lines = code_block.split("\n")
        original_lines = original_content.split("\n")

        # Find approximate match in original content
        start_line = 1
        end_line = min(len(original_lines), len(new_lines))

        lines = []
        for i, new_line in enumerate(new_lines[:20]):  # Limit to 20 lines
            line_num = start_line + i
            original_line = original_lines[i] if i < len(original_lines) else ""

            lines.append(
                LineModification(
                    line_number=line_num,
                    original_line=original_line,
                    modified_line=new_line,
                )
            )

        if not lines:
            return None

        return CodeHunk(
            file_path=file_path,
            start_line=start_line,
            end_line=end_line,
            lines=lines,
        )

    def apply_approved_changes(
        self,
        suggestion: AISuggestion,
        on_apply: Callable[[str], None],
    ) -> bool:
        """Apply approved changes to file.

        Args:
            suggestion: AIsuggestion with approval session
            on_apply: Callback to apply changes (receives new content)

        Returns:
            True if changes applied successfully
        """
        if not suggestion.approval_session.is_ready_for_apply():
            return False

        # Build new file content from approved lines
        new_content_lines = suggestion.original_content.split("\n")

        # Apply each approved hunk
        for hunk in suggestion.approval_session.hunks:
            if hunk.status in (HunkStatus.APPROVED, HunkStatus.PARTIAL):
                approved_lines = hunk.get_approved_lines()
                for i, line in enumerate(hunk.lines):
                    if line.status == HunkStatus.APPROVED:
                        # Replace line in new_content_lines
                        idx = line.line_number - 1
                        if 0 <= idx < len(new_content_lines):
                            new_content_lines[idx] = line.modified_line

        new_content = "\n".join(new_content_lines)
        on_apply(new_content)
        return True

    def get_session_summary(self, session: ApprovalSession) -> str:
        """Get human-readable summary of approval session."""
        summary = session.get_summary()
        return f"""
AI Suggestion Summary
{'=' * 60}
Approved:  {summary['approved']}/{summary['total_hunks']} hunks
Rejected:  {summary['rejected']} hunks
Partial:   {summary['partial']} hunks (some lines approved)
Pending:   {summary['pending']} hunks

Overall approval rate: {summary['overall_approval']}

Status: {'✓ Ready to apply' if session.is_ready_for_apply() else '✗ No changes to apply'}
"""

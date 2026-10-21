"""WebSocket streaming support for real-time reasoning updates."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Optional, Callable, Any
from dataclasses import asdict

from kicli_code_assist.agent.reasoning import ReasoningAgent, ReasoningResult, ThinkingStep


class StreamingReasoningAgent:
    """Reasoning agent with WebSocket streaming support."""

    def __init__(self, project_root: Path):
        """Initialize streaming reasoning agent."""
        self.project_root = project_root
        self.agent = ReasoningAgent(project_root)

    async def reason_about_code_streaming(
        self,
        file_path: Path,
        query: str = "How can this code be improved?",
        request_id: str = "",
        on_step_complete: Optional[Callable[[ThinkingStep], None]] = None,
    ) -> ReasoningResult:
        """
        Multi-step reasoning with streaming callbacks.
        
        Calls on_step_complete for each completed thinking step,
        enabling real-time WebSocket updates.
        
        Args:
            file_path: Path to code file
            query: Question to reason about
            request_id: Request ID for tracking
            on_step_complete: Callback function called after each step completes
            
        Returns:
            ReasoningResult with all thinking steps
        """
        # Run the base reasoning
        result = await self.agent.reason_about_code(
            file_path=file_path,
            query=query,
            request_id=request_id,
        )

        # Stream each thinking step via callback
        if on_step_complete:
            for step in result.thinking:
                on_step_complete(step)

        return result

    def get_step_json(self, step: ThinkingStep) -> str:
        """Get JSON representation of a single step."""
        return json.dumps(asdict(step), default=str)

    def get_result_json(self, result: ReasoningResult) -> str:
        """Get JSON representation of full result."""
        return json.dumps(result.to_dict(), default=str)

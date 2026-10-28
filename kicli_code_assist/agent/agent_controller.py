"""Agent controller for managing autonomous execution with state streaming.

Central orchestrator that:
- Manages agent lifecycle
- Broadcasts state to all listeners
- Processes intervention commands
- Persists execution history
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, Callable, List
from dataclasses import replace
import json
import uuid

from kicli_code_assist.agent.agent_state import (
    AgentStateSnapshot,
    AgentStatus,
    AgentPhase,
    ThinkingStep,
    ThinkingType,
    ActionLog,
    ErrorInfo,
    ExecutionResult,
)
from kicli_code_assist.agent.intervention import (
    InterventionQueue,
    InterventionMode,
    InterventionType,
    InterventionSource,
    InterventionCommand,
)

logger = logging.getLogger("kicli-agent-controller")


class AgentController:
    """Central controller for agent execution with state broadcasting.
    
    Manages:
    - Agent lifecycle (init, execute, pause, resume, stop)
    - Real-time state broadcasting to listeners
    - Intervention queue processing
    - State persistence
    
    All state updates are broadcasted immediately to listeners
    (WebUI, CLI supervisor, etc.) via callbacks.
    """
    
    def __init__(
        self,
        intervention_mode: InterventionMode = InterventionMode.USER_PROMPT,
        state_dir: Optional[Path] = None,
        broadcast_callback: Optional[Callable[[AgentStateSnapshot], None]] = None,
    ):
        """Initialize agent controller.
        
        Args:
            intervention_mode: Strategy for handling conflicting commands
            state_dir: Directory for persisting state (default: ~/.kicli/agent-state)
            broadcast_callback: Callback for state updates
        """
        self.intervention_mode = intervention_mode
        self.state_dir = state_dir or Path.home() / ".kicli" / "agent-state"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        self.broadcast_callback = broadcast_callback
        
        # Active agents
        self._agents: Dict[str, AgentStateSnapshot] = {}
        self._intervention_queues: Dict[str, InterventionQueue] = {}
        self._start_times: Dict[str, datetime] = {}
    
    def create_agent(
        self,
        task_id: str,
        initial_phase: AgentPhase = AgentPhase.INIT,
    ) -> str:
        """Create new agent for a task.
        
        Args:
            task_id: Unique task identifier
            initial_phase: Starting phase
            
        Returns:
            agent_id for this execution
        """
        agent_id = f"agent-{uuid.uuid4().hex[:8]}"
        now = datetime.now()
        
        state = AgentStateSnapshot(
            agent_id=agent_id,
            task_id=task_id,
            status=AgentStatus.IDLE,
            current_phase=initial_phase,
            progress=0,
            started_at=now,
            updated_at=now,
        )
        
        self._agents[agent_id] = state
        self._intervention_queues[agent_id] = InterventionQueue(self.intervention_mode)
        self._start_times[agent_id] = now
        
        logger.info(f"Created agent {agent_id} for task {task_id}")
        self._broadcast(state)
        
        return agent_id
    
    def set_status(
        self,
        agent_id: str,
        status: AgentStatus,
        reason: Optional[str] = None,
    ) -> AgentStateSnapshot:
        """Update agent status.
        
        Args:
            agent_id: Agent identifier
            status: New status
            reason: Optional reason for status change
            
        Returns:
            Updated state snapshot
        """
        if agent_id not in self._agents:
            raise ValueError(f"Unknown agent: {agent_id}")
        
        state = self._agents[agent_id]
        state = replace(
            state,
            status=status,
            updated_at=datetime.now(),
        )
        self._agents[agent_id] = state
        
        if reason:
            logger.info(f"Agent {agent_id}: {status.value} ({reason})")
        else:
            logger.info(f"Agent {agent_id}: {status.value}")
        
        self._broadcast(state)
        return state
    
    def set_phase(
        self,
        agent_id: str,
        phase: AgentPhase,
        progress: Optional[int] = None,
    ) -> AgentStateSnapshot:
        """Update current phase.
        
        Args:
            agent_id: Agent identifier
            phase: New phase
            progress: Optional progress percentage (0-100)
            
        Returns:
            Updated state snapshot
        """
        if agent_id not in self._agents:
            raise ValueError(f"Unknown agent: {agent_id}")
        
        state = self._agents[agent_id]
        new_progress = progress if progress is not None else state.progress
        
        state = replace(
            state,
            current_phase=phase,
            progress=min(100, max(0, new_progress)),
            updated_at=datetime.now(),
        )
        self._agents[agent_id] = state
        
        logger.debug(f"Agent {agent_id}: phase={phase.value}, progress={new_progress}%")
        self._broadcast(state)
        return state
    
    def add_thinking_step(
        self,
        agent_id: str,
        thinking_type: ThinkingType,
        content: str,
        reasoning: Optional[str] = None,
        confidence: float = 1.0,
        alternatives: Optional[List[str]] = None,
    ) -> AgentStateSnapshot:
        """Add a thinking step.
        
        Args:
            agent_id: Agent identifier
            thinking_type: Type of thinking (decision, analysis, etc.)
            content: The thinking content
            reasoning: Optional reasoning behind the thought
            confidence: Confidence level (0.0-1.0)
            alternatives: Alternative approaches considered
            
        Returns:
            Updated state snapshot
        """
        if agent_id not in self._agents:
            raise ValueError(f"Unknown agent: {agent_id}")
        
        state = self._agents[agent_id]
        step = ThinkingStep(
            timestamp=datetime.now(),
            thinking_type=thinking_type,
            content=content,
            reasoning=reasoning,
            confidence=confidence,
            alternatives=alternatives or [],
        )
        
        state = replace(
            state,
            thinking_steps=[*state.thinking_steps, step],
            updated_at=datetime.now(),
        )
        self._agents[agent_id] = state
        
        logger.debug(
            f"Agent {agent_id}: {thinking_type.value} - {content[:50]}..."
        )
        self._broadcast(state)
        return state
    
    def add_action(
        self,
        agent_id: str,
        action_type: str,
        description: str,
        status: str = "success",
        details: Optional[Dict[str, Any]] = None,
    ) -> AgentStateSnapshot:
        """Log a completed action.
        
        Args:
            agent_id: Agent identifier
            action_type: Type of action (file_created, test_run, commit, etc.)
            description: Human-readable description
            status: Status (success, warning, error)
            details: Optional detailed information
            
        Returns:
            Updated state snapshot
        """
        if agent_id not in self._agents:
            raise ValueError(f"Unknown agent: {agent_id}")
        
        state = self._agents[agent_id]
        action = ActionLog(
            timestamp=datetime.now(),
            action_type=action_type,
            description=description,
            status=status,
            details=details,
        )
        
        state = replace(
            state,
            action_log=[*state.action_log, action],
            updated_at=datetime.now(),
        )
        self._agents[agent_id] = state
        
        logger.info(f"Agent {agent_id}: {action_type} - {description}")
        self._broadcast(state)
        return state
    
    def set_error(
        self,
        agent_id: str,
        error_type: str,
        message: str,
        traceback: Optional[str] = None,
        recovery_hint: Optional[str] = None,
    ) -> AgentStateSnapshot:
        """Set error state.
        
        Args:
            agent_id: Agent identifier
            error_type: Type of error
            message: Error message
            traceback: Optional traceback
            recovery_hint: Optional hint for recovery
            
        Returns:
            Updated state snapshot
        """
        if agent_id not in self._agents:
            raise ValueError(f"Unknown agent: {agent_id}")
        
        state = self._agents[agent_id]
        error = ErrorInfo(
            error_type=error_type,
            message=message,
            traceback=traceback,
            recovery_hint=recovery_hint,
        )
        
        state = replace(
            state,
            status=AgentStatus.ERROR,
            error=error,
            updated_at=datetime.now(),
        )
        self._agents[agent_id] = state
        
        logger.error(f"Agent {agent_id}: {error_type} - {message}")
        self._broadcast(state)
        return state
    
    def set_git_context(
        self,
        agent_id: str,
        branch: Optional[str] = None,
        commit: Optional[str] = None,
    ) -> AgentStateSnapshot:
        """Update git context (branch, commit).
        
        Args:
            agent_id: Agent identifier
            branch: Current git branch
            commit: Current git commit SHA
            
        Returns:
            Updated state snapshot
        """
        if agent_id not in self._agents:
            raise ValueError(f"Unknown agent: {agent_id}")
        
        state = self._agents[agent_id]
        state = replace(
            state,
            git_branch=branch or state.git_branch,
            git_commit=commit or state.git_commit,
            updated_at=datetime.now(),
        )
        self._agents[agent_id] = state
        self._broadcast(state)
        return state
    
    def set_test_results(
        self,
        agent_id: str,
        results: Dict[str, Any],
    ) -> AgentStateSnapshot:
        """Update test results.
        
        Args:
            agent_id: Agent identifier
            results: Test results dict
            
        Returns:
            Updated state snapshot
        """
        if agent_id not in self._agents:
            raise ValueError(f"Unknown agent: {agent_id}")
        
        state = self._agents[agent_id]
        state = replace(
            state,
            test_results=results,
            updated_at=datetime.now(),
        )
        self._agents[agent_id] = state
        self._broadcast(state)
        return state
    
    def check_interventions(self, agent_id: str) -> Optional[InterventionCommand]:
        """Check for pending intervention commands.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Next intervention command or None if queue is empty
        """
        if agent_id not in self._intervention_queues:
            return None
        
        queue = self._intervention_queues[agent_id]
        return queue.dequeue()
    
    def enqueue_intervention(
        self,
        agent_id: str,
        intervention_type: InterventionType,
        source: InterventionSource,
        reason: Optional[str] = None,
    ) -> InterventionCommand:
        """Enqueue an intervention command.
        
        Args:
            agent_id: Agent identifier
            intervention_type: Type of intervention
            source: Source of command
            reason: Reason for intervention
            
        Returns:
            The created InterventionCommand
        """
        if agent_id not in self._intervention_queues:
            raise ValueError(f"Unknown agent: {agent_id}")
        
        queue = self._intervention_queues[agent_id]
        return queue.enqueue(intervention_type, source, reason)
    
    def get_state(self, agent_id: str) -> Optional[AgentStateSnapshot]:
        """Get current state of an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Current AgentStateSnapshot or None if agent not found
        """
        return self._agents.get(agent_id)
    
    def get_all_states(self) -> Dict[str, AgentStateSnapshot]:
        """Get all active agents' states.
        
        Returns:
            Dict of agent_id -> AgentStateSnapshot
        """
        return dict(self._agents)
    
    def complete_execution(
        self,
        agent_id: str,
        success: bool,
        error: Optional[ErrorInfo] = None,
        rollback_info: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """Complete agent execution and return result.
        
        Args:
            agent_id: Agent identifier
            success: Whether execution was successful
            error: Optional error information
            rollback_info: Optional rollback information
            
        Returns:
            ExecutionResult with final state
        """
        if agent_id not in self._agents:
            raise ValueError(f"Unknown agent: {agent_id}")
        
        state = self._agents[agent_id]
        start_time = self._start_times.get(agent_id, datetime.now())
        duration = (datetime.now() - start_time).total_seconds()
        
        final_status = AgentStatus.COMPLETED if success else AgentStatus.ERROR
        state = replace(
            state,
            status=final_status,
            updated_at=datetime.now(),
            progress=100 if success else state.progress,
        )
        self._agents[agent_id] = state
        
        result = ExecutionResult(
            agent_id=agent_id,
            task_id=state.task_id,
            success=success,
            status=final_status,
            final_state=state,
            duration_seconds=duration,
            error=error,
            rollback_info=rollback_info,
        )
        
        logger.info(
            f"Agent {agent_id}: Execution {'succeeded' if success else 'failed'} "
            f"in {duration:.1f}s"
        )
        
        self._broadcast(state)
        self._persist_result(result)
        
        return result
    
    def _broadcast(self, state: AgentStateSnapshot) -> None:
        """Broadcast state to all listeners.
        
        Args:
            state: State snapshot to broadcast
        """
        if self.broadcast_callback:
            try:
                self.broadcast_callback(state)
            except Exception as e:
                logger.error(f"Error in broadcast callback: {e}", exc_info=True)
    
    def _persist_result(self, result: ExecutionResult) -> None:
        """Persist execution result to disk.
        
        Args:
            result: Execution result to persist
        """
        try:
            result_file = (
                self.state_dir
                / f"{result.agent_id}_{result.task_id}_{datetime.now().isoformat()}.json"
            )
            with open(result_file, "w") as f:
                f.write(result.to_json())
            logger.debug(f"Persisted result to {result_file}")
        except Exception as e:
            logger.error(f"Error persisting result: {e}")
    
    def cleanup(self, agent_id: str) -> None:
        """Clean up agent resources.
        
        Args:
            agent_id: Agent identifier
        """
        self._agents.pop(agent_id, None)
        self._intervention_queues.pop(agent_id, None)
        self._start_times.pop(agent_id, None)
        logger.debug(f"Cleaned up agent {agent_id}")

"""
Phase 5.4.5: Rollback Capability

Ability to undo failed implementations:
- Track state before changes
- Revert file changes
- Reset git branches
- Clean up failed branches
"""

import logging
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RollbackState:
    """Tracks state for rollback."""
    goal_id: str
    branch_name: str
    previous_head: str
    timestamp: str
    reason: Optional[str] = None
    success: bool = False


class RollbackManager:
    """Manages rollback of failed implementations."""
    
    def __init__(self, project_root: str):
        """Initialize rollback manager."""
        self.project_root = Path(project_root)
        self.rollback_history: List[RollbackState] = []
    
    def _run_git(self, cmd: List[str]) -> bool:
        """Run git command."""
        try:
            result = subprocess.run(
                ["git", "-C", str(self.project_root)] + cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Git command failed: {e}")
            return False
    
    def prepare_rollback(self, goal_id: str, branch_name: str) -> RollbackState:
        """
        Prepare for rollback by capturing current state.
        
        Args:
            goal_id: Goal identifier
            branch_name: Feature branch to track
        
        Returns:
            RollbackState for later rollback
        """
        try:
            # Get current HEAD
            result = subprocess.run(
                ["git", "-C", str(self.project_root), "rev-parse", "HEAD"],
                capture_output=True,
                text=True
            )
            previous_head = result.stdout.strip()
            
            from datetime import datetime
            state = RollbackState(
                goal_id=goal_id,
                branch_name=branch_name,
                previous_head=previous_head,
                timestamp=datetime.now().isoformat()
            )
            
            self.rollback_history.append(state)
            logger.info(f"Rollback state prepared for {goal_id}")
            return state
        
        except Exception as e:
            logger.error(f"Failed to prepare rollback: {e}")
            return None
    
    def rollback_implementation(self, goal_id: str, reason: str = "Implementation failed") -> bool:
        """
        Rollback a failed implementation.
        
        Args:
            goal_id: Goal to rollback
            reason: Reason for rollback
        
        Returns:
            True if successful
        """
        logger.info(f"🔙 Rolling back {goal_id}: {reason}")
        
        # Find the rollback state
        state = None
        for s in self.rollback_history:
            if s.goal_id == goal_id:
                state = s
                break
        
        if not state:
            logger.warning(f"No rollback state found for {goal_id}")
            return False
        
        try:
            # Switch to safe branch
            logger.info("Switching to devel branch...")
            if not self._run_git(["checkout", "devel"]):
                logger.error("Failed to checkout devel")
                return False
            
            # Delete feature branch
            logger.info(f"Deleting feature branch {state.branch_name}...")
            self._run_git(["branch", "-D", state.branch_name])
            
            # Try to delete remote
            self._run_git(["push", "origin", "--delete", state.branch_name])
            
            # Reset to previous HEAD on devel
            logger.info("Resetting to previous state...")
            if not self._run_git(["reset", "--hard", state.previous_head]):
                logger.warning("Could not reset, but branch is cleaned up")
            
            state.reason = reason
            state.success = True
            
            logger.info(f"✓ Rollback successful for {goal_id}")
            return True
        
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    def rollback_to_commit(self, commit_sha: str) -> bool:
        """
        Rollback to a specific commit.
        
        Args:
            commit_sha: Commit to revert to
        
        Returns:
            True if successful
        """
        logger.info(f"Rolling back to commit {commit_sha[:8]}...")
        
        try:
            if not self._run_git(["reset", "--hard", commit_sha]):
                logger.error("Failed to reset to commit")
                return False
            
            logger.info(f"✓ Reset to {commit_sha[:8]}")
            return True
        
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    def get_rollback_history(self) -> List[RollbackState]:
        """Get rollback history."""
        return self.rollback_history.copy()
    
    def print_rollback_summary(self):
        """Print rollback history summary."""
        print("\n📋 Rollback History")
        print("=" * 60)
        
        if not self.rollback_history:
            print("(No rollbacks)")
            return
        
        for state in self.rollback_history:
            status = "✓" if state.success else "✗"
            print(f"{status} {state.goal_id}")
            print(f"   Branch: {state.branch_name}")
            print(f"   Reason: {state.reason or 'unknown'}")
            print(f"   When: {state.timestamp}")
            print()


class SafeImplementationWrapper:
    """Wraps implementation with automatic rollback on failure."""
    
    def __init__(self, project_root: str, goal_id: str, branch_name: str):
        """Initialize wrapper."""
        self.project_root = project_root
        self.goal_id = goal_id
        self.branch_name = branch_name
        self.rollback = RollbackManager(project_root)
        self.state = self.rollback.prepare_rollback(goal_id, branch_name)
    
    def execute_with_rollback(self, implementation_func, *args, **kwargs) -> Any:
        """
        Execute implementation with automatic rollback on exception.
        
        Args:
            implementation_func: Function to execute
            *args, **kwargs: Arguments to pass to function
        
        Returns:
            Function result, or None if exception occurred
        """
        try:
            logger.info(f"Executing implementation with rollback protection...")
            result = implementation_func(*args, **kwargs)
            
            if result.get("success"):
                logger.info(f"✓ Implementation successful, keeping changes")
                return result
            else:
                logger.warning(f"Implementation failed, rolling back...")
                self.rollback.rollback_implementation(
                    self.goal_id,
                    result.get("error", "Implementation returned failure")
                )
                return result
        
        except Exception as e:
            logger.error(f"Exception during implementation, rolling back: {e}")
            self.rollback.rollback_implementation(
                self.goal_id,
                f"Exception: {str(e)}"
            )
            return {
                "success": False,
                "error": str(e),
                "rolled_back": True
            }

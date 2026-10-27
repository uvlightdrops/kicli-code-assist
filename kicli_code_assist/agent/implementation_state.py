"""
Phase 5.4.3: Implementation State Tracking

Tracks which goals have been implemented:
- Persistent state across sessions
- Implementation history and audit trail
- Status tracking (pending/in_progress/done/failed)
- Commit and test result references
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ImplementationStatus(Enum):
    """Implementation status states."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    FAILED = "failed"
    ROLLBACK = "rollback"


@dataclass
class ImplementationEntry:
    """Single implementation record."""
    goal_id: str  # Goal identifier
    goal_title: str  # Goal title for reference
    status: str  # ImplementationStatus value
    project_root: str  # Project path
    commit_sha: Optional[str] = None  # Git commit SHA
    branch_name: Optional[str] = None  # Feature branch created
    test_results: Optional[Dict] = None  # Test execution results
    test_passed: bool = False  # Whether all tests passed
    error_message: Optional[str] = None  # If failed, why?
    created_at: Optional[str] = None  # When started
    completed_at: Optional[str] = None  # When finished
    duration_seconds: float = 0.0  # How long it took
    files_modified: List[str] = None  # Files changed
    
    def __post_init__(self):
        """Initialize defaults."""
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.files_modified is None:
            self.files_modified = []


class ImplementationStateManager:
    """Manages implementation state database."""
    
    def __init__(self, state_file: Optional[str] = None):
        """
        Initialize state manager.
        
        Args:
            state_file: Path to state JSON file (default: ~/.kicli/implementation_state.json)
        """
        if state_file:
            self.state_file = Path(state_file)
        else:
            # Use default location
            state_dir = Path.home() / ".kicli"
            state_dir.mkdir(exist_ok=True)
            self.state_file = state_dir / "implementation_state.json"
        
        self.state: Dict[str, ImplementationEntry] = {}
        self._load_state()
    
    def _load_state(self):
        """Load state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    data = json.load(f)
                
                # Reconstruct ImplementationEntry objects
                for entry_id, entry_data in data.items():
                    try:
                        self.state[entry_id] = ImplementationEntry(**entry_data)
                    except Exception as e:
                        logger.warning(f"Could not load entry {entry_id}: {e}")
                
                logger.info(f"Loaded {len(self.state)} implementation records")
            except Exception as e:
                logger.error(f"Failed to load state: {e}")
                self.state = {}
    
    def _save_state(self):
        """Save state to file."""
        try:
            with open(self.state_file, "w") as f:
                # Convert dataclasses to dicts
                data = {}
                for entry_id, entry in self.state.items():
                    data[entry_id] = asdict(entry)
                
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved {len(self.state)} records to {self.state_file}")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def start_implementation(self, goal_id: str, goal_title: str, 
                            project_root: str) -> ImplementationEntry:
        """
        Mark goal as in-progress.
        
        Args:
            goal_id: Unique goal identifier
            goal_title: Human-readable title
            project_root: Project path
        
        Returns:
            Created ImplementationEntry
        """
        entry = ImplementationEntry(
            goal_id=goal_id,
            goal_title=goal_title,
            status=ImplementationStatus.IN_PROGRESS.value,
            project_root=project_root
        )
        
        self.state[goal_id] = entry
        self._save_state()
        
        logger.info(f"Started: {goal_title}")
        return entry
    
    def complete_implementation(self, goal_id: str, commit_sha: str,
                               branch_name: str, files_modified: List[str],
                               test_results: Optional[Dict] = None,
                               test_passed: bool = False) -> bool:
        """
        Mark goal as done with results.
        
        Args:
            goal_id: Goal identifier
            commit_sha: Git commit SHA
            branch_name: Feature branch name
            files_modified: List of modified files
            test_results: Test execution results (optional)
            test_passed: Whether tests passed
        
        Returns:
            True if successful
        """
        if goal_id not in self.state:
            logger.warning(f"No in-progress entry for {goal_id}")
            return False
        
        entry = self.state[goal_id]
        entry.status = ImplementationStatus.DONE.value
        entry.commit_sha = commit_sha
        entry.branch_name = branch_name
        entry.files_modified = files_modified
        entry.test_results = test_results
        entry.test_passed = test_passed
        entry.completed_at = datetime.now().isoformat()
        
        # Calculate duration
        if entry.created_at:
            created = datetime.fromisoformat(entry.created_at)
            completed = datetime.fromisoformat(entry.completed_at)
            entry.duration_seconds = (completed - created).total_seconds()
        
        self._save_state()
        logger.info(f"Completed: {entry.goal_title} ({commit_sha[:8]})")
        return True
    
    def fail_implementation(self, goal_id: str, error_message: str) -> bool:
        """
        Mark goal as failed.
        
        Args:
            goal_id: Goal identifier
            error_message: Reason for failure
        
        Returns:
            True if successful
        """
        if goal_id not in self.state:
            logger.warning(f"No entry for {goal_id}")
            return False
        
        entry = self.state[goal_id]
        entry.status = ImplementationStatus.FAILED.value
        entry.error_message = error_message
        entry.completed_at = datetime.now().isoformat()
        
        self._save_state()
        logger.warning(f"Failed: {entry.goal_title} - {error_message}")
        return True
    
    def get_status(self, goal_id: str) -> Optional[str]:
        """Get current status of a goal."""
        if goal_id in self.state:
            return self.state[goal_id].status
        return None
    
    def is_completed(self, goal_id: str) -> bool:
        """Check if goal was already completed."""
        status = self.get_status(goal_id)
        return status == ImplementationStatus.DONE.value
    
    def get_completed_goals(self, project_root: Optional[str] = None) -> List[ImplementationEntry]:
        """Get all completed goals."""
        completed = []
        for entry in self.state.values():
            if entry.status == ImplementationStatus.DONE.value:
                if project_root is None or entry.project_root == project_root:
                    completed.append(entry)
        return completed
    
    def get_failed_goals(self, project_root: Optional[str] = None) -> List[ImplementationEntry]:
        """Get all failed implementation attempts."""
        failed = []
        for entry in self.state.values():
            if entry.status == ImplementationStatus.FAILED.value:
                if project_root is None or entry.project_root == project_root:
                    failed.append(entry)
        return failed
    
    def get_implementation_history(self, goal_id: str) -> List[ImplementationEntry]:
        """Get full history for a goal."""
        history = []
        for entry_id, entry in self.state.items():
            if entry.goal_id == goal_id:
                history.append(entry)
        return sorted(history, key=lambda e: e.created_at or "")
    
    def print_summary(self, project_root: Optional[str] = None):
        """Print implementation summary."""
        completed = self.get_completed_goals(project_root)
        failed = self.get_failed_goals(project_root)
        
        print("\n📋 Implementation Summary")
        print("=" * 60)
        
        if completed:
            print(f"\n✅ Completed ({len(completed)}):")
            for entry in completed:
                duration = f"{entry.duration_seconds:.1f}s" if entry.duration_seconds else "?"
                test_status = "✓" if entry.test_passed else "?"
                print(f"   [{test_status}] {entry.goal_title} ({duration})")
                if entry.commit_sha:
                    print(f"       Commit: {entry.commit_sha[:8]}")
        
        if failed:
            print(f"\n❌ Failed ({len(failed)}):")
            for entry in failed:
                print(f"   {entry.goal_title}")
                if entry.error_message:
                    print(f"       Error: {entry.error_message}")
        
        if not completed and not failed:
            print("\n(No records yet)")
        
        print()

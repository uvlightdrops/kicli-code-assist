"""
Phase 5.4.1: Git Workflow Manager

Handles all git operations for autonomous code implementation:
- Create feature branches from goals
- Commit changes with descriptive messages
- Push to remote repository
- Track commits and diffs
"""

import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class GitCommit:
    """Represents a git commit."""
    sha: str
    message: str
    author: str
    timestamp: datetime
    files_changed: List[str]
    insertions: int
    deletions: int


class GitManager:
    """Manages git operations for autonomous code implementation."""
    
    def __init__(self, project_root: str):
        """Initialize git manager for project."""
        self.project_root = Path(project_root)
        self.repo_name = self.project_root.name
        
    def _run_git_command(self, cmd: List[str], check: bool = True) -> str:
        """Run a git command and return output."""
        try:
            result = subprocess.run(
                ["git", "-C", str(self.project_root)] + cmd,
                capture_output=True,
                text=True,
                check=check
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {e.stderr}")
            raise
    
    def get_current_branch(self) -> str:
        """Get current branch name."""
        try:
            return self._run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
        except Exception as e:
            logger.warning(f"Cannot get branch: {e}")
            return "unknown"
    
    def branch_exists(self, branch_name: str) -> bool:
        """Check if branch exists."""
        try:
            output = self._run_git_command(["branch", "-a"], check=True)
            # Check if branch is in list
            for line in output.split("\n"):
                clean_line = line.strip().lstrip("*").strip()
                if clean_line == branch_name or clean_line.endswith(f"/{branch_name}"):
                    return True
            return False
        except:
            return False
    
    def create_branch(self, branch_name: str, base_branch: str = "devel") -> bool:
        """
        Create a feature branch from base branch.
        
        Args:
            branch_name: Name for new branch (sanitized to git format)
            base_branch: Branch to base feature on (default: devel)
        
        Returns:
            True if successful, False otherwise
        """
        # Sanitize branch name (lowercase, replace spaces with hyphens)
        clean_name = branch_name.lower().replace(" ", "-").replace("_", "-")
        clean_name = "".join(c for c in clean_name if c.isalnum() or c == "-")
        feature_branch = f"feature/{clean_name}"
        
        try:
            # Clean up any uncommitted changes before switching branches
            try:
                logger.info("Cleaning up uncommitted changes...")
                self._run_git_command(["clean", "-fd"])
                self._run_git_command(["checkout", "--"])
            except Exception as e:
                logger.warning(f"Cleanup failed: {e}")
            
            # Try to update base branch (may fail if no remote)
            try:
                logger.info(f"Updating {base_branch}...")
                self._run_git_command(["fetch", "origin"])
                self._run_git_command(["checkout", base_branch])
                self._run_git_command(["pull", "origin", base_branch])
            except Exception as e:
                logger.warning(f"Cannot fetch from remote (local repo?): {e}")
                # Try to checkout base branch locally
                try:
                    self._run_git_command(["checkout", base_branch])
                except:
                    logger.info(f"Base branch {base_branch} doesn't exist, using current")
            
            # Create feature branch
            logger.info(f"Creating branch {feature_branch}...")
            if self.branch_exists(feature_branch):
                logger.warning(f"Branch {feature_branch} already exists, checking it out")
                self._run_git_command(["checkout", feature_branch])
            else:
                self._run_git_command(["checkout", "-b", feature_branch])
            
            logger.info(f"✓ Branch created: {feature_branch}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create branch: {e}")
            return False
    
    def get_changed_files(self) -> List[str]:
        """Get list of changed files in current branch."""
        try:
            output = self._run_git_command(["status", "--porcelain"])
            if not output:
                return []
            
            files = []
            for line in output.split("\n"):
                if line.strip():
                    # Format: "XY filename"
                    status = line[:2]
                    filename = line[3:].strip()
                    files.append(filename)
            return files
        except Exception as e:
            logger.error(f"Cannot get changed files: {e}")
            return []
    
    def get_diff_stat(self) -> Dict[str, Any]:
        """Get statistics of changes (insertions/deletions)."""
        try:
            output = self._run_git_command(["diff", "--stat"])
            lines = output.split("\n")
            
            insertions = 0
            deletions = 0
            
            for line in lines:
                if "+" in line and "-" in line:
                    parts = line.split("|")
                    if len(parts) >= 2:
                        changes = parts[-1].strip()
                        insertions += changes.count("+")
                        deletions += changes.count("-")
            
            return {
                "insertions": insertions,
                "deletions": deletions,
                "summary": output
            }
        except Exception as e:
            logger.error(f"Cannot get diff stat: {e}")
            return {"insertions": 0, "deletions": 0, "summary": ""}
    
    def add_files(self, files: Optional[List[str]] = None) -> bool:
        """
        Add files to staging area.
        
        Args:
            files: List of files to add, None = add all changes
        
        Returns:
            True if successful
        """
        try:
            if files is None or len(files) == 0:
                logger.info("Adding all changes...")
                self._run_git_command(["add", "-A"])
            else:
                logger.info(f"Adding {len(files)} files...")
                for f in files:
                    # Convert to string path if it's a Path object
                    f_str = str(f)
                    self._run_git_command(["add", f_str])
            
            logger.info("✓ Files staged")
            return True
        except Exception as e:
            logger.error(f"Failed to add files: {e}")
            return False
    
    def commit_changes(self, goal_title: str, description: str, 
                      files: Optional[List[str]] = None) -> Optional[str]:
        """
        Commit changes with descriptive message.
        
        Args:
            goal_title: Goal being implemented
            description: Details about what was implemented
            files: Files changed (optional, for reference)
        
        Returns:
            Commit SHA if successful, None otherwise
        """
        try:
            # Stage changes
            self.add_files(files)
            
            # Generate commit message
            commit_msg = f"Implement: {goal_title}\n\n{description}"
            if files:
                commit_msg += f"\n\nFiles modified:\n"
                for f in files[:10]:  # First 10 files
                    commit_msg += f"- {f}\n"
                if len(files) > 10:
                    commit_msg += f"- ... and {len(files) - 10} more files\n"
            
            commit_msg += "\nCo-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
            
            logger.info(f"Committing: {goal_title}...")
            self._run_git_command(["commit", "-m", commit_msg])
            
            # Get commit SHA
            commit_sha = self._run_git_command(["rev-parse", "HEAD"])
            logger.info(f"✓ Committed: {commit_sha[:8]}")
            
            return commit_sha
            
        except subprocess.CalledProcessError as e:
            if "nothing to commit" in e.stderr:
                logger.info("No changes to commit")
                return self._run_git_command(["rev-parse", "HEAD"])
            logger.error(f"Failed to commit: {e.stderr}")
            return None
    
    def push_to_remote(self, branch_name: Optional[str] = None) -> bool:
        """
        Push changes to remote repository.
        
        Args:
            branch_name: Branch to push (None = current)
        
        Returns:
            True if successful
        """
        try:
            if branch_name is None:
                branch_name = self.get_current_branch()
            
            logger.info(f"Pushing {branch_name} to origin...")
            self._run_git_command(["push", "-u", "origin", branch_name])
            
            logger.info(f"✓ Pushed to origin/{branch_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to push: {e}")
            return False
    
    def get_commit_info(self, commit_sha: str) -> Optional[GitCommit]:
        """Get information about a specific commit."""
        try:
            # Get commit details
            output = self._run_git_command([
                "show", 
                "--format=%H%n%s%n%an%n%ai",
                "--stat",
                commit_sha
            ])
            
            lines = output.split("\n")
            if len(lines) < 4:
                return None
            
            sha = lines[0]
            message = lines[1]
            author = lines[2]
            timestamp_str = lines[3]
            
            # Parse timestamp
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            except:
                timestamp = datetime.now()
            
            # Get files changed
            files_changed = []
            insertions = 0
            deletions = 0
            
            for line in lines[4:]:
                if "|" in line:
                    parts = line.split("|")
                    filename = parts[0].strip()
                    if filename:
                        files_changed.append(filename)
            
            return GitCommit(
                sha=sha,
                message=message,
                author=author,
                timestamp=timestamp,
                files_changed=files_changed,
                insertions=insertions,
                deletions=deletions
            )
        except Exception as e:
            logger.error(f"Cannot get commit info: {e}")
            return None
    
    def create_pull_request_info(self, goal_title: str, description: str) -> Dict[str, Any]:
        """
        Generate info for creating a pull request.
        
        Returns:
            Dict with PR title, body, and metadata
        """
        branch = self.get_current_branch()
        changed_files = self.get_changed_files()
        diff_stat = self.get_diff_stat()
        
        pr_body = f"""## Implementation Summary

**Goal:** {goal_title}

**Description:**
{description}

**Changes:**
- Files modified: {len(changed_files)}
- Insertions: {diff_stat.get('insertions', 0)}
- Deletions: {diff_stat.get('deletions', 0)}

**Files:**
```
{chr(10).join(changed_files[:20])}
{"..." if len(changed_files) > 20 else ""}
```

---
*Implemented autonomously by kicli-code-assist Agent*
"""
        
        return {
            "title": f"Implement: {goal_title}",
            "body": pr_body,
            "head": branch,
            "base": "devel",
            "files_changed": changed_files,
            "stats": diff_stat
        }
    
    def reset_branch(self, keep_changes: bool = False) -> bool:
        """
        Reset branch to remote state (or local if no remote).
        
        Args:
            keep_changes: If True, stash changes before reset
        
        Returns:
            True if successful
        """
        try:
            branch = self.get_current_branch()
            
            if keep_changes:
                logger.info("Stashing changes...")
                self._run_git_command(["stash"])
            
            logger.info(f"Resetting {branch}...")
            # Try remote first, fallback to local
            try:
                self._run_git_command(["reset", "--hard", f"origin/{branch}"])
            except:
                logger.info("No remote, resetting to HEAD")
                self._run_git_command(["reset", "--hard", "HEAD"])
            
            logger.info(f"✓ Branch reset")
            return True
        except Exception as e:
            logger.error(f"Failed to reset: {e}")
            return False
    
    def delete_branch(self, branch_name: str) -> bool:
        """Delete a feature branch (locally and remotely)."""
        try:
            logger.info(f"Deleting {branch_name}...")
            
            # Ensure we're not on the branch being deleted
            current = self.get_current_branch()
            if current == branch_name:
                self._run_git_command(["checkout", "devel"])
            
            # Delete local
            self._run_git_command(["branch", "-D", branch_name])
            
            # Delete remote
            self._run_git_command(["push", "origin", "--delete", branch_name], check=False)
            
            logger.info(f"✓ Deleted {branch_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete branch: {e}")
            return False

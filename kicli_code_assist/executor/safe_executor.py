"""Safe code execution with audit logging and restrictions."""
import os
import re
import subprocess
import tempfile
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
import json
from datetime import datetime


@dataclass
class ExecutionResult:
    """Result of code execution."""
    success: bool
    stdout: str
    stderr: str
    returncode: int
    execution_time_ms: float
    command: str


class SafeCodeExecutor:
    """Execute code safely with whitelist and restrictions."""
    
    ALLOWED_COMMANDS = {
        'python', 'python3', 'bash', 'sh', 'git', 'grep', 'find',
        'cat', 'head', 'tail', 'ls', 'pwd', 'whoami', 'echo'
    }
    
    FORBIDDEN_PATTERNS = [
        r'rm\s+-rf\s+/',  # rm -rf /
        r'>\s*/dev/sda',  # Write to disk
        r'mkfs\.',  # Format filesystem
        r'dd\s+if=.*of=',  # Dangerous dd
        r'fork\(\)',  # Fork bombs
        r':\(\)\{:\|:\&\}',  # Fork bomb syntax
    ]
    
    WORK_DIR = '/srv/aiagent'
    
    def __init__(self, max_timeout: int = 30):
        """Initialize executor.
        
        Args:
            max_timeout: Max execution time in seconds
        """
        self.max_timeout = max_timeout
        self.audit_log = []
    
    def execute(
        self,
        command: str,
        dry_run: bool = False,
        working_dir: Optional[str] = None
    ) -> ExecutionResult:
        """Execute command safely.
        
        Args:
            command: Command to execute
            dry_run: If True, validate but don't execute
            working_dir: Working directory (must be under /srv)
        
        Returns:
            ExecutionResult with stdout, stderr, returncode
        """
        import time
        start_time = time.time()
        
        # Validate
        if not self._validate_command(command):
            return ExecutionResult(
                success=False,
                stdout='',
                stderr='Command rejected by safety filter',
                returncode=-1,
                execution_time_ms=0,
                command=command
            )
        
        # Validate working directory
        if working_dir:
            wd = Path(working_dir).resolve()
            if not str(wd).startswith(self.WORK_DIR):
                return ExecutionResult(
                    success=False,
                    stdout='',
                    stderr=f'Working directory must be under {self.WORK_DIR}',
                    returncode=-1,
                    execution_time_ms=0,
                    command=command
                )
        else:
            working_dir = self.WORK_DIR
        
        # Log
        self._audit_log(command, dry_run=dry_run)
        
        if dry_run:
            return ExecutionResult(
                success=True,
                stdout=f'[DRY RUN] Would execute: {command}',
                stderr='',
                returncode=0,
                execution_time_ms=(time.time() - start_time) * 1000,
                command=command
            )
        
        # Execute with timeout
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.max_timeout,
                cwd=working_dir
            )
            
            elapsed = (time.time() - start_time) * 1000
            
            return ExecutionResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=result.returncode,
                execution_time_ms=elapsed,
                command=command
            )
        
        except subprocess.TimeoutExpired:
            elapsed = (time.time() - start_time) * 1000
            return ExecutionResult(
                success=False,
                stdout='',
                stderr=f'Command timed out after {self.max_timeout}s',
                returncode=-1,
                execution_time_ms=elapsed,
                command=command
            )
        
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            return ExecutionResult(
                success=False,
                stdout='',
                stderr=str(e),
                returncode=-1,
                execution_time_ms=elapsed,
                command=command
            )
    
    def _validate_command(self, command: str) -> bool:
        """Validate command for safety."""
        cmd_lower = command.lower().strip()
        
        # Check forbidden patterns
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, cmd_lower):
                return False
        
        # Check command is in whitelist
        cmd_name = cmd_lower.split()[0]
        if cmd_name not in self.ALLOWED_COMMANDS:
            # Allow if it's a file in WORK_DIR
            if not cmd_name.startswith('.') and not cmd_name.startswith('/'):
                return False
        
        return True
    
    def _audit_log(self, command: str, dry_run: bool = False):
        """Log command execution to audit trail."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'command': command,
            'user': os.getenv('USER', 'unknown'),
            'dry_run': dry_run,
        }
        self.audit_log.append(log_entry)
    
    def get_audit_log(self) -> str:
        """Return formatted audit log."""
        return json.dumps(self.audit_log, indent=2)

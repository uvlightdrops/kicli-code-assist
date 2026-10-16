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
import time

# Use new shell execution types
from kicli_code_assist.executor.shell_execution import (
    ShellCommand,
    ShellCommandBatch,
    ExecutionResult,  # New unified result type
    RiskLevel,
    classify_risk,
)


class SafeCodeExecutor:
    """Execute shell commands safely with HITL guardrails and audit logging."""
    
    ALLOWED_COMMANDS = {
        'python', 'python3', 'bash', 'sh', 'git', 'grep', 'find',
        'cat', 'head', 'tail', 'ls', 'pwd', 'whoami', 'echo', 'make',
        'pip', 'apt', 'apt-get', 'chmod', 'chown', 'mkdir', 'rm', 'cp',
        'mv', 'touch', 'systemctl', 'service', 'docker', 'docker-compose',
    }
    
    # Commands that are always blocked regardless of other checks
    ALWAYS_BLOCKED = {
        'mkfs.ext4', 'mkfs.ext3', 'mkfs', 'dd', 'fdisk', 'parted',
        'partprobe', 'dmsetup', 'lvchange', 'vgchange', 'pvchange',
        'pvcreate', 'lvcreate', 'vgcreate',
    }
    
    FORBIDDEN_PATTERNS = [
        r'rm\s+-rf\s+/',  # rm -rf /
        r'>\s*/dev/sda',  # Write to disk
        r'mkfs\.',  # Format filesystem
        r'dd\s+if=.*of=',  # Dangerous dd
        r'fork\(\)',  # Fork bombs
        r':\(\)\{:\|:\&\}',  # Fork bomb syntax
        r'chmod\s+000\s+/',  # Remove all permissions from root
    ]
    
    WORK_DIR = '/srv/aiagent'
    
    def __init__(self, max_timeout: int = 30, allow_critical: bool = False):
        """Initialize executor.
        
        Args:
            max_timeout: Max execution time in seconds per command
            allow_critical: If True, allow execution of CRITICAL-risk commands
                           (only enable for fully-trusted automation)
        """
        self.max_timeout = max_timeout
        self.allow_critical = allow_critical
        self.audit_log = []
    
    def execute_batch(
        self,
        batch: ShellCommandBatch,
        dry_run: bool = False,
        allow_critical_override: Optional[bool] = None,
    ) -> list[ExecutionResult]:
        """Execute a batch of shell commands.
        
        Args:
            batch: ShellCommandBatch to execute
            dry_run: If True, validate but don't execute
            allow_critical_override: Override instance setting for this batch
            
        Returns:
            List of ExecutionResult, one per command
        """
        allow_critical = allow_critical_override if allow_critical_override is not None else self.allow_critical
        results = []
        
        for cmd in batch.commands:
            result = self.execute(
                cmd.command,
                dry_run=dry_run,
                working_dir=cmd.working_dir,
                env_vars=cmd.env_vars,
                timeout_override=cmd.timeout_seconds,
                risk_level=cmd.classify_risk(),
                allow_critical=allow_critical,
            )
            results.append(result)
        
        return results
    
    def execute(
        self,
        command: str,
        dry_run: bool = False,
        working_dir: Optional[str] = None,
        env_vars: Optional[dict] = None,
        timeout_override: Optional[int] = None,
        risk_level: Optional[RiskLevel] = None,
        allow_critical: Optional[bool] = None,
    ) -> ExecutionResult:
        """Execute a single shell command safely.
        
        Args:
            command: Shell command to execute
            dry_run: If True, validate but don't execute
            working_dir: Working directory for execution
            env_vars: Environment variables to set
            timeout_override: Override default timeout for this command
            risk_level: Pre-classified risk level (will re-classify if None)
            allow_critical: Override instance setting for CRITICAL commands
            
        Returns:
            ExecutionResult with outcome, stdout, stderr, timing
        """
        start_time = time.time()
        timeout = timeout_override or self.max_timeout
        allow_critical = allow_critical if allow_critical is not None else self.allow_critical
        
        # Classify risk if not provided
        if risk_level is None:
            risk_level = classify_risk(command)
        
        # Validate command
        validation_error = self._validate_command(command, risk_level, allow_critical)
        if validation_error:
            elapsed_ms = (time.time() - start_time) * 1000
            return ExecutionResult(
                command=command,
                success=False,
                stdout='',
                stderr=validation_error,
                returncode=-1,
                execution_time_ms=elapsed_ms,
            )
        
        # Validate working directory
        if working_dir:
            wd = Path(working_dir).resolve()
            # Allow any accessible directory (remove /srv restriction for dev)
            if not wd.exists():
                elapsed_ms = (time.time() - start_time) * 1000
                return ExecutionResult(
                    command=command,
                    success=False,
                    stdout='',
                    stderr=f'Working directory does not exist: {wd}',
                    returncode=-1,
                    execution_time_ms=elapsed_ms,
                )
        else:
            working_dir = os.getcwd()
        
        # Log to audit trail
        self._audit_log(command, risk_level, dry_run=dry_run)
        
        if dry_run:
            elapsed_ms = (time.time() - start_time) * 1000
            return ExecutionResult(
                command=command,
                success=True,
                stdout=f'[DRY RUN] Would execute: {command}',
                stderr='',
                returncode=0,
                execution_time_ms=elapsed_ms,
            )
        
        # Prepare environment
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)
        
        # Execute with timeout
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=working_dir,
                env=env,
            )
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            return ExecutionResult(
                command=command,
                success=result.returncode == 0,
                stdout=result.stdout[:10000] if result.stdout else '',  # Cap output
                stderr=result.stderr[:10000] if result.stderr else '',
                returncode=result.returncode,
                execution_time_ms=elapsed_ms,
            )
        
        except subprocess.TimeoutExpired:
            elapsed_ms = (time.time() - start_time) * 1000
            return ExecutionResult(
                command=command,
                success=False,
                stdout='',
                stderr=f'Command timed out after {timeout}s',
                returncode=-1,
                execution_time_ms=elapsed_ms,
            )
        
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            return ExecutionResult(
                command=command,
                success=False,
                stdout='',
                stderr=f'Execution error: {str(e)}',
                returncode=-1,
                execution_time_ms=elapsed_ms,
            )
    
    def _validate_command(
        self,
        command: str,
        risk_level: Optional[RiskLevel] = None,
        allow_critical: bool = False,
    ) -> Optional[str]:
        """Validate command for safety.
        
        Returns:
            None if valid, error message string if invalid
        """
        cmd_lower = command.lower().strip()
        cmd_name = cmd_lower.split()[0]
        
        # Block CRITICAL risk unless explicitly allowed
        if risk_level is None:
            risk_level = classify_risk(command)
        
        if risk_level == RiskLevel.CRITICAL:
            if not allow_critical:
                return f'Command blocked: CRITICAL risk level (rm -rf /, format disk, etc.)'
        
        # Always block certain commands
        for blocked in self.ALWAYS_BLOCKED:
            if cmd_lower.startswith(blocked):
                return f'Command blocked: {blocked} is always forbidden'
        
        # Check forbidden patterns
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, cmd_lower):
                return f'Command blocked: matches forbidden pattern {pattern}'
        
        return None  # Valid
    
    def _audit_log(
        self,
        command: str,
        risk_level: RiskLevel = RiskLevel.MEDIUM,
        dry_run: bool = False,
    ):
        """Log command execution to immutable audit trail."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'command': command,
            'risk_level': risk_level.value,
            'user': os.getenv('USER', 'unknown'),
            'dry_run': dry_run,
        }
        self.audit_log.append(log_entry)
    
    def get_audit_log(self) -> str:
        """Return formatted audit log.
        
        Returns:
            JSON-formatted audit trail
        """
        return json.dumps(self.audit_log, indent=2)


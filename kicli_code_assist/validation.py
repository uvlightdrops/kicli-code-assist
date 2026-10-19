"""Input validation for LLM operations.

Prevents user mistakes, bad UX, and API errors by validating before sending:
- Prompts (length, content)
- File paths (no traversal, exists)
- Context size (model token limits)
- Shell commands (basic syntax)
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ValidationError(ValueError):
    """Raised when input validation fails."""

    def __init__(self, message: str, suggestion: Optional[str] = None):
        self.message = message
        self.suggestion = suggestion
        super().__init__(message)

    def user_message(self) -> str:
        """Format for UI display."""
        msg = f"❌ {self.message}"
        if self.suggestion:
            msg += f"\n💡 {self.suggestion}"
        return msg


class PromptValidator:
    """Validates user prompts before sending to LLM."""

    # Typical token limits per model
    TOKEN_LIMITS = {
        "gpt-4": 8192,
        "gpt-4-turbo": 128000,
        "gpt-3.5-turbo": 4096,
        "claude-3-opus": 200000,
        "claude-3-sonnet": 200000,
        "mistral-large": 32000,
    }

    MIN_PROMPT_LENGTH = 5  # At least a few characters
    MAX_PROMPT_LENGTH = 50000  # Absolute max for UI sanity
    ESTIMATE_CHARS_PER_TOKEN = 4  # Rough estimate

    @staticmethod
    def validate_prompt(prompt: str, model: Optional[str] = None) -> None:
        """Validate user prompt before sending.

        Args:
            prompt: User's text input
            model: Model name (for token limit check)

        Raises:
            ValidationError: If prompt is invalid
        """
        if not prompt:
            raise ValidationError(
                "Prompt cannot be empty",
                suggestion="Type your request in the input field",
            )

        # Check length
        if len(prompt) < PromptValidator.MIN_PROMPT_LENGTH:
            raise ValidationError(
                f"Prompt too short (minimum {PromptValidator.MIN_PROMPT_LENGTH} characters)",
                suggestion="Provide more detail in your request",
            )

        if len(prompt) > PromptValidator.MAX_PROMPT_LENGTH:
            raise ValidationError(
                f"Prompt too long ({len(prompt)} chars, max {PromptValidator.MAX_PROMPT_LENGTH})",
                suggestion="Reduce the prompt or split into multiple requests",
            )

        # Check token estimate
        if model:
            limit = PromptValidator.TOKEN_LIMITS.get(model)
            if limit:
                estimated_tokens = len(prompt) / PromptValidator.ESTIMATE_CHARS_PER_TOKEN
                if estimated_tokens > limit * 0.8:  # 80% of limit
                    raise ValidationError(
                        f"Prompt may exceed {model} token limit (~{estimated_tokens:.0f} tokens)",
                        suggestion=f"Use a model with higher limits or reduce context",
                    )

        # Check for suspicious patterns
        if re.search(r"^[\s\n]+$", prompt):
            raise ValidationError(
                "Prompt contains only whitespace",
                suggestion="Type your actual request",
            )

        logger.debug(f"✓ Prompt validated ({len(prompt)} chars)")


class FilePathValidator:
    """Validates file paths for safety and existence."""

    # Blocked patterns (path traversal, absolute paths outside project)
    BLOCKED_PATTERNS = [
        r"\.\.",  # Parent directory traversal
        r"^/etc/",  # System directories
        r"^/root/",
        r"^C:\\",  # Windows absolute paths
        r"^/proc/",
        r"^/sys/",
    ]

    @staticmethod
    def validate_path(path: str, base_dir: Optional[Path] = None) -> Path:
        """Validate a file path for safety.

        Args:
            path: File path (relative or absolute)
            base_dir: Base directory to resolve against (usually project root)

        Returns:
            Resolved Path object

        Raises:
            ValidationError: If path is unsafe or doesn't exist
        """
        if not path:
            raise ValidationError("File path cannot be empty")

        # Check blocked patterns
        for pattern in FilePathValidator.BLOCKED_PATTERNS:
            if re.search(pattern, path):
                raise ValidationError(
                    f"File path blocked for safety: {path}",
                    suggestion="Use paths within your project directory",
                )

        # Resolve path
        try:
            p = Path(path)
            if not p.is_absolute() and base_dir:
                p = (base_dir / p).resolve()
            else:
                p = p.resolve()
        except Exception as e:
            raise ValidationError(
                f"Invalid file path: {e}",
                suggestion="Check that the path is correct",
            )

        # Check existence and type
        if not p.exists():
            raise ValidationError(
                f"File not found: {p}",
                suggestion="Check the file name and try again",
            )

        if p.is_dir():
            raise ValidationError(
                f"Path is a directory, not a file: {p}",
                suggestion="Select a specific file within the directory",
            )

        # Check if it's a symlink outside project (security)
        if p.is_symlink() and base_dir:
            try:
                p.resolve().relative_to(base_dir.resolve())
            except ValueError:
                raise ValidationError(
                    f"Symlink points outside project: {p}",
                    suggestion="Use files within your project directory",
                )

        logger.debug(f"✓ File path validated: {p}")
        return p

    @staticmethod
    def validate_paths(paths: list[str], base_dir: Optional[Path] = None) -> list[Path]:
        """Validate multiple file paths.

        Returns:
            List of validated Path objects
        """
        result = []
        for path in paths:
            try:
                result.append(FilePathValidator.validate_path(path, base_dir))
            except ValidationError as e:
                logger.error(f"Invalid path in batch: {e.message}")
                raise
        return result


class ContextValidator:
    """Validates context size against model limits."""

    # Approximate token counts
    ESTIMATE_CHARS_PER_TOKEN = 4
    BUFFER_TOKENS = 500  # Reserve for response

    @staticmethod
    def validate_context_size(
        context_text: str,
        model: str,
        max_tokens: Optional[int] = None,
    ) -> None:
        """Validate that context fits within model limits.

        Args:
            context_text: Full context (prompt + files)
            model: Model name
            max_tokens: Override model token limit

        Raises:
            ValidationError: If context is too large
        """
        if not context_text:
            logger.debug("✓ Empty context (0 tokens)")
            return

        estimated_tokens = (
            len(context_text) / ContextValidator.ESTIMATE_CHARS_PER_TOKEN
        )
        available = max_tokens or 4096  # Default fallback

        if estimated_tokens + ContextValidator.BUFFER_TOKENS > available:
            used_pct = (estimated_tokens / available) * 100
            raise ValidationError(
                f"Context too large for {model} ({used_pct:.0f}% of token limit)",
                suggestion=f"Reduce files or use a model with higher limits",
            )

        logger.debug(
            f"✓ Context validated ({estimated_tokens:.0f} tokens / {available} limit)"
        )


class ShellCommandValidator:
    """Validates shell commands before execution."""

    # Dangerous commands to block
    DANGEROUS_PATTERNS = [
        r"rm\s+-rf\s+/",  # Recursive delete from root
        r":\(\).*\(\)",  # Fork bomb
        r">\s*/dev/sda",  # Write to device
        r";\s*reboot",  # Shutdown
        r";\s*halt",
        r";\s*poweroff",
    ]

    # Allowed shell builtins (safe)
    SAFE_BUILTINS = {
        "echo", "cd", "pwd", "ls", "cat", "grep", "sed", "awk",
        "find", "head", "tail", "wc", "sort", "uniq", "cut",
        "test", "if", "then", "else", "for", "while",
    }

    @staticmethod
    def validate_command(command: str) -> None:
        """Validate a shell command for safety.

        Args:
            command: Shell command to execute

        Raises:
            ValidationError: If command is dangerous
        """
        if not command or not command.strip():
            raise ValidationError("Command cannot be empty")

        # Check for dangerous patterns
        for pattern in ShellCommandValidator.DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                raise ValidationError(
                    "Command blocked for safety (destructive operation detected)",
                    suggestion="Review your command before executing",
                )

        # Check for sudo (requires extra approval)
        if re.search(r"^\s*sudo\s", command):
            raise ValidationError(
                "Sudo commands require explicit approval in settings",
                suggestion="Ask operator to enable sudo or run without sudo",
            )

        # Warn if combining commands (shell pipes can hide behavior)
        if "|" in command or "&&" in command or "||" in command:
            logger.warning(
                f"Command uses pipes/conditionals (verify it's safe): {command[:50]}..."
            )

        logger.debug(f"✓ Command validated: {command[:50]}...")


def validate_all(
    prompt: str,
    files: list[str],
    model: str,
    base_dir: Optional[Path] = None,
    command: Optional[str] = None,
) -> None:
    """Run all validations in one call.

    Args:
        prompt: User prompt
        files: List of file paths
        model: LLM model name
        base_dir: Project base directory
        command: Optional shell command to validate

    Raises:
        ValidationError: If any validation fails
    """
    # Validate prompt
    PromptValidator.validate_prompt(prompt, model)

    # Validate file paths
    if files:
        FilePathValidator.validate_paths(files, base_dir)

    # Validate combined context size
    context = prompt + "\n" + "\n".join(files)
    ContextValidator.validate_context_size(context, model)

    # Validate shell command if provided
    if command:
        ShellCommandValidator.validate_command(command)

    logger.info(f"✓ All validations passed (prompt={len(prompt)} chars, files={len(files)})")

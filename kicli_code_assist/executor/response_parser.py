"""Parse shell command proposals from LLM responses.

Extracts structured shell commands from:
- XML-style <shell_execute> blocks (primary format)
- Markdown code blocks ````bash```` (fallback heuristic)

Returns ShellCommandBatch for HITL approval and execution.
"""

from __future__ import annotations

import re
import json
from dataclasses import dataclass
from typing import Optional, List, Union
from pathlib import Path

from .shell_execution import ShellCommand, ShellCommandBatch, RiskLevel, classify_risk


class ParseError(Exception):
    """Raised when parsing LLM response fails."""
    pass


class ShellExecutionResponseParser:
    """Parse LLM responses for shell command proposals."""

    # XML-style block format: <shell_execute> ... </shell_execute>
    XML_SHELL_BLOCK_PATTERN = re.compile(
        r'<shell_execute>\s*(.*?)\s*</shell_execute>',
        re.DOTALL | re.IGNORECASE
    )

    # Markdown code block with bash/shell: ````bash ... ````
    MARKDOWN_BASH_BLOCK_PATTERN = re.compile(
        r'```(?:bash|shell|sh)\s*\n(.*?)```',
        re.DOTALL | re.IGNORECASE
    )

    @classmethod
    def parse(cls, response: str) -> Optional[ShellCommandBatch]:
        """Parse shell commands from LLM response.

        Args:
            response: LLM response text

        Returns:
            ShellCommandBatch if commands found, None otherwise

        Raises:
            ParseError: If response is malformed or command format invalid
        """
        # Try XML format first (primary, most reliable)
        commands = cls._parse_xml_blocks(response)
        if commands:
            return ShellCommandBatch(commands=commands)

        # Fall back to markdown bash blocks (heuristic)
        commands = cls._parse_markdown_blocks(response)
        if commands:
            return ShellCommandBatch(commands=commands)

        return None

    @classmethod
    def _parse_xml_blocks(cls, response: str) -> List[ShellCommand]:
        """Extract commands from <shell_execute> blocks.

        Format:
            <shell_execute>
            {
              "command": "ls -la /tmp",
              "description": "List tmp directory",
              "cwd": "/tmp"
            }
            </shell_execute>

        Also supports simple command strings as fallback:
            <shell_execute>
            ls -la /tmp
            </shell_execute>
        """
        commands = []
        for match in cls.XML_SHELL_BLOCK_PATTERN.finditer(response):
            block_content = match.group(1).strip()

            # Try JSON format first
            try:
                data = json.loads(block_content)
                cmd = cls._build_command_from_dict(data)
                commands.append(cmd)
                continue
            except (json.JSONDecodeError, ValueError, KeyError):
                pass

            # Fall back to plain command string
            if block_content:
                commands.append(
                    ShellCommand(
                        command=block_content,
                        description="Command proposed by LLM"
                    )
                )

        return commands

    @classmethod
    def _parse_markdown_blocks(cls, response: str) -> List[ShellCommand]:
        """Extract commands from markdown ````bash```` blocks.

        Format:
            ````bash
            ls -la /tmp
            echo "test"
            ````

        Each line is treated as a separate command (or multi-line if continued).
        """
        commands = []
        for match in cls.MARKDOWN_BASH_BLOCK_PATTERN.finditer(response):
            block_content = match.group(1).strip()
            if not block_content:
                continue

            # Split by newlines; filter empty lines
            lines = [line.strip() for line in block_content.split('\n') if line.strip()]

            # Try to group multi-line commands (lines ending with \)
            grouped_commands = cls._group_multiline_commands(lines)
            for cmd_text in grouped_commands:
                commands.append(
                    ShellCommand(
                        command=cmd_text,
                        description="Command from markdown block"
                    )
                )

        return commands

    @classmethod
    def _build_command_from_dict(cls, data: dict) -> ShellCommand:
        """Build ShellCommand from parsed JSON/dict.

        Expected keys:
            command (required): shell command string
            description (optional): human-readable description
            cwd (optional): working directory
            timeout (optional): timeout in seconds
            env_vars (optional): dict of environment variables

        Raises:
            ValueError: If command field missing or invalid type
        """
        if 'command' not in data:
            raise ValueError("Missing required field: 'command'")

        cmd_str = data.get('command')
        if not isinstance(cmd_str, str):
            raise ValueError(f"'command' must be string, got {type(cmd_str).__name__}")

        return ShellCommand(
            command=cmd_str.strip(),
            description=data.get('description', ''),
            cwd=data.get('cwd'),
            timeout=data.get('timeout'),
            env_vars=data.get('env_vars', {})
        )

    @classmethod
    def _group_multiline_commands(cls, lines: List[str]) -> List[str]:
        """Group command lines that continue with backslash.

        Args:
            lines: List of command line strings

        Returns:
            List of grouped command strings
        """
        grouped = []
        current_cmd = ''

        for line in lines:
            if current_cmd:
                current_cmd += ' ' + line.rstrip('\\')
            else:
                current_cmd = line.rstrip('\\')

            # If line doesn't end with \, command is complete
            if not line.endswith('\\'):
                grouped.append(current_cmd)
                current_cmd = ''

        # Add any remaining incomplete command
        if current_cmd:
            grouped.append(current_cmd)

        return grouped

    @classmethod
    def validate_batch(cls, batch: ShellCommandBatch) -> tuple[bool, str]:
        """Validate ShellCommandBatch before submission to approval.

        Args:
            batch: ShellCommandBatch to validate

        Returns:
            (is_valid, error_message)
        """
        if not batch.commands:
            return False, "Batch contains no commands"

        if len(batch.commands) > 50:
            return False, f"Batch too large: {len(batch.commands)} commands (max 50)"

        for i, cmd in enumerate(batch.commands):
            if not cmd.command or not cmd.command.strip():
                return False, f"Command {i} is empty"

            if len(cmd.command) > 2000:
                return False, f"Command {i} too long: {len(cmd.command)} chars (max 2000)"

        return True, ""


class ShellResponseIntegration:
    """Integration helper for ChatSession and TUI to use parser."""

    def __init__(self):
        self.parser = ShellExecutionResponseParser
        self.last_parsed_batch: Optional[ShellCommandBatch] = None
        self.parse_errors: List[str] = []

    def try_parse(self, response: str) -> Optional[ShellCommandBatch]:
        """Attempt to parse response, capture errors."""
        self.parse_errors.clear()
        try:
            batch = self.parser.parse(response)
            if batch:
                is_valid, error = self.parser.validate_batch(batch)
                if not is_valid:
                    self.parse_errors.append(error)
                    return None
                self.last_parsed_batch = batch
            return batch
        except ParseError as e:
            self.parse_errors.append(str(e))
            return None
        except Exception as e:
            self.parse_errors.append(f"Unexpected error: {e}")
            return None

    def get_summary(self) -> dict:
        """Get summary of last parse attempt."""
        return {
            "batch": self.last_parsed_batch,
            "command_count": len(self.last_parsed_batch.commands) if self.last_parsed_batch else 0,
            "errors": self.parse_errors
        }

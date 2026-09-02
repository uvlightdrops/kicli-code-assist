"""Diff engine for code change management and visualization."""

import difflib
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple, NamedTuple
from dataclasses import dataclass
from enum import Enum

from ki_core import Config


class DiffFormat(Enum):
    """Supported diff formats."""
    UNIFIED = "unified"
    SIDE_BY_SIDE = "side_by_side"
    INLINE = "inline"


@dataclass
class LineChange:
    """Single line change in a diff."""
    line_num_old: Optional[int]
    line_num_new: Optional[int]
    content: str
    change_type: str  # added, removed, context, modified


@dataclass
class FileDiff:
    """Diff for a single file."""
    file_path: str
    original_content: str
    modified_content: str
    is_new: bool = False
    is_deleted: bool = False
    similarity: float = 1.0  # 0-1, how similar old and new are

    def get_changes(self) -> List[LineChange]:
        """Get line-by-line changes."""
        changes = []

        if self.is_new:
            for i, line in enumerate(self.modified_content.split("\n"), 1):
                changes.append(LineChange(None, i, line, "added"))
        elif self.is_deleted:
            for i, line in enumerate(self.original_content.split("\n"), 1):
                changes.append(LineChange(i, None, line, "removed"))
        else:
            old_lines = self.original_content.split("\n")
            new_lines = self.modified_content.split("\n")

            differ = difflib.SequenceMatcher(None, old_lines, new_lines)

            old_line_num = 1
            new_line_num = 1

            for tag, i1, i2, j1, j2 in differ.get_opcodes():
                if tag == "equal":
                    for k in range(i2 - i1):
                        changes.append(
                            LineChange(
                                old_line_num + k,
                                new_line_num + k,
                                old_lines[i1 + k],
                                "context",
                            )
                        )
                    old_line_num += i2 - i1
                    new_line_num += j2 - j1
                elif tag == "replace":
                    for k in range(i2 - i1):
                        if i1 + k < len(old_lines):
                            changes.append(
                                LineChange(
                                    old_line_num + k,
                                    None,
                                    old_lines[i1 + k],
                                    "removed",
                                )
                            )
                    for k in range(j2 - j1):
                        if j1 + k < len(new_lines):
                            changes.append(
                                LineChange(
                                    None,
                                    new_line_num + k,
                                    new_lines[j1 + k],
                                    "added",
                                )
                            )
                    old_line_num += i2 - i1
                    new_line_num += j2 - j1
                elif tag == "delete":
                    for k in range(i2 - i1):
                        if i1 + k < len(old_lines):
                            changes.append(
                                LineChange(
                                    old_line_num + k,
                                    None,
                                    old_lines[i1 + k],
                                    "removed",
                                )
                            )
                    old_line_num += i2 - i1
                elif tag == "insert":
                    for k in range(j2 - j1):
                        if j1 + k < len(new_lines):
                            changes.append(
                                LineChange(
                                    None,
                                    new_line_num + k,
                                    new_lines[j1 + k],
                                    "added",
                                )
                            )
                    new_line_num += j2 - j1

        return changes

    def to_unified_diff(self, context_lines: int = 3) -> str:
        """Generate unified diff format."""
        old_lines = self.original_content.split("\n")
        new_lines = self.modified_content.split("\n")

        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{self.file_path}",
            tofile=f"b/{self.file_path}",
            lineterm="",
            n=context_lines,
        )

        return "\n".join(diff)

    def count_changes(self) -> Tuple[int, int, int]:
        """Count additions, removals, and context lines."""
        changes = self.get_changes()
        added = sum(1 for c in changes if c.change_type == "added")
        removed = sum(1 for c in changes if c.change_type == "removed")
        context = sum(1 for c in changes if c.change_type == "context")
        return added, removed, context


class LLMOutputParser:
    """Parse LLM-generated code and extract file changes."""

    # Common markers for code blocks
    CODE_BLOCK_PATTERNS = [
        r"```(\w+)?\n(.*?)\n```",  # Markdown code blocks
        r"<code>(.*?)</code>",  # HTML code tags
        r"\[START_CODE\](.*?)\[END_CODE\]",  # Custom markers
    ]

    FILE_REFERENCE_PATTERNS = [
        r"(?:in file|edit|modify|update|at)\s+['\"]?([^\s'\"]+\.(?:py|js|go|ts|tsx|jsx))['\"]?",
        r"(?:file|path):\s*['\"]?([^\s'\"]+\.(?:py|js|go|ts|tsx|jsx))['\"]?",
        r"(?:create|add|new file)\s+['\"]?([^\s'\"]+\.(?:py|js|go|ts|tsx|jsx))['\"]?",
        r"(?:^|\W)([a-zA-Z_][a-zA-Z0-9_]*\.(?:py|js|go|ts|tsx|jsx))(?:\W|$)",
    ]

    def __init__(self, config: Optional[Config] = None):
        """Initialize parser.

        Args:
            config: Configuration object
        """
        self.config = config or Config.from_env()

    def extract_code_blocks(self, text: str) -> List[Tuple[str, str]]:
        """Extract code blocks from LLM output.

        Args:
            text: LLM output text

        Returns:
            List of (language, code) tuples
        """
        code_blocks = []

        for pattern in self.CODE_BLOCK_PATTERNS:
            for match in re.finditer(pattern, text, re.DOTALL):
                if match.lastindex and match.lastindex >= 2:
                    lang = match.group(1) or "plaintext"
                    code = match.group(2)
                    code_blocks.append((lang, code))
                elif match.lastindex == 1:
                    code = match.group(1)
                    code_blocks.append(("plaintext", code))

        return code_blocks

    def extract_file_references(self, text: str) -> List[str]:
        """Extract file paths mentioned in LLM output.

        Args:
            text: LLM output text

        Returns:
            List of file paths
        """
        files = []

        for pattern in self.FILE_REFERENCE_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                file_path = match.group(1)
                if file_path and file_path not in files:
                    files.append(file_path)

        return files

    def parse_code_with_path(self, text: str) -> List[Tuple[str, str, str]]:
        """Parse LLM output to extract (file_path, language, code) tuples.

        Args:
            text: LLM output text

        Returns:
            List of (file_path, language, code) tuples
        """
        results = []
        file_refs = self.extract_file_references(text)
        code_blocks = self.extract_code_blocks(text)

        # Try to match files with code blocks
        for i, (lang, code) in enumerate(code_blocks):
            if i < len(file_refs):
                file_path = file_refs[i]
                results.append((file_path, lang, code))

        # If no file refs, still return code blocks
        if not file_refs:
            for lang, code in code_blocks:
                results.append(("unknown.txt", lang, code))

        return results

    def estimate_confidence(self, file_path: str, code: str) -> float:
        """Estimate confidence score for extracted code.

        Args:
            file_path: File path
            code: Code content

        Returns:
            Confidence score (0-1)
        """
        score = 0.5  # Base score

        # Check for complete functions/classes
        if re.search(r"^def\s+\w+\(", code, re.MULTILINE) or re.search(
            r"^class\s+\w+", code, re.MULTILINE
        ):
            score += 0.2

        # Check for file extension match
        if file_path:
            ext = Path(file_path).suffix
            if ext in [".py", ".js", ".go", ".ts", ".jsx", ".tsx"]:
                score += 0.1

        # Check for imports/requires
        if re.search(r"^(?:import|require|from)\s+", code, re.MULTILINE):
            score += 0.1

        # Deduct for obvious placeholders
        if "..." in code or "TODO" in code or "FIXME" in code:
            score -= 0.15

        return min(max(score, 0.0), 1.0)


class DiffGenerator:
    """Generate diffs between original and modified code."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize diff generator.

        Args:
            config: Configuration object
        """
        self.config = config or Config.from_env()
        self.context_lines = self.config.diff_context_lines
        self.format = DiffFormat(self.config.diff_format)
        self.auto_apply_threshold = self.config.diff_auto_apply_threshold

    def generate_file_diff(
        self,
        file_path: str,
        original: str,
        modified: str,
    ) -> FileDiff:
        """Generate diff for a file.

        Args:
            file_path: Path to file
            original: Original content
            modified: Modified content

        Returns:
            FileDiff object
        """
        is_new = not original
        is_deleted = not modified

        # Calculate similarity
        similarity = self._calculate_similarity(original, modified)

        return FileDiff(
            file_path=file_path,
            original_content=original,
            modified_content=modified,
            is_new=is_new,
            is_deleted=is_deleted,
            similarity=similarity,
        )

    def _calculate_similarity(self, original: str, modified: str) -> float:
        """Calculate similarity between two texts (0-1)."""
        if not original and not modified:
            return 1.0
        if not original or not modified:
            return 0.0

        matcher = difflib.SequenceMatcher(None, original, modified)
        return matcher.ratio()

    def generate_diffs(
        self,
        files: Dict[str, Tuple[str, str]],
    ) -> List[FileDiff]:
        """Generate diffs for multiple files.

        Args:
            files: Dict of {file_path: (original, modified)}

        Returns:
            List of FileDiff objects
        """
        diffs = []

        for file_path, (original, modified) in files.items():
            diff = self.generate_file_diff(file_path, original, modified)
            diffs.append(diff)

        return sorted(diffs, key=lambda d: d.similarity)

    def should_auto_apply(self, diff: FileDiff) -> bool:
        """Determine if change should be auto-applied.

        Args:
            diff: FileDiff object

        Returns:
            True if confidence is high enough
        """
        return diff.similarity >= self.auto_apply_threshold

    def apply_diff(self, original: str, diff_text: str) -> Optional[str]:
        """Apply a unified diff to original content.

        Args:
            original: Original content
            diff_text: Unified diff text

        Returns:
            Modified content or None if patch fails
        """
        try:
            import io
            patch = difflib.unified_diff(
                original.split("\n"),
                [],
                lineterm="",
            )
            # Simple patch application
            lines = original.split("\n")

            # Parse diff_text
            for line in diff_text.split("\n"):
                if line.startswith("---") or line.startswith("+++"):
                    continue
                elif line.startswith("@@"):
                    continue
                elif line.startswith("-") and not line.startswith("---"):
                    try:
                        content = line[1:]
                        lines.remove(content)
                    except ValueError:
                        pass
                elif line.startswith("+") and not line.startswith("+++"):
                    content = line[1:]
                    lines.append(content)

            return "\n".join(lines)
        except Exception:
            return None

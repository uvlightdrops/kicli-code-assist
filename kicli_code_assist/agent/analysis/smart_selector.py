"""Minimal smart context selector."""

from pathlib import Path
from typing import List, Dict


class SmartSelector:
    """Minimal token-aware context selector."""

    def __init__(self, max_tokens: int = 4000):
        self.max_tokens = max_tokens
        self.TOKENS_PER_CHAR = 0.25

    def select_context(
        self,
        query: str,
        relevant_files: List[Path],
        max_lines: int = 100,
    ) -> Dict[Path, str]:
        """Select code snippets within token budget."""
        result = {}
        tokens_used = 0

        for file_path in relevant_files:
            if tokens_used >= self.max_tokens:
                break

            try:
                content = file_path.read_text()
                lines = content.split("\n")[:max_lines]
                snippet = "\n".join(lines)
                tokens = int(len(snippet) * self.TOKENS_PER_CHAR)

                if tokens_used + tokens <= self.max_tokens:
                    result[file_path] = snippet
                    tokens_used += tokens
            except Exception:
                pass

        return result

    def estimate_tokens(self, text: str) -> int:
        """Rough token estimate."""
        return max(1, int(len(text) * self.TOKENS_PER_CHAR))

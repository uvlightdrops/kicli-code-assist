"""Minimal semantic indexer."""

from pathlib import Path
from typing import List, Optional


class SemanticIndexer:
    """Minimal in-memory indexer for quick iteration."""

    def __init__(self, cache_path: Optional[Path] = None):
        self.cache = {}  # Simple dict cache

    def index_function(self, file_path: Path, func_name: str, summary: str) -> None:
        """Add function to index."""
        key = f"{file_path}:{func_name}"
        self.cache[key] = summary

    def search(self, query: str) -> List[tuple[str, str]]:
        """Quick search in index."""
        results = []
        query_lower = query.lower()
        for (file_path, func_name), summary in self.cache.items():
            if query_lower in func_name.lower() or query_lower in summary.lower():
                results.append((f"{file_path}:{func_name}", summary))
        return results

    def clear(self) -> None:
        """Clear index."""
        self.cache.clear()

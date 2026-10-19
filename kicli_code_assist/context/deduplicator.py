"""File context deduplication manager.

Tracks which files have been added to context and prevents duplicates
from being loaded again, improving performance and reducing token waste.
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass, field
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class DeduplicationStats:
    """Statistics about deduplication hits."""
    total_load_attempts: int = 0
    successful_loads: int = 0
    deduplicated_files: int = 0  # Files that were already loaded
    dedup_savings_bytes: int = 0
    dedup_hits: Dict[str, int] = field(default_factory=dict)  # Track per-file hits

    def record_load_attempt(self) -> None:
        """Record a load attempt."""
        self.total_load_attempts += 1

    def record_successful_load(self, file_size: int) -> None:
        """Record a successful new file load."""
        self.successful_loads += 1

    def record_dedup_hit(self, file_path: str, file_size: int) -> None:
        """Record when a file is deduplicated (already in context)."""
        self.deduplicated_files += 1
        self.dedup_savings_bytes += file_size
        normalized_path = str(Path(file_path).resolve())
        self.dedup_hits[normalized_path] = self.dedup_hits.get(normalized_path, 0) + 1

    def get_stats(self) -> dict:
        """Get deduplication statistics as dict."""
        return {
            "total_attempts": self.total_load_attempts,
            "successful_loads": self.successful_loads,
            "deduplicated_files": self.deduplicated_files,
            "dedup_percentage": (
                (self.deduplicated_files / self.total_load_attempts * 100)
                if self.total_load_attempts > 0
                else 0
            ),
            "bytes_saved": self.dedup_savings_bytes,
            "top_deduplicated": sorted(
                self.dedup_hits.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
        }


class ContextDeduplicator:
    """Manages deduplication of files in context window."""

    def __init__(self):
        """Initialize deduplicator."""
        self.loaded_files: Dict[str, int] = {}  # Map file path to size
        self.file_hashes: Dict[str, str] = {}  # Map file path to content hash
        self.stats = DeduplicationStats()

    def add_file(self, file_path: str, file_size: int, file_hash: Optional[str] = None) -> None:
        """Register a file as loaded to context.

        Args:
            file_path: Full path to file
            file_size: File size in bytes
            file_hash: Optional content hash for validity checking
        """
        normalized_path = str(Path(file_path).resolve())
        self.loaded_files[normalized_path] = file_size
        if file_hash:
            self.file_hashes[normalized_path] = file_hash

    def is_loaded(self, file_path: str) -> bool:
        """Check if a file is already in context.

        Args:
            file_path: Path to check

        Returns:
            True if file was already loaded, False otherwise
        """
        normalized_path = str(Path(file_path).resolve())
        return normalized_path in self.loaded_files

    def check_and_register(self, file_path: str, file_size: int, file_hash: Optional[str] = None) -> bool:
        """Check if file is loaded and register if not.

        This is the main entry point for deduplication logic.

        Args:
            file_path: Path to check
            file_size: File size in bytes
            file_hash: Optional content hash for validity

        Returns:
            True if file is NEW (should be loaded), False if already loaded
        """
        self.stats.record_load_attempt()
        normalized_path = str(Path(file_path).resolve())

        if normalized_path in self.loaded_files:
            # File already loaded - record dedup hit
            self.stats.record_dedup_hit(file_path, file_size)
            logger.info(
                f"📁 Context dedup: '{Path(file_path).name}' cached (found in context) "
                f"[Hit #{self.stats.dedup_hits.get(normalized_path, 1)}]"
            )
            return False

        # New file - register it
        self.add_file(file_path, file_size, file_hash)
        self.stats.record_successful_load(file_size)
        logger.info(
            f"📁 Context dedup: '{Path(file_path).name}' loading (new) [{file_size} bytes]"
        )
        return True

    def clear(self) -> None:
        """Clear all tracked files."""
        self.loaded_files.clear()
        self.file_hashes.clear()
        self.stats = DeduplicationStats()

    def get_loaded_files(self) -> List[str]:
        """Get list of all loaded files."""
        return list(self.loaded_files.keys())

    def get_stats(self) -> dict:
        """Get deduplication statistics."""
        return self.stats.get_stats()

    def _compute_file_hash(self, file_path: str) -> str:
        """Compute SHA256 hash of file content.

        Args:
            file_path: Path to file

        Returns:
            Hex digest of SHA256 hash
        """
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except (OSError, IOError):
            return ""


# Global instance for app-level tracking
_deduplicator: Optional[ContextDeduplicator] = None


def get_deduplicator() -> ContextDeduplicator:
    """Get or create global deduplicator instance."""
    global _deduplicator
    if _deduplicator is None:
        _deduplicator = ContextDeduplicator()
    return _deduplicator


def reset_deduplicator() -> None:
    """Reset global deduplicator (useful for testing)."""
    global _deduplicator
    _deduplicator = None

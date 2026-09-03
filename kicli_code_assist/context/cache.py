"""Context caching system with LRU eviction and TTL management."""

import hashlib
import json
import time
from pathlib import Path
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import OrderedDict
from datetime import datetime, timedelta

from ki_core import Config


@dataclass
class CacheEntry:
    """Single cache entry with metadata."""
    key: str
    content: str
    file_hashes: Dict[str, str]  # Map of file paths to content hashes
    timestamp: float  # Creation timestamp
    ttl_hours: int
    size_kb: float

    def is_expired(self, ttl_hours: int) -> bool:
        """Check if entry has expired."""
        age_hours = (time.time() - self.timestamp) / 3600
        return age_hours > ttl_hours

    def is_valid_for_files(self, file_hashes: Dict[str, str]) -> bool:
        """Check if cached content is still valid for current files."""
        return self.file_hashes == file_hashes

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "CacheEntry":
        """Create from dict."""
        return cls(**data)


class ContextCache:
    """LRU cache for project context with TTL support."""

    def __init__(
        self,
        cache_dir: Optional[str] = None,
        config: Optional[Config] = None,
    ):
        """Initialize context cache.

        Args:
            cache_dir: Directory for cache storage
            config: Configuration object
        """
        self.config = config or Config.from_env()
        from kicli_code_assist.chat_history import get_cache_dir

        configured_cache_dir = cache_dir or self.config.kicli_cache_dir
        base_cache_dir = Path(configured_cache_dir) if configured_cache_dir else get_cache_dir()
        self.cache_dir = base_cache_dir / "context_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.max_cache_size_mb = self.config.context_cache_max_size_mb
        self.ttl_hours = self.config.context_cache_ttl_hours
        self.cache_enabled = self.config.context_cache_enabled

        # In-memory cache (LRU)
        self.memory_cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.current_size_kb = 0.0

        # Load existing cache from disk
        self._load_cache_from_disk()

    def _load_cache_from_disk(self) -> None:
        """Load cache index from disk."""
        index_file = self.cache_dir / "index.json"
        if not index_file.exists():
            return

        try:
            with open(index_file, "r") as f:
                data = json.load(f)
                for key, entry_data in data.items():
                    entry = CacheEntry.from_dict(entry_data)
                    # Skip expired entries
                    if not entry.is_expired(self.ttl_hours):
                        self.memory_cache[key] = entry
                        self.current_size_kb += entry.size_kb
        except (json.JSONDecodeError, OSError):
            pass

    def _save_cache_to_disk(self) -> None:
        """Save cache index to disk."""
        if not self.cache_enabled:
            return

        index_file = self.cache_dir / "index.json"
        try:
            data = {
                key: entry.to_dict()
                for key, entry in self.memory_cache.items()
                if not entry.is_expired(self.ttl_hours)
            }
            with open(index_file, "w") as f:
                json.dump(data, f, indent=2)
        except OSError:
            pass

    def _get_cache_file_path(self, key: str) -> Path:
        """Get file path for cache entry."""
        safe_key = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / f"{safe_key}.cache"

    def get(self, key: str, file_hashes: Optional[Dict[str, str]] = None) -> Optional[str]:
        """Get cached content.

        Args:
            key: Cache key
            file_hashes: File hashes for validation (optional)

        Returns:
            Cached content if valid, None otherwise
        """
        if not self.cache_enabled:
            return None

        if key not in self.memory_cache:
            return None

        entry = self.memory_cache[key]

        # Check expiration
        if entry.is_expired(self.ttl_hours):
            del self.memory_cache[key]
            self.current_size_kb -= entry.size_kb
            self._save_cache_to_disk()
            return None

        # Check file validity if hashes provided
        if file_hashes and not entry.is_valid_for_files(file_hashes):
            del self.memory_cache[key]
            self.current_size_kb -= entry.size_kb
            self._save_cache_to_disk()
            return None

        # Move to end (LRU)
        self.memory_cache.move_to_end(key)

        # Load from disk
        cache_file = self._get_cache_file_path(key)
        if cache_file.exists():
            try:
                return cache_file.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                return None

        return None

    def set(
        self,
        key: str,
        content: str,
        file_hashes: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Set cached content.

        Args:
            key: Cache key
            content: Content to cache
            file_hashes: File hashes for validation

        Returns:
            True if cached successfully, False if size limit exceeded
        """
        if not self.cache_enabled:
            return False

        content_size_kb = len(content.encode("utf-8")) / 1024

        # Check if content exceeds size limit
        if content_size_kb > self.max_cache_size_mb * 1024:
            return False

        # Make room if needed
        while (
            self.current_size_kb + content_size_kb > self.max_cache_size_mb * 1024
            and self.memory_cache
        ):
            self._evict_lru()

        # Create entry
        entry = CacheEntry(
            key=key,
            content=content,
            file_hashes=file_hashes or {},
            timestamp=time.time(),
            ttl_hours=self.ttl_hours,
            size_kb=content_size_kb,
        )

        # Save to disk
        cache_file = self._get_cache_file_path(key)
        try:
            cache_file.write_text(content, encoding="utf-8")
        except OSError:
            return False

        # Store in memory
        self.memory_cache[key] = entry
        self.current_size_kb += content_size_kb

        self._save_cache_to_disk()
        return True

    def delete(self, key: str) -> bool:
        """Delete cache entry.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        if key not in self.memory_cache:
            return False

        entry = self.memory_cache.pop(key)
        self.current_size_kb -= entry.size_kb

        cache_file = self._get_cache_file_path(key)
        try:
            cache_file.unlink()
        except OSError:
            pass

        self._save_cache_to_disk()
        return True

    def clear(self) -> None:
        """Clear all cache entries."""
        self.memory_cache.clear()
        self.current_size_kb = 0.0

        # Delete cache directory
        try:
            for file in self.cache_dir.glob("*.cache"):
                file.unlink()
        except OSError:
            pass

        # Clear index
        index_file = self.cache_dir / "index.json"
        try:
            index_file.unlink()
        except OSError:
            pass

    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self.memory_cache:
            return

        key, entry = self.memory_cache.popitem(last=False)
        self.current_size_kb -= entry.size_kb

        cache_file = self._get_cache_file_path(key)
        try:
            cache_file.unlink()
        except OSError:
            pass

    def get_stats(self) -> dict:
        """Get cache statistics."""
        valid_entries = [
            e for e in self.memory_cache.values()
            if not e.is_expired(self.ttl_hours)
        ]

        return {
            "enabled": self.cache_enabled,
            "num_entries": len(valid_entries),
            "current_size_mb": self.current_size_kb / 1024,
            "max_size_mb": self.max_cache_size_mb,
            "usage_percent": (self.current_size_kb / (self.max_cache_size_mb * 1024)) * 100
            if self.max_cache_size_mb > 0
            else 0,
            "ttl_hours": self.ttl_hours,
            "cache_dir": str(self.cache_dir),
        }

    def invalidate_by_pattern(self, pattern: str) -> int:
        """Invalidate all cache entries matching a pattern.

        Args:
            pattern: Pattern to match in cache keys

        Returns:
            Number of entries invalidated
        """
        invalidated = 0
        keys_to_delete = [k for k in self.memory_cache.keys() if pattern in k]

        for key in keys_to_delete:
            self.delete(key)
            invalidated += 1

        return invalidated


class ContextCacheManager:
    """High-level manager for context caching."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize cache manager.

        Args:
            config: Configuration object
        """
        self.config = config or Config.from_env()
        self.cache = ContextCache(config=self.config)

    def compute_file_hashes(self, files: Dict[str, str]) -> Dict[str, str]:
        """Compute hashes for a set of files.

        Args:
            files: Dict of file path to content

        Returns:
            Dict of file path to content hash
        """
        hashes = {}
        for path, content in files.items():
            hash_obj = hashlib.sha256(content.encode("utf-8"))
            hashes[path] = hash_obj.hexdigest()
        return hashes

    def get_cached_context(
        self,
        query: str,
        files: Dict[str, str],
    ) -> Optional[str]:
        """Get cached context for query if available.

        Args:
            query: Query string
            files: Dict of file path to content

        Returns:
            Cached context or None if not available
        """
        cache_key = self._make_cache_key(query)
        file_hashes = self.compute_file_hashes(files)
        return self.cache.get(cache_key, file_hashes)

    def cache_context(
        self,
        query: str,
        files: Dict[str, str],
        context: str,
    ) -> bool:
        """Cache context for query.

        Args:
            query: Query string
            files: Dict of file path to content
            context: Formatted context string

        Returns:
            True if cached successfully
        """
        cache_key = self._make_cache_key(query)
        file_hashes = self.compute_file_hashes(files)
        return self.cache.set(cache_key, context, file_hashes)

    def invalidate_for_project(self, project_path: str) -> int:
        """Invalidate all cache for a project.

        Args:
            project_path: Path to project

        Returns:
            Number of entries invalidated
        """
        pattern = hashlib.sha256(project_path.encode()).hexdigest()[:8]
        return self.cache.invalidate_by_pattern(pattern)

    def _make_cache_key(self, query: str) -> str:
        """Create cache key from query."""
        return hashlib.sha256(query.encode()).hexdigest()[:16]

    def get_stats(self) -> dict:
        """Get cache statistics."""
        return self.cache.get_stats()

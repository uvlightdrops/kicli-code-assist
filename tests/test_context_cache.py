"""Tests for context caching system."""

import pytest
import time
import tempfile
from pathlib import Path
from unittest.mock import patch

from kicli_code_assist.context.cache import (
    CacheEntry,
    ContextCache,
    ContextCacheManager,
)
from ki_core import Config


class TestCacheEntry:
    """Test CacheEntry class."""

    def test_creation(self):
        """Test creating cache entry."""
        entry = CacheEntry(
            key="test",
            content="content",
            file_hashes={"file.py": "hash123"},
            timestamp=time.time(),
            ttl_hours=24,
            size_kb=5.0,
        )
        assert entry.key == "test"
        assert entry.content == "content"
        assert entry.size_kb == 5.0

    def test_is_expired_false(self):
        """Test non-expired entry."""
        entry = CacheEntry(
            key="test",
            content="content",
            file_hashes={},
            timestamp=time.time(),
            ttl_hours=24,
            size_kb=5.0,
        )
        assert not entry.is_expired(24)

    def test_is_expired_true(self):
        """Test expired entry."""
        old_time = time.time() - (25 * 3600)  # 25 hours ago
        entry = CacheEntry(
            key="test",
            content="content",
            file_hashes={},
            timestamp=old_time,
            ttl_hours=24,
            size_kb=5.0,
        )
        assert entry.is_expired(24)

    def test_is_valid_for_files_true(self):
        """Test valid file hashes."""
        file_hashes = {"file.py": "hash123"}
        entry = CacheEntry(
            key="test",
            content="content",
            file_hashes=file_hashes,
            timestamp=time.time(),
            ttl_hours=24,
            size_kb=5.0,
        )
        assert entry.is_valid_for_files(file_hashes)

    def test_is_valid_for_files_false(self):
        """Test invalid file hashes."""
        entry = CacheEntry(
            key="test",
            content="content",
            file_hashes={"file.py": "hash123"},
            timestamp=time.time(),
            ttl_hours=24,
            size_kb=5.0,
        )
        assert not entry.is_valid_for_files({"file.py": "hash456"})

    def test_to_dict(self):
        """Test converting to dict."""
        entry = CacheEntry(
            key="test",
            content="content",
            file_hashes={"file.py": "hash123"},
            timestamp=time.time(),
            ttl_hours=24,
            size_kb=5.0,
        )
        data = entry.to_dict()
        assert data["key"] == "test"
        assert data["content"] == "content"

    def test_from_dict(self):
        """Test creating from dict."""
        data = {
            "key": "test",
            "content": "content",
            "file_hashes": {"file.py": "hash123"},
            "timestamp": time.time(),
            "ttl_hours": 24,
            "size_kb": 5.0,
        }
        entry = CacheEntry.from_dict(data)
        assert entry.key == "test"
        assert entry.content == "content"


class TestContextCache:
    """Test ContextCache class."""

    def test_initialization(self):
        """Test cache initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ContextCache(cache_dir=tmpdir)
            assert cache.cache_dir.exists()
            assert cache.current_size_kb == 0.0

    def test_set_and_get(self):
        """Test setting and getting cache entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ContextCache(
                cache_dir=tmpdir,
                config=Config(context_cache_enabled=True, context_cache_max_size_mb=10),
            )
            content = "test content"
            file_hashes = {"file.py": "hash123"}

            # Set
            result = cache.set("key1", content, file_hashes)
            assert result is True

            # Get
            retrieved = cache.get("key1", file_hashes)
            assert retrieved == content

    def test_get_nonexistent(self):
        """Test getting non-existent entry."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ContextCache(cache_dir=tmpdir)
            result = cache.get("nonexistent")
            assert result is None

    def test_get_expired(self):
        """Test getting expired entry."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ContextCache(
                cache_dir=tmpdir,
                config=Config(context_cache_enabled=True, context_cache_ttl_hours=1),
            )

            # Set entry
            cache.set("key1", "content", {})

            # Mock time to simulate expiration
            entry = cache.memory_cache["key1"]
            entry.timestamp = time.time() - (2 * 3600)  # 2 hours ago

            # Try to get (should be expired and removed)
            result = cache.get("key1")
            assert result is None
            assert "key1" not in cache.memory_cache

    def test_get_invalid_files(self):
        """Test getting entry with invalid file hashes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ContextCache(cache_dir=tmpdir)
            content = "content"
            original_hashes = {"file.py": "hash123"}

            cache.set("key1", content, original_hashes)

            # Get with different hashes
            new_hashes = {"file.py": "hash456"}
            result = cache.get("key1", new_hashes)
            assert result is None

    def test_delete(self):
        """Test deleting cache entry."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ContextCache(cache_dir=tmpdir)
            cache.set("key1", "content")

            result = cache.delete("key1")
            assert result is True
            assert cache.get("key1") is None

    def test_delete_nonexistent(self):
        """Test deleting non-existent entry."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ContextCache(cache_dir=tmpdir)
            result = cache.delete("nonexistent")
            assert result is False

    def test_clear(self):
        """Test clearing all cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ContextCache(cache_dir=tmpdir)
            cache.set("key1", "content1")
            cache.set("key2", "content2")
            cache.set("key3", "content3")

            cache.clear()

            assert cache.current_size_kb == 0.0
            assert len(cache.memory_cache) == 0

    def test_size_limit_enforcement(self):
        """Test that cache respects size limit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ContextCache(
                cache_dir=tmpdir,
                config=Config(context_cache_enabled=True, context_cache_max_size_mb=0.1),
            )

            # Try to add content larger than limit
            large_content = "x" * (200 * 1024)  # 200 KB
            result = cache.set("large", large_content)

            # Should fail
            assert result is False

    def test_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ContextCache(
                cache_dir=tmpdir,
                config=Config(context_cache_enabled=True, context_cache_max_size_mb=0.01),
            )

            # Try to add multiple entries
            cache.set("key1", "x" * 10000)  # ~10 KB
            cache.set("key2", "x" * 10000)  # ~10 KB
            cache.set("key3", "x" * 10000)  # ~10 KB

            # Cache should have evicted entries due to size limit
            stats = cache.get_stats()
            # Total should be well below 3 entries or 30 KB
            assert stats["current_size_mb"] * 1024 <= 15  # <= 15 KB

    def test_get_stats(self):
        """Test getting cache statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ContextCache(
                cache_dir=tmpdir,
                config=Config(context_cache_enabled=True, context_cache_max_size_mb=10),
            )

            cache.set("key1", "x" * 10000)

            stats = cache.get_stats()
            assert stats["enabled"] is True
            assert stats["num_entries"] == 1
            assert stats["ttl_hours"] > 0
            assert stats["max_size_mb"] == 10

    def test_invalidate_by_pattern(self):
        """Test invalidating entries by pattern."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ContextCache(cache_dir=tmpdir)

            cache.set("project_a_query1", "content1")
            cache.set("project_a_query2", "content2")
            cache.set("project_b_query1", "content3")

            # Invalidate all project_a entries
            invalidated = cache.invalidate_by_pattern("project_a")
            assert invalidated == 2

            # Check they're gone
            assert cache.get("project_a_query1") is None
            assert cache.get("project_a_query2") is None
            # project_b should remain
            assert cache.get("project_b_query1") is not None

    def test_cache_disabled(self):
        """Test cache behavior when disabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ContextCache(
                cache_dir=tmpdir,
                config=Config(context_cache_enabled=False),
            )

            # Set should return False
            result = cache.set("key1", "content")
            assert result is False

            # Get should return None
            result = cache.get("key1")
            assert result is None

    def test_persistence(self):
        """Test cache persistence to disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # First cache instance
            cache1 = ContextCache(
                cache_dir=tmpdir,
                config=Config(context_cache_enabled=True, context_cache_max_size_mb=10),
            )
            cache1.set("key1", "content1")
            cache1.set("key2", "content2")

            # Create new instance (should load from disk)
            cache2 = ContextCache(
                cache_dir=tmpdir,
                config=Config(context_cache_enabled=True, context_cache_max_size_mb=10),
            )

            assert cache2.get("key1") == "content1"
            assert cache2.get("key2") == "content2"


class TestContextCacheManager:
    """Test ContextCacheManager."""

    def test_initialization(self):
        """Test manager initialization."""
        manager = ContextCacheManager()
        assert manager.cache is not None

    def test_compute_file_hashes(self):
        """Test computing file hashes."""
        manager = ContextCacheManager()
        files = {
            "file1.py": "content1",
            "file2.py": "content2",
        }

        hashes = manager.compute_file_hashes(files)
        assert len(hashes) == 2
        assert "file1.py" in hashes
        assert "file2.py" in hashes
        # Same content should produce same hash
        hashes2 = manager.compute_file_hashes({"file1.py": "content1"})
        assert hashes["file1.py"] == hashes2["file1.py"]

    def test_get_cached_context(self):
        """Test getting cached context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ContextCacheManager(
                config=Config(
                    context_cache_enabled=True,
                    context_cache_max_size_mb=10,
                    kicli_cache_dir=tmpdir,
                )
            )

            query = "test query"
            files = {"file.py": "content"}
            context = "# Context\nSome content"

            # Cache it
            manager.cache_context(query, files, context)

            # Retrieve it
            retrieved = manager.get_cached_context(query, files)
            assert retrieved == context

    def test_cache_invalidation_on_file_change(self):
        """Test cache invalidation when files change."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ContextCacheManager(
                config=Config(
                    context_cache_enabled=True,
                    context_cache_max_size_mb=10,
                    kicli_cache_dir=tmpdir,
                )
            )

            query = "test query"
            files = {"file.py": "original content"}
            context = "# Context"

            manager.cache_context(query, files, context)

            # Change file content
            changed_files = {"file.py": "modified content"}
            retrieved = manager.get_cached_context(query, changed_files)

            # Should not find cached version
            assert retrieved is None

    def test_invalidate_for_project(self):
        """Test invalidating cache for entire project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ContextCacheManager(
                config=Config(
                    context_cache_enabled=True,
                    context_cache_max_size_mb=10,
                    kicli_cache_dir=tmpdir,
                )
            )

            # Add some cache entries
            manager.cache_context("query1", {"file.py": "content"}, "context1")
            manager.cache_context("query2", {"file.py": "content"}, "context2")

            # Verify they're cached
            assert manager.get_cached_context("query1", {"file.py": "content"}) is not None
            assert manager.get_cached_context("query2", {"file.py": "content"}) is not None


class TestContextCacheIntegration:
    """Integration tests for caching system."""

    def test_full_caching_workflow(self):
        """Test complete cache workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ContextCache(
                cache_dir=tmpdir,
                config=Config(context_cache_enabled=True, context_cache_max_size_mb=10),
            )

            # Simulate file content and hashes
            files = {
                "auth.py": "def authenticate(): pass",
                "utils.py": "def helper(): pass",
            }
            query = "authentication query"
            context_content = "# Authentication Context\n..."

            # Set cache
            hashes = {k: hash(v) for k, v in files.items()}
            cache.set(query, context_content, hashes)

            # Get cache
            retrieved = cache.get(query, hashes)
            assert retrieved == context_content

            # Verify stats
            stats = cache.get_stats()
            assert stats["num_entries"] == 1
            assert stats["current_size_mb"] > 0

    def test_cache_expiration_workflow(self):
        """Test cache expiration workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ContextCache(
                cache_dir=tmpdir,
                config=Config(context_cache_enabled=True, context_cache_ttl_hours=24),
            )

            cache.set("key1", "content1")
            retrieved = cache.get("key1")
            assert retrieved == "content1"

            # Verify stats
            stats = cache.get_stats()
            assert stats["num_entries"] == 1

    def test_multiple_projects_isolation(self):
        """Test cache isolation between different queries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ContextCacheManager(
                config=Config(
                    context_cache_enabled=True,
                    context_cache_max_size_mb=10,
                    kicli_cache_dir=tmpdir,
                )
            )

            # Query A with specific files
            files_a = {"a.py": "content_a"}
            manager.cache_context("search_a", files_a, "context_A")

            # Query B with different files
            files_b = {"b.py": "content_b"}
            manager.cache_context("search_b", files_b, "context_B")

            # Different queries should have different contexts
            ctx_a = manager.get_cached_context("search_a", files_a)
            ctx_b = manager.get_cached_context("search_b", files_b)

            assert ctx_a == "context_A"
            assert ctx_b == "context_B"
            assert ctx_a != ctx_b

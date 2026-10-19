"""Tests for context deduplication."""

import pytest
import tempfile
from pathlib import Path
from kicli_code_assist.context.deduplicator import (
    ContextDeduplicator,
    DeduplicationStats,
    get_deduplicator,
    reset_deduplicator,
)


class TestDeduplicationStats:
    """Test DeduplicationStats dataclass."""

    def test_stats_initialization(self):
        """Test stats are initialized with zeros."""
        stats = DeduplicationStats()
        assert stats.total_load_attempts == 0
        assert stats.successful_loads == 0
        assert stats.deduplicated_files == 0
        assert stats.dedup_savings_bytes == 0

    def test_record_load_attempt(self):
        """Test recording load attempts."""
        stats = DeduplicationStats()
        stats.record_load_attempt()
        stats.record_load_attempt()
        assert stats.total_load_attempts == 2

    def test_record_successful_load(self):
        """Test recording successful loads."""
        stats = DeduplicationStats()
        stats.record_successful_load(1000)
        assert stats.successful_loads == 1

    def test_record_dedup_hit(self):
        """Test recording dedup hits."""
        stats = DeduplicationStats()
        stats.record_dedup_hit("/path/to/file.py", 1000)
        assert stats.deduplicated_files == 1
        assert stats.dedup_savings_bytes == 1000

    def test_dedup_hit_multiple_times_same_file(self):
        """Test multiple hits on same file."""
        stats = DeduplicationStats()
        stats.record_dedup_hit("/path/to/file.py", 500)
        stats.record_dedup_hit("/path/to/file.py", 500)
        assert stats.deduplicated_files == 2
        assert stats.dedup_savings_bytes == 1000
        assert stats.dedup_hits["/path/to/file.py"] == 2

    def test_get_stats_percentage(self):
        """Test dedup percentage calculation."""
        stats = DeduplicationStats()
        stats.total_load_attempts = 10
        stats.deduplicated_files = 3
        stats_dict = stats.get_stats()
        assert stats_dict["dedup_percentage"] == 30.0


class TestContextDeduplicator:
    """Test ContextDeduplicator class."""

    def test_initialization(self):
        """Test deduplicator initialization."""
        dedup = ContextDeduplicator()
        assert dedup.loaded_files == {}
        assert dedup.file_hashes == {}
        assert isinstance(dedup.stats, DeduplicationStats)

    def test_add_file(self):
        """Test adding a file."""
        dedup = ContextDeduplicator()
        dedup.add_file("/path/to/file.py", 1000)
        assert "/path/to/file.py" in dedup.loaded_files
        assert dedup.loaded_files["/path/to/file.py"] == 1000

    def test_is_loaded_true(self):
        """Test is_loaded returns True for registered file."""
        dedup = ContextDeduplicator()
        dedup.add_file("/path/to/file.py", 1000)
        assert dedup.is_loaded("/path/to/file.py") is True

    def test_is_loaded_false(self):
        """Test is_loaded returns False for unregistered file."""
        dedup = ContextDeduplicator()
        assert dedup.is_loaded("/path/to/file.py") is False

    def test_check_and_register_new_file(self):
        """Test check_and_register with new file."""
        dedup = ContextDeduplicator()
        result = dedup.check_and_register("/path/to/file.py", 1000)
        assert result is True  # Should load
        assert dedup.is_loaded("/path/to/file.py") is True
        assert dedup.stats.successful_loads == 1

    def test_check_and_register_duplicate_file(self):
        """Test check_and_register with duplicate file."""
        dedup = ContextDeduplicator()
        
        # First load
        result1 = dedup.check_and_register("/path/to/file.py", 1000)
        assert result1 is True
        
        # Second load (duplicate)
        result2 = dedup.check_and_register("/path/to/file.py", 1000)
        assert result2 is False  # Should NOT load
        assert dedup.stats.deduplicated_files == 1
        assert dedup.stats.dedup_savings_bytes == 1000

    def test_path_normalization(self):
        """Test that different path representations are treated as same file."""
        dedup = ContextDeduplicator()
        
        # Add with one path format
        dedup.add_file("./relative/path.py", 1000)
        
        # Both should be resolved to absolute paths
        assert dedup.is_loaded("./relative/path.py") is True

    def test_get_loaded_files(self):
        """Test getting list of loaded files."""
        dedup = ContextDeduplicator()
        dedup.add_file("/file1.py", 100)
        dedup.add_file("/file2.py", 200)
        
        files = dedup.get_loaded_files()
        assert len(files) == 2

    def test_clear(self):
        """Test clearing all tracked files."""
        dedup = ContextDeduplicator()
        dedup.add_file("/file.py", 1000)
        dedup.stats.record_load_attempt()
        
        dedup.clear()
        assert dedup.loaded_files == {}
        assert dedup.stats.total_load_attempts == 0

    def test_get_stats(self):
        """Test getting statistics."""
        dedup = ContextDeduplicator()
        dedup.check_and_register("/file1.py", 1000)
        dedup.check_and_register("/file1.py", 1000)
        dedup.check_and_register("/file2.py", 2000)
        
        stats = dedup.get_stats()
        assert stats["total_attempts"] == 3
        assert stats["successful_loads"] == 2
        assert stats["deduplicated_files"] == 1
        assert stats["dedup_percentage"] > 0


class TestGlobalDeduplicator:
    """Test global deduplicator instance."""

    def test_get_deduplicator_singleton(self):
        """Test that get_deduplicator returns same instance."""
        reset_deduplicator()
        dedup1 = get_deduplicator()
        dedup2 = get_deduplicator()
        assert dedup1 is dedup2

    def test_reset_deduplicator(self):
        """Test resetting global deduplicator."""
        dedup1 = get_deduplicator()
        dedup1.add_file("/file.py", 1000)
        
        reset_deduplicator()
        dedup2 = get_deduplicator()
        
        assert dedup1 is not dedup2
        assert len(dedup2.loaded_files) == 0


class TestWithRealFiles:
    """Test deduplication with real files."""

    def test_with_temp_files(self):
        """Test deduplication with actual temporary files."""
        dedup = ContextDeduplicator()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            file1 = Path(tmpdir) / "file1.py"
            file1.write_text("print('hello')")
            
            # Load file twice
            size1 = file1.stat().st_size
            result1 = dedup.check_and_register(str(file1), size1)
            result2 = dedup.check_and_register(str(file1), size1)
            
            assert result1 is True
            assert result2 is False
            assert dedup.stats.deduplicated_files == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""Scan project structure and extract file metadata."""

import logging
from pathlib import Path
from typing import Set, Dict, List
from .project_graph import FileNode

logger = logging.getLogger(__name__)


class StructureScanner:
    """Scans project recursively and extracts file metadata."""

    # Language mappings
    LANGUAGE_EXTENSIONS = {
        "python": {".py"},
        "yaml": {".yaml", ".yml"},
        "json": {".json"},
        "toml": {".toml"},
        "markdown": {".md", ".markdown"},
        "shell": {".sh", ".bash"},
        "ansible": {".yaml", ".yml"},  # Ansible files are YAML
    }

    # Directories to exclude
    DEFAULT_EXCLUDE_DIRS = {
        ".git",
        ".venv",
        "venv",
        ".env",
        "env",
        "__pycache__",
        ".pytest_cache",
        "node_modules",
        ".mypy_cache",
        "dist",
        "build",
        "*.egg-info",
        ".coverage",
        ".tox",
    }

    # Files to exclude
    DEFAULT_EXCLUDE_FILES = {".gitignore", ".gitkeep", ".DS_Store", "*.pyc"}

    def __init__(
        self,
        project_root: Path,
        include_extensions: List[str] = None,
        exclude_dirs: Set[str] = None,
        exclude_files: Set[str] = None,
    ):
        self.project_root = Path(project_root).resolve()
        self.include_extensions = set(include_extensions or [".py", ".yaml", ".json", ".toml"])
        self.exclude_dirs = exclude_dirs or self.DEFAULT_EXCLUDE_DIRS
        self.exclude_files = exclude_files or self.DEFAULT_EXCLUDE_FILES

    def scan(self) -> List[FileNode]:
        """Scan project and return list of FileNodes."""
        files = []

        try:
            for file_path in self._walk_files():
                try:
                    file_node = self._extract_metadata(file_path)
                    if file_node:
                        files.append(file_node)
                except Exception as e:
                    logger.warning(f"Failed to extract metadata for {file_path}: {e}")
        except Exception as e:
            logger.error(f"Failed to scan project {self.project_root}: {e}")

        return files

    def _walk_files(self):
        """Walk project recursively, excluding directories."""
        for path in self.project_root.rglob("*"):
            if path.is_file():
                # Check if should exclude
                if self._should_exclude(path):
                    continue
                yield path

    def _should_exclude(self, file_path: Path) -> bool:
        """Check if file should be excluded."""
        # Check extension
        if file_path.suffix not in self.include_extensions:
            return True

        # Check if any parent directory is excluded
        for part in file_path.relative_to(self.project_root).parts[:-1]:
            if part in self.exclude_dirs:
                return True

        # Check filename
        if file_path.name in self.exclude_files:
            return True

        return False

    def _extract_metadata(self, file_path: Path) -> FileNode:
        """Extract metadata for a single file."""
        rel_path = file_path.relative_to(self.project_root)
        language = self._detect_language(file_path)

        # Read file content
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            logger.warning(f"Failed to read {file_path}: {e}")
            content = ""

        lines = len(content.split("\n"))
        size = file_path.stat().st_size if file_path.exists() else 0

        # Check for tests
        has_tests = "test_" in file_path.name or "_test.py" in file_path.name

        return FileNode(
            path=file_path,
            rel_path=str(rel_path),
            language=language,
            size_bytes=size,
            lines=lines,
            has_tests=has_tests,
        )

    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension."""
        ext = file_path.suffix.lower()

        for language, extensions in self.LANGUAGE_EXTENSIONS.items():
            if ext in extensions:
                # Special handling for Ansible
                if language == "ansible" and "roles/" in str(file_path):
                    return "ansible"
                return language if language != "ansible" else "yaml"

        return "unknown"

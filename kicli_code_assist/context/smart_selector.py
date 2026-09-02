"""Intelligent file selection based on AST parsing and dependency analysis."""

import ast
import json
import re
from pathlib import Path
from typing import Optional, Dict, List, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

from ki_core import Config


@dataclass
class FileMetadata:
    """Metadata about a file for smart selection."""
    path: Path
    language: str  # 'python', 'javascript', 'go'
    imports: Set[str] = field(default_factory=set)
    exports: Set[str] = field(default_factory=set)
    dependencies: Set[str] = field(default_factory=set)  # Other files it imports
    dependents: Set[str] = field(default_factory=set)  # Files that import this
    size_kb: float = 0.0
    relevance_score: float = 0.0


class DependencyGraph:
    """Build and analyze file dependency graph."""

    def __init__(self):
        """Initialize the dependency graph."""
        self.files: Dict[str, FileMetadata] = {}
        self.import_to_files: Dict[str, Set[str]] = defaultdict(set)

    def add_file(self, file_meta: FileMetadata) -> None:
        """Add file metadata to graph."""
        file_key = str(file_meta.path)
        self.files[file_key] = file_meta

    def resolve_imports(self, root: Path) -> None:
        """Resolve import statements to file paths."""
        for file_key, file_meta in self.files.items():
            for import_name in file_meta.imports:
                # Convert import name to potential file paths
                potential_paths = self._import_to_paths(import_name, root, file_meta.language)
                for potential in potential_paths:
                    for other_key in self.files.keys():
                        if str(Path(other_key)).endswith(potential):
                            file_meta.dependencies.add(other_key)
                            self.files[other_key].dependents.add(file_key)

    def _import_to_paths(self, import_name: str, root: Path, language: str) -> List[str]:
        """Convert import name to potential file paths."""
        if language == "python":
            # foo.bar.baz -> foo/bar/baz.py or foo/bar/baz/__init__.py
            parts = import_name.split(".")
            paths = [
                "/".join(parts) + ".py",
                "/".join(parts) + "/__init__.py",
            ]
            return paths
        elif language == "javascript":
            # foo/bar/baz -> foo/bar/baz.js or foo/bar/baz/index.js
            parts = import_name.replace(".", "/").split("/")
            paths = [
                "/".join(parts) + ".js",
                "/".join(parts) + "/index.js",
                "/".join(parts) + ".jsx",
                "/".join(parts) + "/index.jsx",
            ]
            return paths
        elif language == "go":
            # github.com/org/pkg -> go files in that directory
            parts = import_name.split("/")
            return ["/".join(parts)]
        return []

    def get_related_files(self, file_key: str, depth: int = 2) -> Set[str]:
        """Get all files related to a given file (imports + dependents)."""
        if file_key not in self.files:
            return set()

        related = {file_key}
        current_level = {file_key}

        for _ in range(depth):
            next_level = set()
            for current in current_level:
                if current in self.files:
                    next_level.update(self.files[current].dependencies)
                    next_level.update(self.files[current].dependents)
            related.update(next_level)
            current_level = next_level

        return related

    def get_entry_points(self) -> List[str]:
        """Identify entry point files (main, index, etc)."""
        entry_patterns = ["main.py", "app.py", "index.js", "main.go", "__main__.py"]
        entry_points = []
        for file_key in self.files.keys():
            filename = Path(file_key).name
            if filename in entry_patterns:
                entry_points.append(file_key)
        return entry_points


class ASTAnalyzer:
    """Analyze files using AST parsing."""

    @staticmethod
    def analyze_python(content: str) -> Tuple[Set[str], Set[str]]:
        """Extract imports and definitions from Python code."""
        imports = set()
        exports = set()

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return imports, exports

        for node in ast.walk(tree):
            # Extract imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)

            # Extract function and class definitions (exports)
            if isinstance(node, ast.FunctionDef):
                if not node.name.startswith("_"):
                    exports.add(node.name)
            elif isinstance(node, ast.ClassDef):
                if not node.name.startswith("_"):
                    exports.add(node.name)

        return imports, exports

    @staticmethod
    def analyze_javascript(content: str) -> Tuple[Set[str], Set[str]]:
        """Extract imports and exports from JavaScript code."""
        imports = set()
        exports = set()

        # Match various import patterns
        import_patterns = [
            r"import\s+(?:{[^}]+}|[^\s]+)\s+from\s+['\"]([^'\"]+)['\"]",
            r"require\s*\(['\"]([^'\"]+)['\"]\)",
            r"import\s+['\"]([^'\"]+)['\"]",
        ]

        for pattern in import_patterns:
            for match in re.finditer(pattern, content):
                imports.add(match.group(1))

        # Match export patterns
        export_patterns = [
            r"export\s+(?:function|const|class|let|var)\s+(\w+)",
            r"module\.exports\s*=",
        ]

        for pattern in export_patterns:
            for match in re.finditer(pattern, content):
                if match.lastindex:
                    exports.add(match.group(1))

        return imports, exports

    @staticmethod
    def analyze_go(content: str) -> Tuple[Set[str], Set[str]]:
        """Extract imports and exports from Go code."""
        imports = set()
        exports = set()

        # Extract imports
        import_pattern = r'import\s*\(\s*(.*?)\s*\)|import\s+"([^"]+)"'
        for match in re.finditer(import_pattern, content, re.DOTALL):
            if match.group(1):
                for line in match.group(1).split("\n"):
                    line = line.strip().strip('"')
                    if line:
                        imports.add(line)
            elif match.group(2):
                imports.add(match.group(2))

        # Extract exported functions/types (start with capital letter)
        func_pattern = r"func\s+\(.*?\)\s+(\w+)\s*\(|func\s+(\w+)\s*\(|type\s+(\w+)\s+"
        for match in re.finditer(func_pattern, content):
            name = match.group(1) or match.group(2) or match.group(3)
            if name and name[0].isupper():
                exports.add(name)

        return imports, exports

    @classmethod
    def analyze(cls, content: str, language: str) -> Tuple[Set[str], Set[str]]:
        """Analyze file based on language."""
        if language == "python":
            return cls.analyze_python(content)
        elif language == "javascript":
            return cls.analyze_javascript(content)
        elif language == "go":
            return cls.analyze_go(content)
        return set(), set()


class SmartFileSelector:
    """Intelligently select relevant files for LLM context."""

    def __init__(self, project_root: str = ".", config: Optional[Config] = None):
        """Initialize smart file selector.

        Args:
            project_root: Root directory of project
            config: Configuration object (uses defaults if not provided)
        """
        self.root = Path(project_root).resolve()
        self.config = config or Config.from_env()
        self.max_files = self.config.context_max_files
        self.max_size_mb = self.config.context_max_size_mb
        self.relevance_threshold = max(self.config.context_relevance_threshold, 0.1)  # Min 0.1
        self.ignore_patterns = self.config.context_ignore_patterns.split(",")

        self.graph = DependencyGraph()
        self.analyzer = ASTAnalyzer()

    def scan_project(self) -> Dict[str, FileMetadata]:
        """Scan project and build dependency graph."""
        files_scanned = 0
        for path in self.root.rglob("*"):
            if not path.is_file():
                continue

            # Skip ignored patterns
            if self._should_ignore(path):
                continue

            language = self._detect_language(path)
            if not language:
                continue

            try:
                size_kb = path.stat().st_size / 1024
                if size_kb > 1000:  # Skip files > 1MB
                    continue

                content = path.read_text(encoding="utf-8", errors="ignore")
                imports, exports = self.analyzer.analyze(content, language)

                file_meta = FileMetadata(
                    path=path,
                    language=language,
                    imports=imports,
                    exports=exports,
                    size_kb=size_kb,
                )
                self.graph.add_file(file_meta)
                files_scanned += 1

            except (OSError, PermissionError):
                continue

        # Resolve dependencies
        self.graph.resolve_imports(self.root)
        return self.graph.files

    def _should_ignore(self, path: Path) -> bool:
        """Check if file should be ignored."""
        path_str = str(path)
        for pattern in self.ignore_patterns:
            pattern = pattern.strip()
            if pattern in path_str or path_str.endswith(pattern):
                return True
        return False

    def _detect_language(self, path: Path) -> Optional[str]:
        """Detect file language."""
        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "javascript",
            ".tsx": "javascript",
            ".go": "go",
        }
        return extension_map.get(path.suffix)

    def select_files_for_query(self, query: str) -> List[Tuple[str, float]]:
        """Select best files for a user query.

        Args:
            query: User query/question

        Returns:
            List of (file_path, relevance_score) tuples, sorted by relevance
        """
        if not self.graph.files:
            self.scan_project()

        # Score each file
        scored_files = []
        for file_key, file_meta in self.graph.files.items():
            score = self._score_file(file_meta, query)
            if score >= self.relevance_threshold:
                scored_files.append((file_key, score))

        # Sort by relevance
        scored_files.sort(key=lambda x: x[1], reverse=True)

        # Apply size constraint
        selected = []
        total_size = 0
        for file_key, score in scored_files:
            if len(selected) >= self.max_files:
                break
            if total_size + self.graph.files[file_key].size_kb > self.max_size_mb * 1024:
                break
            selected.append((file_key, score))
            total_size += self.graph.files[file_key].size_kb

        return selected

    def _score_file(self, file_meta: FileMetadata, query: str) -> float:
        """Score a file's relevance to a query.

        Args:
            file_meta: File metadata
            query: Query string

        Returns:
            Relevance score (0-1)
        """
        score = 0.0
        query_lower = query.lower()
        filename_lower = file_meta.path.name.lower()
        filename_stem = file_meta.path.stem.lower()  # Without extension

        # 1. Extract keywords from query and filename
        query_words = query_lower.split()
        filename_parts = filename_stem.split("_")  # Split by underscore

        # 2. Bidirectional keyword matching
        for word in query_words:
            word = word.lower().strip("()[]{}:")
            if len(word) > 1:
                # Check if query word is in filename (e.g., "auth" in "auth.py")
                if word in filename_stem:
                    score += 0.25
                    break
                # Check if filename part is in query word (e.g., "auth" in "authentication")
                for part in filename_parts:
                    if len(part) > 2 and part in word:
                        score += 0.25
                        break

        # 3. Exact query in filename
        if query_lower in filename_lower:
            score += 0.3

        # 4. Query keywords in imports/exports
        for keyword in query_words:
            keyword = keyword.lower().strip("()[]{}:")
            if len(keyword) > 2:
                for export in file_meta.exports:
                    if keyword.lower() in export.lower():
                        score += 0.25
                        break
                for imp in file_meta.imports:
                    if keyword.lower() in imp.lower():
                        score += 0.15
                        break

        # 5. Priority files (entry points, config, docs)
        if file_meta.path.name in ["main.py", "app.py", "index.js", "main.go"]:
            score += 0.2
        if file_meta.path.name in ["README.md", "setup.py", "pyproject.toml"]:
            score += 0.15

        # 6. File size preference (prefer smaller files, but not too small)
        if 5 < file_meta.size_kb < 100:
            score += 0.1
        elif file_meta.size_kb > 500:
            score -= 0.2

        return min(score, 1.0)

    def get_context_for_query(self, query: str) -> str:
        """Get formatted context string for LLM based on query.

        Args:
            query: User query

        Returns:
            Formatted context string
        """
        # Scan project if not already done
        if not self.graph.files:
            self.scan_project()

        selected = self.select_files_for_query(query)

        if not selected:
            return f"No relevant files found for query: {query}"

        lines = [f"# Context for Query: {query}\n"]
        lines.append(f"Selected {len(selected)} files based on relevance:\n")

        for file_key, score in selected:
            file_meta = self.graph.files[file_key]
            relative_path = file_meta.path.relative_to(self.root)
            lines.append(f"\n## {relative_path} (relevance: {score:.1%})")
            lines.append(f"Language: {file_meta.language} | Size: {file_meta.size_kb:.1f}KB")

            if file_meta.imports:
                lines.append(f"Imports: {', '.join(list(file_meta.imports)[:5])}")
            if file_meta.exports:
                lines.append(f"Exports: {', '.join(list(file_meta.exports)[:5])}")

            # Add file preview
            try:
                content = file_meta.path.read_text(encoding="utf-8", errors="ignore")
                preview = "\n".join(content.split("\n")[:20])
                lines.append(f"\n```{file_meta.language}")
                lines.append(preview)
                lines.append("```")
            except (OSError, PermissionError):
                pass

        return "\n".join(lines)

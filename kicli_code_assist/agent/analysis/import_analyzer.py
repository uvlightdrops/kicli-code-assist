"""Parse imports and build dependency graph for Python files."""

import ast
import logging
from pathlib import Path
from typing import Set, Dict, List, Optional
from .project_graph import FileNode, ProjectGraph

logger = logging.getLogger(__name__)


class ImportAnalyzer:
    """Analyzes Python imports and builds dependency graph."""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()

    def build_graph(self, files: List[FileNode]) -> ProjectGraph:
        """Build complete dependency graph from list of files."""
        graph = ProjectGraph(self.project_root)

        # Add all files to graph
        for file in files:
            if file.language == "python":
                graph.add_file(file)

        # Extract imports for each file
        for file in files:
            if file.language != "python":
                continue

            imports = self._extract_imports(file.path)
            file.imports = imports

            # Map module names to file paths
            for import_name in imports:
                target_file = self._resolve_import(import_name, file)
                if target_file:
                    graph.add_dependency(file.rel_path, target_file)
                else:
                    # If not found in project, log but don't fail
                    logger.debug(f"Could not resolve {import_name} in {file.rel_path}")

        return graph

    def _extract_imports(self, file_path: Path) -> Set[str]:
        """Extract all imports from a Python file."""
        imports = set()

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(content)
        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {e}")
            return imports

        # Walk AST for import statements
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # "import package.utils" -> add "package.utils"
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    # "from package.utils import helper" -> add "package.utils"
                    imports.add(node.module)
                # "from . import utils" or "from .. import something" are relative imports
                # Skip for now (TODO: handle relative imports)

        return imports

    def _resolve_import(self, import_name: str, from_file: FileNode) -> Optional[str]:
        """
        Try to resolve import name to actual file in project.
        Returns relative path or None if not found in project.
        """
        # Try different resolution strategies in order
        strategies = [
            self._resolve_as_module_file,  # Try "package.utils" -> "package/utils.py"
            self._resolve_as_package,      # Try "package" -> "package/__init__.py"
        ]

        for strategy in strategies:
            result = strategy(import_name)
            if result:
                return result

        return None

    def _resolve_as_module_file(self, import_name: str) -> Optional[str]:
        """Try to resolve import as a Python module file (e.g., 'package.utils' -> 'package/utils.py')."""
        # Convert dot notation to path
        module_file = self.project_root / (import_name.replace(".", "/") + ".py")

        if module_file.exists() and module_file.is_relative_to(self.project_root):
            return str(module_file.relative_to(self.project_root))

        return None

    def _resolve_as_package(self, import_name: str) -> Optional[str]:
        """Try to resolve import as a package __init__.py (e.g., 'package' -> 'package/__init__.py')."""
        package_dir = self.project_root / import_name.replace(".", "/")
        init_file = package_dir / "__init__.py"

        if init_file.exists() and init_file.is_relative_to(self.project_root):
            return str(init_file.relative_to(self.project_root))

        return None

    def extract_exported_symbols(self, file_path: Path) -> Set[str]:
        """Extract function and class definitions from a file."""
        symbols = set()

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(content)
        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {e}")
            return symbols

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                symbols.add(node.name)

        return symbols

    def detect_circular_dependencies(self, graph: ProjectGraph) -> List[List[str]]:
        """Detect circular dependencies in the graph."""
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node: str, path: List[str]) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.dependencies.get(node, set()):
                if neighbor not in visited:
                    dfs(neighbor, path.copy())
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)

            rec_stack.remove(node)

        for file in graph.files.keys():
            if file not in visited:
                dfs(file, [])

        return cycles

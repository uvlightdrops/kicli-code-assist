"""Collect code metrics for files."""

import ast
import logging
from pathlib import Path
from typing import List, Dict
from .project_graph import FileNode

logger = logging.getLogger(__name__)


class CodemetricsCollector:
    """Collects metrics like LOC, complexity, and code smells."""

    def collect_metrics(self, files: List[FileNode]) -> None:
        """Collect and store metrics for each file."""
        for file in files:
            if file.language != "python":
                continue

            try:
                metrics = self._analyze_file(file.path)
                file.cyclomatic_complexity = metrics["cyclomatic_complexity"]
                file.exported_symbols = metrics["exported_symbols"]
            except Exception as e:
                logger.warning(f"Failed to collect metrics for {file.path}: {e}")

    def _analyze_file(self, file_path: Path) -> Dict:
        """Analyze a single file for metrics."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(content)
        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {e}")
            return {"cyclomatic_complexity": 1, "exported_symbols": set()}

        # Count cyclomatic complexity
        complexity = self._calculate_complexity(tree)

        # Extract exported symbols
        exported = self._extract_exported_symbols(tree)

        return {
            "cyclomatic_complexity": complexity,
            "exported_symbols": exported,
        }

    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity for an AST."""
        complexity = 1

        for node in ast.walk(tree):
            # Count decision points
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            # Boolean operators count as decisions
            elif isinstance(node, ast.BoolOp):
                complexity += 1
            # Try statements add complexity
            elif isinstance(node, ast.Try):
                complexity += len(node.handlers)

        return complexity

    def _extract_exported_symbols(self, tree: ast.AST) -> set:
        """Extract function and class definitions."""
        symbols = set()

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Only top-level functions (not nested)
                if not self._is_nested(node, tree):
                    symbols.add(node.name)
            elif isinstance(node, ast.ClassDef):
                # Only top-level classes
                if not self._is_nested(node, tree):
                    symbols.add(node.name)

        return symbols

    def _is_nested(self, node: ast.AST, root: ast.AST) -> bool:
        """Check if node is nested inside another function/class."""
        for parent in ast.walk(root):
            if parent is node:
                continue
            if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                # Check if node is in parent's body
                if any(child is node for child in ast.walk(parent)):
                    return True
        return False

    def get_stats_by_file(self, files: List[FileNode]) -> List[Dict]:
        """Get metrics for each file, sorted by complexity."""
        stats = []
        for file in files:
            if file.language == "python":
                stats.append({
                    "file": file.rel_path,
                    "lines": file.lines,
                    "complexity": file.cyclomatic_complexity,
                    "symbols": len(file.exported_symbols),
                })

        return sorted(stats, key=lambda x: x["complexity"], reverse=True)

    def get_complex_files(self, files: List[FileNode], threshold: int = 10) -> List[Dict]:
        """Get files with complexity above threshold."""
        complex_files = [
            f for f in files
            if f.language == "python" and f.cyclomatic_complexity > threshold
        ]
        return self.get_stats_by_file(complex_files)

    def get_hotspots(self, files: List[FileNode], top_n: int = 10) -> List[Dict]:
        """Get top N most complex files."""
        complex_files = sorted(
            [f for f in files if f.language == "python"],
            key=lambda x: x.cyclomatic_complexity,
            reverse=True,
        )[:top_n]
        return self.get_stats_by_file(complex_files)

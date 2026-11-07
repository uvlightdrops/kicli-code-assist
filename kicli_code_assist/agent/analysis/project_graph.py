"""Project graph representation and analysis."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Set, List, Optional, Tuple
from enum import Enum


class ImpactLevel(Enum):
    """Impact severity levels."""
    CRITICAL = "critical"  # Many dependents, core module
    HIGH = "high"  # Several dependents
    MEDIUM = "medium"  # Few dependents
    LOW = "low"  # No dependents


@dataclass
class FileNode:
    """Represents a single file in project."""
    path: Path
    rel_path: str  # relative to project root
    language: str
    size_bytes: int = 0
    lines: int = 0
    imports: Set[str] = field(default_factory=set)  # module names/paths
    exported_symbols: Set[str] = field(default_factory=set)  # functions, classes
    cyclomatic_complexity: int = 1
    has_tests: bool = False


@dataclass
class ImpactZone:
    """Files affected by a change to a target file."""
    primary_file: str
    direct_dependents: Set[str] = field(default_factory=set)
    indirect_dependents: Set[str] = field(default_factory=set)
    all_affected: Set[str] = field(default_factory=set)
    cascade_depth: int = 0
    impact_level: ImpactLevel = ImpactLevel.LOW
    circular_deps: List[List[str]] = field(default_factory=list)


class ProjectGraph:
    """Full project dependency graph and analysis."""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        self.files: Dict[str, FileNode] = {}  # rel_path -> FileNode
        self.dependencies: Dict[str, Set[str]] = {}  # file -> files it imports
        self.dependents: Dict[str, Set[str]] = {}  # file -> files importing it
        self._circular_deps: List[List[str]] = []

    def add_file(self, file_node: FileNode) -> None:
        """Add a file to the graph."""
        self.files[file_node.rel_path] = file_node
        if file_node.rel_path not in self.dependencies:
            self.dependencies[file_node.rel_path] = set()
        if file_node.rel_path not in self.dependents:
            self.dependents[file_node.rel_path] = set()

    def add_dependency(self, from_file: str, to_file: str) -> None:
        """Record that from_file imports to_file."""
        if from_file not in self.dependencies:
            self.dependencies[from_file] = set()
        if to_file not in self.dependents:
            self.dependents[to_file] = set()

        self.dependencies[from_file].add(to_file)
        self.dependents[to_file].add(from_file)

    def get_transitive_dependents(self, file: str, max_depth: int = 10) -> Set[str]:
        """Get all files transitively depending on this file."""
        visited = set()
        queue = [file]
        depth = 0

        while queue and depth < max_depth:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)

            for dependent in self.dependents.get(current, set()):
                if dependent not in visited:
                    queue.append(dependent)
            depth += 1

        return visited - {file}

    def get_impact_zone(self, file: str) -> ImpactZone:
        """Get complete impact analysis for a file change."""
        zone = ImpactZone(primary_file=file)

        # Direct dependents
        zone.direct_dependents = self.dependents.get(file, set()).copy()

        # Transitive dependents
        zone.indirect_dependents = self.get_transitive_dependents(file) - zone.direct_dependents

        # All affected
        zone.all_affected = zone.direct_dependents | zone.indirect_dependents

        # Cascade depth
        if zone.direct_dependents:
            zone.cascade_depth = self._calculate_cascade_depth(file)

        # Impact level
        affected_count = len(zone.all_affected)
        if affected_count == 0:
            zone.impact_level = ImpactLevel.LOW
        elif affected_count <= 3:
            zone.impact_level = ImpactLevel.MEDIUM
        elif affected_count <= 10:
            zone.impact_level = ImpactLevel.HIGH
        else:
            zone.impact_level = ImpactLevel.CRITICAL

        # Check for circular dependencies
        zone.circular_deps = self._find_circular_deps(file)

        return zone

    def _calculate_cascade_depth(self, file: str, visited: Optional[Set[str]] = None, depth: int = 0) -> int:
        """Calculate maximum cascade depth."""
        if visited is None:
            visited = set()

        if file in visited or depth > 20:
            return depth

        visited.add(file)
        max_depth = depth

        for dependent in self.dependents.get(file, set()):
            d = self._calculate_cascade_depth(dependent, visited.copy(), depth + 1)
            max_depth = max(max_depth, d)

        return max_depth

    def _find_circular_deps(self, file: str) -> List[List[str]]:
        """Find circular dependencies involving this file."""
        cycles = []

        def dfs(node: str, path: List[str], visited: Set[str]) -> None:
            if node in visited:
                if node == file and len(path) > 1:
                    cycles.append(path + [node])
                return

            visited.add(node)
            for neighbor in self.dependencies.get(node, set()):
                dfs(neighbor, path + [node], visited.copy())

        dfs(file, [], set())
        return cycles

    def get_stats(self) -> Dict:
        """Get project-wide statistics."""
        return {
            "total_files": len(self.files),
            "total_lines": sum(f.lines for f in self.files.values()),
            "languages": self._group_by_language(),
            "avg_complexity": self._avg_complexity(),
            "files_with_high_impact": self._high_impact_files(),
            "circular_dependencies": len(self._circular_deps),
        }

    def _group_by_language(self) -> Dict[str, int]:
        """Count files by language."""
        langs = {}
        for file in self.files.values():
            langs[file.language] = langs.get(file.language, 0) + 1
        return langs

    def _avg_complexity(self) -> float:
        """Average cyclomatic complexity."""
        if not self.files:
            return 0
        total = sum(f.cyclomatic_complexity for f in self.files.values())
        return total / len(self.files)

    def _high_impact_files(self) -> List[Tuple[str, int]]:
        """Files with most dependents."""
        impact = [(f, len(self.dependents.get(f, set()))) for f in self.files.keys()]
        return sorted(impact, key=lambda x: x[1], reverse=True)[:10]

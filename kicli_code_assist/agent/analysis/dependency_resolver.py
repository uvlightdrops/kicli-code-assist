"""Minimal dependency resolver."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Set, List, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class DependencyGraph:
    """Simple dependency graph representation."""
    nodes: Dict[Path, Set[Path]] = field(default_factory=dict)  # file -> direct dependencies


class DependencyResolver:
    """Minimal dependency resolver for quick iteration."""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()

    def get_file_dependents(self, file_path: Path) -> Set[Path]:
        """Quick: what files import this file?"""
        file_path = file_path.resolve()
        py_files = list(self.project_root.glob("**/*.py"))
        dependents = set()
        
        for py_file in py_files:
            try:
                content = py_file.read_text()
                # Simple heuristic: grep for filename
                module_name = file_path.stem
                if f"import {module_name}" in content or f"from {module_name}" in content:
                    dependents.add(py_file)
            except Exception:
                pass
        
        return dependents

    def get_impact(self, changed_file: Path) -> Dict[str, int]:
        """Quick impact analysis."""
        dependents = self.get_file_dependents(changed_file)
        return {"affected_files": len(dependents), "files": [str(f) for f in dependents]}

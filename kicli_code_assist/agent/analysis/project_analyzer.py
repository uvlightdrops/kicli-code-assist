"""Minimal project analyzer."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class ProjectMetadata:
    """Minimal project metadata."""
    root: Path
    name: str
    frameworks: List[str] = field(default_factory=list)
    entry_points: List[str] = field(default_factory=list)


class ProjectAnalysisService:
    """Minimal project analyzer for quick iteration."""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()

    def analyze(self) -> ProjectMetadata:
        """Quick project analysis."""
        metadata = ProjectMetadata(
            root=self.project_root,
            name=self.project_root.name,
        )

        # Quick framework detection
        content_str = " ".join([f.name for f in self.project_root.glob("**/*.py")])
        for fw in ["flask", "django", "fastapi"]:
            if fw in content_str.lower():
                metadata.frameworks.append(fw)

        # Find entry points
        for entry in ["main.py", "app.py", "run.py"]:
            if (self.project_root / entry).exists():
                metadata.entry_points.append(entry)

        return metadata

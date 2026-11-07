"""Full project analyzer - orchestrates scanning, import analysis, and metrics."""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from .project_graph import FileNode, ProjectGraph, ImpactZone
from .structure_scanner import StructureScanner
from .import_analyzer import ImportAnalyzer
from .code_metrics_collector import CodemetricsCollector

logger = logging.getLogger(__name__)


@dataclass
class ProjectMetadata:
    """Complete project metadata and analysis."""
    root: Path
    name: str
    frameworks: List[str] = field(default_factory=list)
    entry_points: List[str] = field(default_factory=list)


class ProjectAnalysisService:
    """Full project analyzer combining multiple analysis strategies."""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        self.graph: Optional[ProjectGraph] = None
        self.files: List[FileNode] = []

    def analyze(self) -> ProjectMetadata:
        """Complete project analysis."""
        metadata = ProjectMetadata(
            root=self.project_root,
            name=self.project_root.name,
        )

        # Framework detection
        content_str = " ".join([f.name for f in self.project_root.glob("**/*.py")])
        for fw in ["flask", "django", "fastapi"]:
            if fw in content_str.lower():
                metadata.frameworks.append(fw)

        # Entry points
        for entry in ["main.py", "app.py", "run.py"]:
            if (self.project_root / entry).exists():
                metadata.entry_points.append(entry)

        return metadata

    def analyze_full(self) -> ProjectGraph:
        """Perform complete project analysis (structure + imports + metrics)."""
        logger.info(f"Starting full project analysis for {self.project_root}")

        # Step 1: Scan structure
        scanner = StructureScanner(self.project_root)
        self.files = scanner.scan()
        logger.info(f"Found {len(self.files)} files")

        # Step 2: Analyze imports and build graph
        import_analyzer = ImportAnalyzer(self.project_root)
        self.graph = import_analyzer.build_graph(self.files)
        logger.info(f"Built dependency graph with {len(self.graph.files)} files")

        # Step 3: Collect metrics
        metrics = CodemetricsCollector()
        metrics.collect_metrics(self.files)
        logger.info("Collected code metrics")

        logger.info(f"Project analysis complete: {self.graph.get_stats()}")
        return self.graph

    def get_file_impact(self, rel_path: str) -> Optional[ImpactZone]:
        """Get impact analysis for a specific file."""
        if not self.graph:
            return None
        if rel_path not in self.graph.files:
            logger.warning(f"File {rel_path} not found in project")
            return None
        return self.graph.get_impact_zone(rel_path)

    def get_project_stats(self) -> Dict:
        """Get project-wide statistics."""
        if not self.graph:
            return {}
        return self.graph.get_stats()

    def get_high_impact_files(self) -> List[str]:
        """Get files that are imported by many other files."""
        if not self.graph:
            return []
        return [f for f, _ in self.graph._high_impact_files()]

    def get_circular_dependencies(self) -> List[List[str]]:
        """Get all circular dependencies in project."""
        if not self.graph:
            return []
        return self.graph._circular_deps

    def get_complex_files(self) -> List[str]:
        """Get most complex files."""
        if not self.files:
            return []
        complex = CodemetricsCollector().get_hotspots(self.files, top_n=10)
        return [f["file"] for f in complex]

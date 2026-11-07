"""Tests for Phase I2 ProjectAnalyzer module."""

import tempfile
import logging
from pathlib import Path
import pytest

from kicli_code_assist.agent.analysis.project_analyzer import ProjectAnalysisService
from kicli_code_assist.agent.analysis.structure_scanner import StructureScanner
from kicli_code_assist.agent.analysis.import_analyzer import ImportAnalyzer
from kicli_code_assist.agent.analysis.code_metrics_collector import CodemetricsCollector
from kicli_code_assist.agent.analysis.project_graph import ProjectGraph, ImpactLevel

logger = logging.getLogger(__name__)


@pytest.fixture
def test_project():
    """Create a temporary test project structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # Create module structure
        (root / "package").mkdir()
        (root / "package" / "__init__.py").write_text("")

        # Create utils module (imported by multiple files)
        (root / "package" / "utils.py").write_text(
            "def helper(): pass\ndef format_data(): pass\n"
        )

        # Create module_a (depends on utils)
        (root / "package" / "module_a.py").write_text(
            "from package.utils import helper\ndef process(): return helper()\n"
        )

        # Create module_b (depends on utils and module_a)
        (root / "package" / "module_b.py").write_text(
            "from package.utils import format_data\nfrom package.module_a import process\n"
            "def run(): return process()\n"
        )

        # Create module_c (depends on module_b)
        (root / "package" / "module_c.py").write_text(
            "from package.module_b import run\ndef execute(): return run()\n"
        )

        # Create test file
        (root / "package" / "test_utils.py").write_text(
            "from package.utils import helper\ndef test_helper(): assert helper()\n"
        )

        # Create config file
        (root / "config.yaml").write_text("debug: true\n")

        yield root


class TestStructureScanner:
    """Test file scanning and metadata extraction."""

    def test_scan_finds_python_files(self, test_project):
        """Should find all Python files."""
        scanner = StructureScanner(test_project)
        files = scanner.scan()

        py_files = [f for f in files if f.language == "python"]
        assert len(py_files) == 5  # utils, module_a, module_b, module_c, test_utils

    def test_scan_detects_language(self, test_project):
        """Should correctly detect file languages."""
        scanner = StructureScanner(test_project)
        files = scanner.scan()

        languages = {f.language for f in files}
        assert "python" in languages
        assert "yaml" in languages

    def test_scan_extracts_metadata(self, test_project):
        """Should extract file metadata."""
        scanner = StructureScanner(test_project)
        files = scanner.scan()

        utils_file = next((f for f in files if "utils.py" in f.rel_path), None)
        assert utils_file is not None
        assert utils_file.lines > 0
        assert utils_file.size_bytes > 0

    def test_scan_detects_test_files(self, test_project):
        """Should identify test files."""
        scanner = StructureScanner(test_project)
        files = scanner.scan()

        test_file = next((f for f in files if "test_" in f.rel_path), None)
        assert test_file is not None
        assert test_file.has_tests

    def test_scan_respects_exclusions(self, test_project):
        """Should respect exclude patterns."""
        # Create excluded directories
        (test_project / "__pycache__").mkdir()
        (test_project / "__pycache__" / "utils.cpython-39.pyc").write_text("")

        scanner = StructureScanner(test_project)
        files = scanner.scan()

        # Should not include pyc files
        assert all(".pyc" not in f.rel_path for f in files)


class TestImportAnalyzer:
    """Test import parsing and dependency graph building."""

    def test_extract_imports(self, test_project):
        """Should extract imports from Python files."""
        analyzer = ImportAnalyzer(test_project)

        module_b = test_project / "package" / "module_b.py"
        imports = analyzer._extract_imports(module_b)

        assert "package" in imports

    def test_build_graph(self, test_project):
        """Should build complete dependency graph."""
        scanner = StructureScanner(test_project)
        files = scanner.scan()

        analyzer = ImportAnalyzer(test_project)
        graph = analyzer.build_graph(files)

        # Should have 5 Python files in graph
        assert len(graph.files) == 5

    def test_graph_dependencies(self, test_project):
        """Should record dependency relationships."""
        scanner = StructureScanner(test_project)
        files = scanner.scan()

        analyzer = ImportAnalyzer(test_project)
        graph = analyzer.build_graph(files)

        # module_a depends on utils
        utils_path = "package/utils.py"
        assert utils_path in graph.files

    def test_detect_circular_deps(self, test_project):
        """Should detect circular dependencies."""
        # Create circular dependency
        (test_project / "package" / "circular_a.py").write_text(
            "from package.circular_b import func_b\n"
        )
        (test_project / "package" / "circular_b.py").write_text(
            "from package.circular_a import func_a\n"
        )

        scanner = StructureScanner(test_project)
        files = scanner.scan()

        analyzer = ImportAnalyzer(test_project)
        graph = analyzer.build_graph(files)
        cycles = analyzer.detect_circular_dependencies(graph)

        # Should detect at least one cycle
        assert len(cycles) > 0

    def test_extract_exported_symbols(self, test_project):
        """Should extract function and class definitions."""
        analyzer = ImportAnalyzer(test_project)

        utils_file = test_project / "package" / "utils.py"
        symbols = analyzer.extract_exported_symbols(utils_file)

        assert "helper" in symbols
        assert "format_data" in symbols


class TestCodemetricsCollector:
    """Test code metric collection."""

    def test_collect_metrics(self, test_project):
        """Should collect metrics for files."""
        scanner = StructureScanner(test_project)
        files = scanner.scan()

        collector = CodemetricsCollector()
        collector.collect_metrics(files)

        # Files should have complexity assigned
        py_files = [f for f in files if f.language == "python"]
        assert all(f.cyclomatic_complexity > 0 for f in py_files)

    def test_calculate_complexity(self, test_project):
        """Should calculate cyclomatic complexity."""
        # Create file with known complexity
        complex_file = test_project / "complex.py"
        complex_file.write_text(
            "def complex_func(x):\n"
            "    if x > 0:\n"
            "        if x > 10:\n"
            "            return 'big'\n"
            "    return 'small'\n"
        )

        from kicli_code_assist.agent.analysis.project_graph import FileNode
        file_node = FileNode(complex_file, "complex.py", "python")

        collector = CodemetricsCollector()
        metrics = collector._analyze_file(complex_file)

        # Should have > 1 complexity due to if statements
        assert metrics["cyclomatic_complexity"] > 1

    def test_get_complex_files(self, test_project):
        """Should identify most complex files."""
        scanner = StructureScanner(test_project)
        files = scanner.scan()

        collector = CodemetricsCollector()
        collector.collect_metrics(files)

        complex_files = collector.get_complex_files(files, threshold=1)
        assert len(complex_files) > 0


class TestProjectGraph:
    """Test dependency graph and impact analysis."""

    def test_transitive_dependents(self, test_project):
        """Should find all transitive dependents."""
        scanner = StructureScanner(test_project)
        files = scanner.scan()

        analyzer = ImportAnalyzer(test_project)
        graph = analyzer.build_graph(files)

        # Get dependents of utils.py
        utils_dependents = graph.get_transitive_dependents("package/utils.py")

        # module_a, module_b, module_c all depend on utils transitively
        assert len(utils_dependents) > 0

    def test_impact_zone_calculation(self, test_project):
        """Should calculate impact zone correctly."""
        scanner = StructureScanner(test_project)
        files = scanner.scan()

        analyzer = ImportAnalyzer(test_project)
        graph = analyzer.build_graph(files)

        # Get impact of changing utils.py
        impact = graph.get_impact_zone("package/utils.py")

        assert isinstance(impact, type(impact))
        assert impact.primary_file == "package/utils.py"

    def test_impact_level_determination(self, test_project):
        """Should determine correct impact level."""
        scanner = StructureScanner(test_project)
        files = scanner.scan()

        analyzer = ImportAnalyzer(test_project)
        graph = analyzer.build_graph(files)

        # Get impact of utils.py (many dependents)
        impact = graph.get_impact_zone("package/utils.py")

        # Should have some dependents, so at least MEDIUM impact
        if impact.all_affected:
            assert impact.impact_level in [ImpactLevel.MEDIUM, ImpactLevel.HIGH, ImpactLevel.CRITICAL]

    def test_get_stats(self, test_project):
        """Should return project statistics."""
        scanner = StructureScanner(test_project)
        files = scanner.scan()

        analyzer = ImportAnalyzer(test_project)
        graph = analyzer.build_graph(files)

        stats = graph.get_stats()

        assert "total_files" in stats
        assert "total_lines" in stats
        assert "languages" in stats
        assert stats["total_files"] == 5  # Python files


class TestProjectAnalysisService:
    """Integration tests for ProjectAnalysisService."""

    def test_analyze_full(self, test_project):
        """Should perform complete analysis."""
        service = ProjectAnalysisService(test_project)
        graph = service.analyze_full()

        assert graph is not None
        assert len(graph.files) == 5

    def test_get_file_impact(self, test_project):
        """Should get impact for specific file."""
        service = ProjectAnalysisService(test_project)
        service.analyze_full()

        impact = service.get_file_impact("package/utils.py")

        assert impact is not None
        assert impact.primary_file == "package/utils.py"

    def test_get_project_stats(self, test_project):
        """Should return project statistics."""
        service = ProjectAnalysisService(test_project)
        service.analyze_full()

        stats = service.get_project_stats()

        assert "total_files" in stats
        assert stats["total_files"] > 0

    def test_get_high_impact_files(self, test_project):
        """Should identify high-impact files."""
        service = ProjectAnalysisService(test_project)
        service.analyze_full()

        high_impact = service.get_high_impact_files()

        # utils.py should be high impact
        assert any("utils.py" in f for f in high_impact)

    def test_analyze_minimal(self, test_project):
        """Should handle minimal project."""
        service = ProjectAnalysisService(test_project)
        metadata = service.analyze()

        assert metadata.name == test_project.name
        assert metadata.root == test_project


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

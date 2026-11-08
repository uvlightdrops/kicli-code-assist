"""
Project Structure Analyzer: Extracts code architecture and patterns from Python projects.

Capabilities:
- AST-based code analysis (classes, functions, patterns)
- Dependency extraction (imports, internal/external)
- Module hierarchy and relationships
- Architecture pattern detection
- Complexity metrics
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class ModuleInfo:
    """Information about a Python module."""
    path: str
    name: str
    classes: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    internal_imports: List[str] = field(default_factory=list)
    loc: int = 0


@dataclass
class ProjectStructure:
    """Comprehensive project structure analysis."""
    project_root: str
    project_name: str
    modules: List[ModuleInfo] = field(default_factory=list)
    total_loc: int = 0
    external_dependencies: Set[str] = field(default_factory=set)
    internal_dependencies: Dict[str, List[str]] = field(default_factory=dict)
    entry_points: List[str] = field(default_factory=list)
    key_abstractions: List[str] = field(default_factory=list)
    architectural_patterns: List[str] = field(default_factory=list)


class ProjectStructureAnalyzer:
    """
    Analyzes Python project code structure using AST.
    Extracts classes, functions, dependencies, and patterns.
    """

    def __init__(self, project_root: str):
        """Initialize analyzer for project root."""
        self.project_root = Path(project_root)
        self.project_name = self.project_root.name
        self.modules: Dict[str, ModuleInfo] = {}
        self.all_imports: Dict[str, List[str]] = defaultdict(list)
        self.class_definitions: Dict[str, str] = {}  # class_name -> module

    def analyze(self) -> ProjectStructure:
        """Run full analysis pipeline."""
        logger.info(f"Analyzing project: {self.project_root}")
        
        # Scan all Python files
        python_files = self._find_python_files()
        logger.info(f"Found {len(python_files)} Python files")
        
        # Analyze each module
        for py_file in python_files:
            self._analyze_module(py_file)
        
        # Build structure
        structure = ProjectStructure(
            project_root=str(self.project_root),
            project_name=self.project_name,
            modules=list(self.modules.values()),
            total_loc=sum(m.loc for m in self.modules.values()),
            external_dependencies=self._extract_external_deps(),
            internal_dependencies=self._build_dependency_graph(),
            entry_points=self._find_entry_points(),
            key_abstractions=self._extract_key_abstractions(),
            architectural_patterns=self._detect_patterns(),
        )
        
        return structure

    def _find_python_files(self) -> List[Path]:
        """Recursively find all Python files in project."""
        python_files = []
        for root, dirs, files in os.walk(self.project_root):
            # Skip common non-code directories
            dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', '.venv', 'venv', 'node_modules', '.egg-info'}]
            
            for file in files:
                if file.endswith('.py') and not file.startswith('.'):
                    python_files.append(Path(root) / file)
        
        return sorted(python_files)

    def _analyze_module(self, py_file: Path) -> None:
        """Analyze single Python module using AST."""
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count LOC
            loc = len([line for line in content.split('\n') if line.strip() and not line.strip().startswith('#')])
            
            # Parse AST
            tree = ast.parse(content)
            
            # Extract module info
            module_name = self._get_module_name(py_file)
            module_info = ModuleInfo(path=str(py_file), name=module_name, loc=loc)
            
            # Walk AST
            for node in ast.walk(tree):
                # Classes
                if isinstance(node, ast.ClassDef):
                    module_info.classes.append(node.name)
                    self.class_definitions[node.name] = module_name
                
                # Functions (top-level)
                elif isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                    module_info.functions.append(node.name)
            
            # Extract imports
            self._extract_imports(tree, module_info)
            
            self.modules[module_name] = module_info
            
        except Exception as e:
            logger.warning(f"Failed to analyze {py_file}: {e}")

    def _get_module_name(self, py_file: Path) -> str:
        """Get relative module name from file path."""
        try:
            rel_path = py_file.relative_to(self.project_root)
            if rel_path.name == '__init__.py':
                return str(rel_path.parent).replace(os.sep, '.')
            else:
                return str(rel_path.with_suffix('')).replace(os.sep, '.')
        except ValueError:
            return str(py_file.stem)

    def _extract_imports(self, tree: ast.AST, module_info: ModuleInfo) -> None:
        """Extract import statements."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_info.imports.append(alias.name)
                    self._categorize_import(alias.name, module_info)
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_info.imports.append(node.module)
                    self._categorize_import(node.module, module_info)

    def _categorize_import(self, import_name: str, module_info: ModuleInfo) -> None:
        """Categorize import as internal or external."""
        if self._is_internal_import(import_name):
            module_info.internal_imports.append(import_name)
        else:
            if import_name not in module_info.imports or import_name not in module_info.internal_imports:
                self.all_imports[import_name].append(module_info.name)

    def _is_internal_import(self, import_name: str) -> bool:
        """Check if import is internal to project."""
        base_name = import_name.split('.')[0]
        
        # Check if it's a project module
        for module in self.modules:
            if module.startswith(base_name):
                return True
        
        # Common stdlib modules
        stdlib_modules = {
            'os', 'sys', 'json', 'logging', 'pathlib', 'typing', 'dataclasses',
            'abc', 'functools', 're', 'collections', 'itertools', 'datetime',
            'subprocess', 'threading', 'asyncio', 'urllib', 'http', 'socket'
        }
        
        return base_name in stdlib_modules

    def _extract_external_deps(self) -> Set[str]:
        """Extract external package dependencies."""
        external = set()
        for import_name, uses in self.all_imports.items():
            base_name = import_name.split('.')[0]
            # Filter out stdlib and internal
            if base_name and not self._is_internal_import(import_name):
                external.add(base_name)
        return external

    def _build_dependency_graph(self) -> Dict[str, List[str]]:
        """Build internal module dependency graph."""
        graph = defaultdict(list)
        for module, info in self.modules.items():
            for internal_imp in info.internal_imports:
                graph[module].append(internal_imp)
        return dict(graph)

    def _find_entry_points(self) -> List[str]:
        """Find main entry points (modules with if __name__ == '__main__')."""
        entry_points = []
        for py_file in self._find_python_files():
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if "__name__" in content and "__main__" in content:
                        module_name = self._get_module_name(py_file)
                        entry_points.append(module_name)
            except Exception:
                pass
        return entry_points

    def _extract_key_abstractions(self) -> List[str]:
        """Extract key abstractions (base classes, main classes)."""
        abstractions = []
        
        # Collect all classes
        for module, info in self.modules.items():
            abstractions.extend(info.classes)
        
        # Prioritize: classes in main modules (shorter paths)
        abstractions.sort(key=lambda x: len(x))
        
        # Filter to most important (remove test/private classes)
        key = [c for c in abstractions if not (c.startswith('_') or c.startswith('Test'))]
        
        return key[:20]  # Top 20

    def _detect_patterns(self) -> List[str]:
        """Detect architectural patterns."""
        patterns = []
        
        # Check for common patterns
        class_names = set(self.class_definitions.keys())
        
        # Factory pattern
        if any('Factory' in name for name in class_names):
            patterns.append("Factory Pattern")
        
        # Strategy pattern
        if any('Strategy' in name for name in class_names):
            patterns.append("Strategy Pattern")
        
        # Observer pattern
        if any('Observer' in name or 'Listener' in name for name in class_names):
            patterns.append("Observer Pattern")
        
        # Manager/Handler pattern
        if any('Manager' in name or 'Handler' in name for name in class_names):
            patterns.append("Manager/Handler Pattern")
        
        # Pipeline/Processing
        if any('Pipeline' in name or 'Processor' in name or 'Task' in name for name in class_names):
            patterns.append("Pipeline/Processing Pattern")
        
        # Service/API pattern
        if any('Service' in name or 'API' in name for name in class_names):
            patterns.append("Service/API Pattern")
        
        # Check module structure
        if len(self.modules) > 1:
            patterns.append("Modular Architecture")
        
        if self._has_config_files():
            patterns.append("Configuration-Driven")
        
        return patterns

    def _has_config_files(self) -> bool:
        """Check if project uses config files."""
        config_patterns = {'.yaml', '.yml', '.json', '.toml', '.ini', '.cfg'}
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', '.venv'}]
            for file in files:
                if any(file.endswith(p) for p in config_patterns):
                    return True
        return False


def get_structure_analyzer(project_root: str) -> ProjectStructureAnalyzer:
    """Factory function for ProjectStructureAnalyzer."""
    return ProjectStructureAnalyzer(project_root)

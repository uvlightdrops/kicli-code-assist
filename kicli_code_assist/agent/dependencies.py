"""Dependency analysis agent for code structure and import relationships."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Optional, Set, Dict, List, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum

from kicli_code_assist.agent.analysis.ast_analyzer import ASTAnalyzer


class DependencyType(Enum):
    """Types of dependencies."""
    IMPORT = "import"
    FROM_IMPORT = "from_import"
    INTERNAL = "internal"
    EXTERNAL = "external"
    CIRCULAR = "circular"


@dataclass
class ImportInfo:
    """Information about a single import statement."""
    module: str
    items: List[str] = field(default_factory=list)
    is_relative: bool = False
    line_number: int = 0
    import_type: str = "import"


@dataclass
class ModuleInfo:
    """Information about a module's dependencies."""
    module_path: str
    imports: List[ImportInfo] = field(default_factory=list)
    internal_dependencies: List[str] = field(default_factory=list)
    external_dependencies: List[str] = field(default_factory=list)
    unused_imports: List[str] = field(default_factory=list)


@dataclass
class DependencyGraph:
    """Complete dependency graph for a project or file."""
    root_module: str
    modules: Dict[str, ModuleInfo] = field(default_factory=dict)
    circular_dependencies: List[Tuple[str, str]] = field(default_factory=list)
    external_packages: Set[str] = field(default_factory=set)
    total_imports: int = 0
    unused_imports_count: int = 0
    has_circular_deps: bool = False
    status: str = "ok"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "root_module": self.root_module,
            "modules": {
                k: asdict(v) for k, v in self.modules.items()
            },
            "circular_dependencies": self.circular_dependencies,
            "external_packages": list(self.external_packages),
            "total_imports": self.total_imports,
            "unused_imports_count": self.unused_imports_count,
            "has_circular_deps": self.has_circular_deps,
            "status": self.status,
        }


class DependencyAnalyzer:
    """Analyze code dependencies and imports."""

    def __init__(self, project_root: Path):
        """Initialize dependency analyzer."""
        self.project_root = project_root
        self.ast_analyzer = ASTAnalyzer()  # No project_root parameter
        self.analyzed_modules: Set[str] = set()

    async def analyze_file(self, file_path: Path) -> DependencyGraph:
        """
        Analyze dependencies for a single file.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            DependencyGraph with imports and dependencies
        """
        file_path = self.project_root / file_path if not file_path.is_absolute() else file_path
        
        graph = DependencyGraph(root_module=str(file_path.relative_to(self.project_root)))
        
        try:
            with open(file_path) as f:
                tree = ast.parse(f.read(), filename=str(file_path))
            
            module_info = ModuleInfo(module_path=str(file_path))
            
            # Extract all imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imp = ImportInfo(
                            module=alias.name,
                            line_number=node.lineno,
                            import_type="import",
                        )
                        module_info.imports.append(imp)
                        self._classify_import(alias.name, module_info)
                        graph.total_imports += 1
                
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        imp = ImportInfo(
                            module=node.module or ".",
                            items=[alias.name],
                            is_relative=node.level > 0,
                            line_number=node.lineno,
                            import_type="from_import",
                        )
                        module_info.imports.append(imp)
                        self._classify_import(node.module or ".", module_info)
                        graph.total_imports += 1
            
            # Detect unused imports (simple heuristic: not referenced in AST except import statement)
            module_info.unused_imports = self._find_unused_imports(file_path, tree)
            graph.unused_imports_count = len(module_info.unused_imports)
            
            graph.modules[str(file_path.relative_to(self.project_root))] = module_info
            
        except Exception as e:
            graph.status = f"error: {str(e)}"
        
        return graph

    async def analyze_directory(self, dir_path: Path) -> DependencyGraph:
        """
        Analyze dependencies for an entire directory.
        
        Args:
            dir_path: Path to directory
            
        Returns:
            DependencyGraph with all modules and cross-references
        """
        dir_path = self.project_root / dir_path if not dir_path.is_absolute() else dir_path
        
        graph = DependencyGraph(root_module=str(dir_path.relative_to(self.project_root)))
        
        # Find all Python files
        py_files = list(dir_path.rglob("*.py"))
        
        for py_file in py_files:
            # Analyze each file
            file_graph = await self.analyze_file(py_file.relative_to(self.project_root))
            
            # Merge into main graph
            for mod_path, mod_info in file_graph.modules.items():
                graph.modules[mod_path] = mod_info
                graph.external_packages.update(mod_info.external_dependencies)
                graph.unused_imports_count += len(mod_info.unused_imports)
        
        # Detect circular dependencies
        graph.circular_dependencies = self._detect_circular_deps(graph)
        graph.has_circular_deps = len(graph.circular_dependencies) > 0
        graph.total_imports = file_graph.total_imports
        
        return graph

    def _classify_import(self, module_name: str, module_info: ModuleInfo):
        """Classify import as internal or external."""
        if module_name.startswith("."):
            module_info.internal_dependencies.append(module_name)
        elif any(
            module_name.startswith(prefix)
            for prefix in ("kicli_", "ki_", "yaml_cfg_")
        ):
            module_info.internal_dependencies.append(module_name)
        else:
            module_info.external_dependencies.append(module_name)

    def _find_unused_imports(self, file_path: Path, tree: ast.AST) -> List[str]:
        """Find potentially unused imports using simple heuristics."""
        imported_names: Set[str] = set()
        used_names: Set[str] = set()
        import_lines: Dict[str, int] = {}
        
        # Collect imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name.split(".")[0]
                    imported_names.add(name)
                    import_lines[name] = node.lineno
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname or alias.name
                    imported_names.add(name)
                    import_lines[name] = node.lineno
        
        # Collect usages (excluding import statements)
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name):
                    used_names.add(node.value.id)
        
        # Find unused
        unused = imported_names - used_names
        return list(unused)

    def _detect_circular_deps(self, graph: DependencyGraph) -> List[Tuple[str, str]]:
        """Detect circular dependencies using simple graph analysis."""
        circular = []
        
        # Build adjacency list
        adj = {mod: [] for mod in graph.modules}
        for mod_path, mod_info in graph.modules.items():
            for dep in mod_info.internal_dependencies:
                # Try to find matching module
                for other_mod in graph.modules:
                    if dep.replace(".", "/") in other_mod or other_mod in dep:
                        adj[mod_path].append(other_mod)
        
        # Simple cycle detection
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        
        def has_cycle(node: str, path: List[str]) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor, path):
                        return True
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    circular.append((cycle[0], cycle[1]))
                    return True
            
            path.pop()
            rec_stack.remove(node)
            return False
        
        for node in adj:
            if node not in visited:
                has_cycle(node, [])
        
        return circular

"""
Refactoring impact analyzer: Find all files affected by code changes.

Handles:
- Finding all usages of a class/function/constant
- Building dependency graphs
- Suggesting safe change order
- Import dependency analysis
"""

import ast
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
import networkx as nx

logger = logging.getLogger("kicli-agent")


@dataclass
class EntityUsage:
    """Single usage of an entity in code."""
    file_path: str
    line_number: int
    context: str  # Code snippet
    usage_type: str  # "definition", "import", "call", "usage"


@dataclass
class RefactoringImpact:
    """Analysis result: what needs to change."""
    entity_type: str  # "class", "function", "constant", "module"
    entity_name: str
    files_with_definition: List[str]
    files_with_import: List[str]
    files_with_usage: List[str]
    all_affected_files: List[str]
    total_affected_files: int
    usages_by_file: Dict[str, List[EntityUsage]] = field(default_factory=dict)
    dependency_graph: Optional[nx.DiGraph] = None
    suggested_change_order: Optional[List[str]] = None
    
    def summary(self) -> str:
        """Human-readable summary."""
        return (
            f"{self.entity_name} ({self.entity_type}) used in {self.total_affected_files} files:\n"
            f"  - Defined in: {', '.join(self.files_with_definition) or 'N/A'}\n"
            f"  - Imported in: {len(self.files_with_import)} files\n"
            f"  - Used in: {len(self.files_with_usage)} files\n"
            f"  - Change order: {' → '.join(self.suggested_change_order or [])}"
        )


class RefactoringAnalyzer:
    """Analyze code for refactoring impacts."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.ast_cache: Dict[str, ast.Module] = {}
    
    def analyze_impact(
        self,
        entity_type: str,
        entity_name: str,
        project_root: Optional[str] = None
    ) -> RefactoringImpact:
        """
        Find all files affected by refactoring an entity.
        
        Args:
            entity_type: "class", "function", "constant", "module"
            entity_name: Name of entity (e.g., "UserAccount")
            project_root: Override root if needed
            
        Returns:
            RefactoringImpact with all findings
        """
        if project_root:
            self.project_root = Path(project_root)
        
        logger.info(f"Analyzing impact of {entity_type} '{entity_name}'")
        
        # Find all Python files
        py_files = list(self.project_root.rglob("*.py"))
        
        # Analyze each file
        files_with_definition = []
        files_with_import = []
        files_with_usage = []
        usages_by_file = {}
        
        for py_file in py_files:
            try:
                tree = self._parse_file(py_file)
                if not tree:
                    continue
                
                # Check for definition
                if self._has_definition(tree, entity_type, entity_name):
                    files_with_definition.append(str(py_file.relative_to(self.project_root)))
                
                # Check for imports
                imports = self._find_imports(tree, entity_name)
                if imports:
                    files_with_import.append(str(py_file.relative_to(self.project_root)))
                    if str(py_file.relative_to(self.project_root)) not in usages_by_file:
                        usages_by_file[str(py_file.relative_to(self.project_root))] = []
                    usages_by_file[str(py_file.relative_to(self.project_root))].extend(imports)
                
                # Check for usage
                usages = self._find_usages(tree, entity_name)
                if usages:
                    files_with_usage.append(str(py_file.relative_to(self.project_root)))
                    rel_path = str(py_file.relative_to(self.project_root))
                    if rel_path not in usages_by_file:
                        usages_by_file[rel_path] = []
                    usages_by_file[rel_path].extend(usages)
            
            except Exception as e:
                logger.warning(f"Error analyzing {py_file}: {e}")
                continue
        
        # Deduplicate
        all_files = sorted(set(files_with_definition + files_with_import + files_with_usage))
        
        # Build dependency graph
        dep_graph = self._build_dependency_graph(all_files)
        
        # Suggest change order
        change_order = self._suggest_change_order(
            dep_graph,
            files_with_definition,
            all_files
        )
        
        impact = RefactoringImpact(
            entity_type=entity_type,
            entity_name=entity_name,
            files_with_definition=files_with_definition,
            files_with_import=files_with_import,
            files_with_usage=files_with_usage,
            all_affected_files=all_files,
            total_affected_files=len(all_files),
            usages_by_file=usages_by_file,
            dependency_graph=dep_graph,
            suggested_change_order=change_order
        )
        
        logger.info(impact.summary())
        return impact
    
    def _parse_file(self, file_path: Path) -> Optional[ast.Module]:
        """Parse Python file, cache result."""
        file_str = str(file_path)
        if file_str in self.ast_cache:
            return self.ast_cache[file_str]
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source)
            self.ast_cache[file_str] = tree
            return tree
        except Exception:
            return None
    
    def _has_definition(self, tree: ast.Module, entity_type: str, name: str) -> bool:
        """Check if entity is defined in AST."""
        if entity_type == "class":
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == name:
                    return True
        elif entity_type == "function":
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == name:
                    return True
        return False
    
    def _find_imports(self, tree: ast.Module, entity_name: str) -> List[EntityUsage]:
        """Find all imports of entity."""
        usages = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.names:
                    for alias in node.names:
                        if alias.name == entity_name or alias.name == "*":
                            usages.append(EntityUsage(
                                file_path="",
                                line_number=node.lineno,
                                context=f"from {node.module} import {alias.name}",
                                usage_type="import"
                            ))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if entity_name in alias.name:
                        usages.append(EntityUsage(
                            file_path="",
                            line_number=node.lineno,
                            context=f"import {alias.name}",
                            usage_type="import"
                        ))
        return usages
    
    def _find_usages(self, tree: ast.Module, entity_name: str) -> List[EntityUsage]:
        """Find all usages of entity."""
        usages = []
        for node in ast.walk(tree):
            # Name reference
            if isinstance(node, ast.Name) and node.id == entity_name:
                usages.append(EntityUsage(
                    file_path="",
                    line_number=node.lineno,
                    context=entity_name,
                    usage_type="usage"
                ))
            # Attribute access
            elif isinstance(node, ast.Attribute) and node.attr == entity_name:
                usages.append(EntityUsage(
                    file_path="",
                    line_number=node.lineno,
                    context=f"*.{entity_name}",
                    usage_type="usage"
                ))
        return usages
    
    def _build_dependency_graph(self, files: List[str]) -> nx.DiGraph:
        """Build directed graph: file A → file B means A depends on B."""
        graph = nx.DiGraph()
        graph.add_nodes_from(files)
        
        for file in files:
            file_path = self.project_root / file
            tree = self._parse_file(file_path)
            if not tree:
                continue
            
            # Find what this file imports
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    # from X import Y → depends on X
                    if node.module:
                        module_file = self._module_to_file(node.module)
                        if module_file and module_file in files:
                            graph.add_edge(file, module_file)
        
        return graph
    
    def _module_to_file(self, module_name: str) -> Optional[str]:
        """Convert module name to file path."""
        # Simple conversion: pkg.submodule → pkg/submodule.py
        parts = module_name.split(".")
        file_path = self.project_root / "/".join(parts[:-1]) / f"{parts[-1]}.py"
        
        if file_path.exists():
            return str(file_path.relative_to(self.project_root))
        
        # Try __init__.py
        file_path = self.project_root / "/".join(parts) / "__init__.py"
        if file_path.exists():
            return str(file_path.relative_to(self.project_root))
        
        return None
    
    def _suggest_change_order(
        self,
        graph: nx.DiGraph,
        definition_files: List[str],
        all_files: List[str]
    ) -> List[str]:
        """
        Suggest safe order: definitions first, then dependents.
        
        Strategy:
        1. Files defining the entity
        2. Files that depend on definitions (topological sort)
        """
        order = []
        
        # First: files with definitions
        for f in definition_files:
            if f in all_files:
                order.append(f)
        
        # Then: dependents in topological order
        try:
            topo = list(nx.topological_sort(graph))
            for f in topo:
                if f not in order and f in all_files:
                    order.append(f)
        except nx.NetworkXError:
            # Circular dependency, fall back to sorting
            for f in sorted(all_files):
                if f not in order:
                    order.append(f)
        
        return order


# Example usage
if __name__ == "__main__":
    analyzer = RefactoringAnalyzer("/home/flow/dev_flow/kicli-code-assist")
    impact = analyzer.analyze_impact("class", "CodeImplementationAgent")
    print(impact.summary())

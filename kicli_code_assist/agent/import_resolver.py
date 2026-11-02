"""
Import resolver: Update and validate imports when code is refactored.

Handles:
- Updating import statements
- Detecting circular imports
- Validating import chains
- Handling relative vs. absolute imports
"""

import ast
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Set, Optional, Tuple, Dict

logger = logging.getLogger("kicli-agent")


@dataclass
class ImportIssue:
    """Problem found in imports."""
    file_path: str
    issue_type: str  # "circular", "missing", "duplicate", "syntax"
    description: str
    severity: str  # "error", "warning"


class ImportResolver:
    """Manage and validate imports during refactoring."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.ast_cache: Dict[str, ast.Module] = {}
    
    def update_imports(
        self,
        file_path: str,
        old_entity: str,
        new_entity: str,
        old_module: Optional[str] = None,
        new_module: Optional[str] = None
    ) -> str:
        """
        Update import statements in a file.
        
        Examples:
        - Rename class: UserAccount → User
          from models import UserAccount → from models import User
          
        - Move class: models.py → user_models.py
          from models import UserAccount → from user_models import UserAccount
          
        - Both: move + rename
          from models import UserAccount → from user_models import User
        
        Args:
            file_path: Path to file to update
            old_entity: Old name (e.g., "UserAccount")
            new_entity: New name (e.g., "User")
            old_module: Old module if moving (e.g., "models")
            new_module: New module if moving (e.g., "user_models")
            
        Returns:
            Updated file content
        """
        file_path = self.project_root / file_path
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()
        except Exception as e:
            logger.error(f"Cannot read {file_path}: {e}")
            return source
        
        # Parse and transform
        lines = source.split("\n")
        updated_lines = []
        
        for line in lines:
            updated_line = self._update_import_line(
                line, old_entity, new_entity, old_module, new_module
            )
            updated_lines.append(updated_line)
        
        result = "\n".join(updated_lines)
        logger.debug(f"Updated imports in {file_path}")
        return result
    
    def _update_import_line(
        self,
        line: str,
        old_entity: str,
        new_entity: str,
        old_module: Optional[str],
        new_module: Optional[str]
    ) -> str:
        """Update single line if it contains the entity."""
        stripped = line.strip()
        
        # Pattern 1: from module import Entity
        if stripped.startswith("from "):
            parts = stripped.split()
            if len(parts) >= 4 and parts[0] == "from" and parts[2] == "import":
                module = parts[1]
                imported = " ".join(parts[3:])  # Everything after "import"
                
                # Check if this import is for the entity
                if old_module and module != old_module:
                    return line
                
                # Update entity name
                if old_entity in imported:
                    imported_updated = imported.replace(old_entity, new_entity)
                    
                    # Update module if specified
                    if new_module:
                        module = new_module
                    
                    indent = len(line) - len(line.lstrip())
                    return " " * indent + f"from {module} import {imported_updated}"
        
        # Pattern 2: import module.entity or import module as alias
        elif stripped.startswith("import "):
            # Handle: import models.UserAccount as UA
            # → import user_models.User as UA
            parts = stripped.split()
            if len(parts) >= 2:
                module_path = parts[1]
                
                if old_entity in module_path:
                    updated = module_path.replace(old_entity, new_entity)
                    if old_module and new_module:
                        updated = updated.replace(old_module, new_module)
                    
                    rest = " ".join(parts[2:])  # as alias, etc.
                    indent = len(line) - len(line.lstrip())
                    return " " * indent + f"import {updated}" + (f" {rest}" if rest else "")
        
        # No change needed
        return line
    
    def validate_import_chain(
        self,
        file_path: str,
        project_root: Optional[str] = None
    ) -> List[ImportIssue]:
        """
        Check for circular imports and other import issues.
        
        Args:
            file_path: File to validate
            project_root: Override root if needed
            
        Returns:
            List of ImportIssue objects (empty if OK)
        """
        if project_root:
            self.project_root = Path(project_root)
        
        file_path = self.project_root / file_path
        issues = []
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()
            
            tree = ast.parse(source)
        except Exception as e:
            issues.append(ImportIssue(
                file_path=str(file_path.relative_to(self.project_root)),
                issue_type="syntax",
                description=f"Cannot parse file: {e}",
                severity="error"
            ))
            return issues
        
        # Check for circular imports
        imports = self._extract_imports(tree)
        circular = self._find_circular_imports(str(file_path.relative_to(self.project_root)), imports)
        issues.extend(circular)
        
        # Check for missing imports (referenced names not imported)
        missing = self._find_missing_imports(tree)
        issues.extend(missing)
        
        # Check for duplicate imports
        duplicates = self._find_duplicate_imports(tree)
        issues.extend(duplicates)
        
        if issues:
            logger.warning(f"Found {len(issues)} import issues in {file_path}")
        
        return issues
    
    def _extract_imports(self, tree: ast.Module) -> Set[str]:
        """Extract all imports from AST."""
        imports = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
        
        return imports
    
    def _find_circular_imports(self, file_path: str, imports: Set[str]) -> List[ImportIssue]:
        """Detect if imports create a circle."""
        issues = []
        
        # Simple check: if A imports B and B imports A → circular
        for import_target in imports:
            import_file = self._module_to_file(import_target)
            if not import_file:
                continue
            
            try:
                with open(self.project_root / import_file, "r", encoding="utf-8") as f:
                    source = f.read()
                
                tree = ast.parse(source)
                reverse_imports = self._extract_imports(tree)
                
                # Does the imported module import us back?
                for rev_import in reverse_imports:
                    if rev_import == file_path.replace(".py", "").replace("/", "."):
                        issues.append(ImportIssue(
                            file_path=file_path,
                            issue_type="circular",
                            description=f"Circular import: {file_path} ↔ {import_file}",
                            severity="error"
                        ))
            except Exception:
                pass
        
        return issues
    
    def _find_missing_imports(self, tree: ast.Module) -> List[ImportIssue]:
        """Find references to names that aren't imported."""
        issues = []
        
        imported_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.names:
                    for alias in node.names:
                        name = alias.asname or alias.name
                        imported_names.add(name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name.split(".")[0]
                    imported_names.add(name)
        
        # Find Name references
        referenced_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                referenced_names.add(node.id)
        
        # Built-ins and common names to ignore
        builtins = {"print", "len", "str", "int", "list", "dict", "set", "tuple", "type", "object", "super", "property", "staticmethod", "classmethod"}
        
        missing = referenced_names - imported_names - builtins
        
        for name in sorted(missing):
            issues.append(ImportIssue(
                file_path="",
                issue_type="missing",
                description=f"Name '{name}' used but not imported",
                severity="warning"
            ))
        
        return issues
    
    def _find_duplicate_imports(self, tree: ast.Module) -> List[ImportIssue]:
        """Find duplicate import statements."""
        issues = []
        seen_imports = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                key = (node.module, tuple(alias.name for alias in node.names))
                if key in seen_imports:
                    issues.append(ImportIssue(
                        file_path="",
                        issue_type="duplicate",
                        description=f"Duplicate import: from {node.module} import ...",
                        severity="warning"
                    ))
                seen_imports.add(key)
        
        return issues
    
    def _module_to_file(self, module_name: str) -> Optional[str]:
        """Convert module name to file path."""
        parts = module_name.split(".")
        
        # Try as direct file
        file_path = self.project_root / "/".join(parts) + ".py"
        if file_path.exists():
            return str(file_path.relative_to(self.project_root))
        
        # Try as package
        file_path = self.project_root / "/".join(parts) / "__init__.py"
        if file_path.exists():
            return str(file_path.relative_to(self.project_root))
        
        return None


# Example usage
if __name__ == "__main__":
    resolver = ImportResolver("/home/flow/dev_flow/kicli-code-assist")
    
    # Test: update imports in a file
    content = resolver.update_imports(
        "kicli_code_assist/agent/code_implementation.py",
        "UserAccount",
        "User"
    )
    
    # Test: validate imports
    issues = resolver.validate_import_chain(
        "kicli_code_assist/agent/code_implementation.py"
    )
    for issue in issues:
        print(f"  {issue.issue_type}: {issue.description}")

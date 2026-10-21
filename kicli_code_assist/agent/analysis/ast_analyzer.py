"""AST Analyzer for Python code understanding."""

import ast
import inspect
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Any


@dataclass
class ImportInfo:
    """Information about an import statement."""
    module: str
    name: Optional[str] = None  # For 'from X import Y', name is Y
    alias: Optional[str] = None
    line_no: int = 0
    is_relative: bool = False

    @property
    def full_name(self) -> str:
        """Return the fully qualified imported name."""
        if self.name:
            return f"{self.module}.{self.name}"
        return self.module


@dataclass
class ParameterInfo:
    """Information about a function parameter."""
    name: str
    annotation: Optional[str] = None
    default: Optional[str] = None


@dataclass
class FunctionInfo:
    """Information about a function definition."""
    name: str
    file: Path
    line_no: int
    end_line: int
    docstring: Optional[str] = None
    parameters: List[ParameterInfo] = field(default_factory=list)
    return_annotation: Optional[str] = None
    is_async: bool = False
    is_private: bool = False
    complexity: int = 1  # Cyclomatic complexity
    body: str = ""


@dataclass
class ClassInfo:
    """Information about a class definition."""
    name: str
    file: Path
    line_no: int
    end_line: int
    docstring: Optional[str] = None
    base_classes: List[str] = field(default_factory=list)
    methods: List[FunctionInfo] = field(default_factory=list)
    attributes: Dict[str, Optional[str]] = field(default_factory=dict)  # name -> type annotation
    body: str = ""


class ASTAnalyzer:
    """Analyzes Python files using AST to extract structure and semantics."""

    def __init__(self):
        self.files_analyzed: Dict[Path, ast.AST] = {}
        self.cache: Dict[str, Any] = {}

    def analyze_file(self, file_path: Path) -> tuple[List[FunctionInfo], List[ClassInfo], List[ImportInfo]]:
        """Analyze a Python file and extract functions, classes, and imports."""
        file_path = Path(file_path).resolve()

        if file_path in self.files_analyzed:
            # Return cached analysis
            return self._extract_cached(file_path)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()
        except (IOError, UnicodeDecodeError) as e:
            raise ValueError(f"Cannot read file {file_path}: {e}")

        try:
            tree = ast.parse(source, filename=str(file_path))
        except SyntaxError as e:
            raise ValueError(f"Syntax error in {file_path}: {e}")

        self.files_analyzed[file_path] = tree

        functions = []
        classes = []
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_info = self._extract_function_info(node, file_path, source)
                functions.append(func_info)
            elif isinstance(node, ast.AsyncFunctionDef):
                func_info = self._extract_function_info(node, file_path, source, is_async=True)
                functions.append(func_info)
            elif isinstance(node, ast.ClassDef):
                class_info = self._extract_class_info(node, file_path, source)
                classes.append(class_info)

        # Extract top-level imports only
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.extend(self._extract_imports(node))

        return functions, classes, imports

    def _extract_function_info(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, file_path: Path, source: str, is_async: bool = False
    ) -> FunctionInfo:
        """Extract information from a function definition node."""
        docstring = ast.get_docstring(node)
        params = []

        for arg in node.args.args:
            annotation = None
            if arg.annotation:
                annotation = ast.unparse(arg.annotation)

            # Get default value if it exists
            default = None
            default_offset = len(node.args.args) - len(node.args.defaults)
            arg_index = node.args.args.index(arg)
            if arg_index >= default_offset:
                default = ast.unparse(node.args.defaults[arg_index - default_offset])

            params.append(ParameterInfo(name=arg.arg, annotation=annotation, default=default))

        return_annotation = None
        if node.returns:
            return_annotation = ast.unparse(node.returns)

        # Extract function body
        body_lines = source.split("\n")[node.lineno - 1 : node.end_lineno]  # type: ignore
        body = "\n".join(body_lines)

        complexity = self._calculate_cyclomatic_complexity(node)

        return FunctionInfo(
            name=node.name,
            file=file_path,
            line_no=node.lineno,
            end_line=node.end_lineno or node.lineno,  # type: ignore
            docstring=docstring,
            parameters=params,
            return_annotation=return_annotation,
            is_async=is_async,
            is_private=node.name.startswith("_"),
            complexity=complexity,
            body=body,
        )

    def _extract_class_info(self, node: ast.ClassDef, file_path: Path, source: str) -> ClassInfo:
        """Extract information from a class definition node."""
        docstring = ast.get_docstring(node)

        base_classes = []
        for base in node.bases:
            base_classes.append(ast.unparse(base))

        # Extract methods
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_info = self._extract_function_info(item, file_path, source, isinstance(item, ast.AsyncFunctionDef))
                methods.append(method_info)

        # Extract class attributes from annotations and assignments
        attributes: Dict[str, Optional[str]] = {}
        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                annotation = ast.unparse(item.annotation) if item.annotation else None
                attributes[item.target.id] = annotation

        # Extract class body
        body_lines = source.split("\n")[node.lineno - 1 : node.end_lineno]  # type: ignore
        body = "\n".join(body_lines)

        return ClassInfo(
            name=node.name,
            file=file_path,
            line_no=node.lineno,
            end_line=node.end_lineno or node.lineno,  # type: ignore
            docstring=docstring,
            base_classes=base_classes,
            methods=methods,
            attributes=attributes,
            body=body,
        )

    def _extract_imports(self, node: ast.Import | ast.ImportFrom) -> List[ImportInfo]:
        """Extract imports from Import or ImportFrom nodes."""
        imports = []

        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(
                    ImportInfo(
                        module=alias.name,
                        alias=alias.asname,
                        line_no=node.lineno,
                    )
                )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imports.append(
                    ImportInfo(
                        module=module,
                        name=alias.name,
                        alias=alias.asname,
                        line_no=node.lineno,
                        is_relative=node.level > 0,
                    )
                )

        return imports

    def _calculate_cyclomatic_complexity(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
        """Calculate cyclomatic complexity of a function (simple version)."""
        complexity = 1
        for n in ast.walk(node):
            if isinstance(n, (ast.If, ast.While, ast.For, ast.ExceptHandler, ast.BoolOp)):
                complexity += 1
        return complexity

    def get_function_docstring(self, func_name: str, file_path: Path) -> Optional[str]:
        """Get docstring for a specific function."""
        functions, _, _ = self.analyze_file(file_path)
        for func in functions:
            if func.name == func_name:
                return func.docstring
        return None

    def get_class_methods(self, class_name: str, file_path: Path) -> List[FunctionInfo]:
        """Get all methods of a specific class."""
        _, classes, _ = self.analyze_file(file_path)
        for cls in classes:
            if cls.name == class_name:
                return cls.methods
        return []

    def clear_cache(self):
        """Clear analysis cache."""
        self.files_analyzed.clear()
        self.cache.clear()

    def _extract_cached(self, file_path: Path) -> tuple[List[FunctionInfo], List[ClassInfo], List[ImportInfo]]:
        """Re-extract from cached AST (for demonstration - real impl would cache results)."""
        tree = self.files_analyzed[file_path]
        source = open(file_path, "r", encoding="utf-8").read()

        functions = []
        classes = []
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_info = self._extract_function_info(node, file_path, source)
                functions.append(func_info)
            elif isinstance(node, ast.ClassDef):
                class_info = self._extract_class_info(node, file_path, source)
                classes.append(class_info)

        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.extend(self._extract_imports(node))

        return functions, classes, imports

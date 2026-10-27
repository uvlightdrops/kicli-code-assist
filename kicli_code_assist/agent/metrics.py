"""Code metrics analyzer for code health and complexity metrics."""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict, field
from enum import Enum

from kicli_code_assist.agent.analysis.ast_analyzer import ASTAnalyzer


class ComplexityLevel(Enum):
    """Complexity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class FunctionMetrics:
    """Metrics for a single function."""
    name: str
    line_start: int
    line_end: int
    lines_of_code: int
    cyclomatic_complexity: int
    number_of_parameters: int
    is_async: bool = False
    complexity_level: str = ComplexityLevel.LOW.value


@dataclass
class FileMetrics:
    """Metrics for an entire file."""
    file_path: str
    total_lines: int
    code_lines: int
    comment_lines: int
    blank_lines: int
    number_of_functions: int
    number_of_classes: int
    average_function_length: float
    average_complexity: float
    functions: List[FunctionMetrics] = field(default_factory=list)
    maintainability_index: float = 0.0  # 0 to 100
    duplication_ratio: float = 0.0  # 0 to 1
    status: str = "ok"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "file_path": self.file_path,
            "total_lines": self.total_lines,
            "code_lines": self.code_lines,
            "comment_lines": self.comment_lines,
            "blank_lines": self.blank_lines,
            "number_of_functions": self.number_of_functions,
            "number_of_classes": self.number_of_classes,
            "average_function_length": self.average_function_length,
            "average_complexity": self.average_complexity,
            "functions": [asdict(f) for f in self.functions],
            "maintainability_index": self.maintainability_index,
            "duplication_ratio": self.duplication_ratio,
            "status": self.status,
        }


class CodeMetricsAnalyzer:
    """Analyze code metrics and complexity."""

    def __init__(self, project_root: Path):
        """Initialize metrics analyzer."""
        self.project_root = project_root
        self.ast_analyzer = ASTAnalyzer()  # No project_root parameter

    def analyze(self, file_path: str | Path) -> dict:
        """
        Synchronous wrapper for analyze_file.
        
        Args:
            file_path: Path to Python file (string or Path)
            
        Returns:
            Dictionary with metrics data
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)
        
        metrics = self._analyze_file_sync(file_path)
        return metrics.to_dict()

    def _analyze_file_sync(self, file_path: Path) -> FileMetrics:
        """
        Analyze metrics for a single file.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            FileMetrics with comprehensive code metrics
        """
        file_path = self.project_root / file_path if not file_path.is_absolute() else file_path
        
        metrics = FileMetrics(
            file_path=str(file_path.relative_to(self.project_root)),
            total_lines=0,
            code_lines=0,
            comment_lines=0,
            blank_lines=0,
            number_of_functions=0,
            number_of_classes=0,
            average_function_length=0.0,
            average_complexity=0.0,
        )
        
        try:
            with open(file_path) as f:
                source = f.read()
                tree = ast.parse(source, filename=str(file_path))
            
            lines = source.split("\n")
            metrics.total_lines = len(lines)
            
            # Count line types
            metrics.code_lines, metrics.comment_lines, metrics.blank_lines = self._count_line_types(
                lines
            )
            
            # Analyze functions
            func_metrics_list = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_metrics = self._analyze_function(node, lines, file_path)
                    func_metrics_list.append(func_metrics)
                    metrics.number_of_functions += 1
                
                elif isinstance(node, ast.ClassDef):
                    metrics.number_of_classes += 1
            
            metrics.functions = func_metrics_list
            
            # Calculate averages
            if metrics.number_of_functions > 0:
                total_loc = sum(f.lines_of_code for f in func_metrics_list)
                metrics.average_function_length = total_loc / metrics.number_of_functions
                
                total_complexity = sum(f.cyclomatic_complexity for f in func_metrics_list)
                metrics.average_complexity = total_complexity / metrics.number_of_functions
            
            # Calculate maintainability index (0-100 scale)
            metrics.maintainability_index = self._calculate_maintainability_index(metrics)
            
            # Calculate duplication ratio (simple heuristic)
            metrics.duplication_ratio = self._calculate_duplication_ratio(source)
            
        except Exception as e:
            metrics.status = f"error: {str(e)}"
        
        return metrics

    def _count_line_types(self, lines: List[str]) -> tuple[int, int, int]:
        """Count code, comment, and blank lines."""
        code_lines = 0
        comment_lines = 0
        blank_lines = 0
        
        for line in lines:
            stripped = line.strip()
            
            if not stripped:
                blank_lines += 1
            elif stripped.startswith("#"):
                comment_lines += 1
            else:
                code_lines += 1
        
        return code_lines, comment_lines, blank_lines

    def _analyze_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, lines: List[str], file_path: Path
    ) -> FunctionMetrics:
        """Analyze metrics for a single function."""
        func_metrics = FunctionMetrics(
            name=node.name,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            lines_of_code=node.end_lineno - node.lineno + 1 if node.end_lineno else 1,
            cyclomatic_complexity=self._calculate_cyclomatic_complexity(node),
            number_of_parameters=len(node.args.args),
            is_async=isinstance(node, ast.AsyncFunctionDef),
        )
        
        # Assign complexity level
        if func_metrics.cyclomatic_complexity <= 2:
            func_metrics.complexity_level = ComplexityLevel.LOW.value
        elif func_metrics.cyclomatic_complexity <= 5:
            func_metrics.complexity_level = ComplexityLevel.MEDIUM.value
        elif func_metrics.cyclomatic_complexity <= 10:
            func_metrics.complexity_level = ComplexityLevel.HIGH.value
        else:
            func_metrics.complexity_level = ComplexityLevel.VERY_HIGH.value
        
        return func_metrics

    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """
        Calculate cyclomatic complexity (simplified).
        Counts decision points: if, elif, else, for, while, except, etc.
        """
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                # Count boolean operators as decision points
                complexity += len(child.values) - 1
        
        return complexity

    def _calculate_maintainability_index(self, metrics: FileMetrics) -> float:
        """
        Calculate maintainability index (0-100 scale).
        Based on LOC, cyclomatic complexity, and documentation.
        """
        if metrics.code_lines == 0:
            return 100.0
        
        # Penalize high LOC
        loc_penalty = min(40, metrics.total_lines / 10)
        
        # Penalize high complexity
        complexity_penalty = min(30, metrics.average_complexity * 5)
        
        # Reward documentation
        comment_ratio = metrics.comment_lines / metrics.code_lines if metrics.code_lines > 0 else 0
        comment_reward = min(20, comment_ratio * 100)
        
        # Base score of 100
        index = 100.0 - loc_penalty - complexity_penalty + comment_reward
        
        return max(0.0, min(100.0, index))

    def _calculate_duplication_ratio(self, source: str) -> float:
        """
        Calculate code duplication ratio (simple heuristic).
        Looks for repeated line patterns.
        """
        lines = source.split("\n")
        if len(lines) < 2:
            return 0.0
        
        # Count identical lines
        line_counts: Dict[str, int] = {}
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                line_counts[stripped] = line_counts.get(stripped, 0) + 1
        
        # Calculate ratio of duplicated lines
        duplicated = sum(count - 1 for count in line_counts.values() if count > 1)
        
        return duplicated / len(lines) if lines else 0.0

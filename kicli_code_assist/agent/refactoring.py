"""Refactoring suggestions agent for code improvements."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict, field
from enum import Enum

from kicli_code_assist.agent.analysis.ast_analyzer import ASTAnalyzer


class RefactoringType(Enum):
    """Types of refactoring suggestions."""
    EXTRACT_METHOD = "extract_method"
    RENAME_VARIABLE = "rename_variable"
    REDUCE_COMPLEXITY = "reduce_complexity"
    REMOVE_DUPLICATION = "remove_duplication"
    SIMPLIFY_LOGIC = "simplify_logic"
    IMPROVE_NAMING = "improve_naming"


@dataclass
class RefactoringSuggestion:
    """A single refactoring suggestion."""
    refactoring_type: str
    location: str  # File:line
    current_code: str
    suggested_code: str
    explanation: str
    impact_score: float  # 0.0 to 1.0 (readability, performance, maintainability)
    difficulty: str  # easy, medium, hard
    priority: int  # 1 (critical) to 5 (nice-to-have)


@dataclass
class RefactoringResult:
    """Result of refactoring analysis."""
    file_path: str
    suggestions: List[RefactoringSuggestion] = field(default_factory=list)
    total_issues: int = 0
    improvement_potential: float = 0.0  # 0.0 to 1.0
    status: str = "ok"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "file_path": self.file_path,
            "suggestions": [asdict(s) for s in self.suggestions],
            "total_issues": self.total_issues,
            "improvement_potential": self.improvement_potential,
            "status": self.status,
        }


class RefactoringAnalyzer:
    """Analyze code and suggest refactorings."""

    def __init__(self, project_root: Path):
        """Initialize refactoring analyzer."""
        self.project_root = project_root
        self.ast_analyzer = ASTAnalyzer()  # No project_root parameter

    async def analyze_file(self, file_path: Path) -> RefactoringResult:
        """
        Analyze file for refactoring opportunities.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            RefactoringResult with suggestions
        """
        file_path = self.project_root / file_path if not file_path.is_absolute() else file_path
        
        result = RefactoringResult(file_path=str(file_path.relative_to(self.project_root)))
        
        try:
            with open(file_path) as f:
                source = f.read()
                tree = ast.parse(source, filename=str(file_path))
            
            lines = source.split("\n")
            
            # Analyze for different refactoring opportunities
            result.suggestions.extend(self._check_long_methods(tree, lines, file_path))
            result.suggestions.extend(self._check_complex_conditionals(tree, lines, file_path))
            result.suggestions.extend(self._check_poor_naming(tree, lines, file_path))
            result.suggestions.extend(self._check_duplicate_logic(tree, lines, file_path))
            
            result.total_issues = len(result.suggestions)
            
            # Calculate improvement potential as weighted average impact
            if result.suggestions:
                total_impact = sum(s.impact_score for s in result.suggestions)
                result.improvement_potential = min(1.0, total_impact / len(result.suggestions))
            
            # Sort by priority
            result.suggestions.sort(key=lambda s: s.priority)
            
        except Exception as e:
            result.status = f"error: {str(e)}"
        
        return result

    def _check_long_methods(
        self, tree: ast.AST, lines: List[str], file_path: Path
    ) -> List[RefactoringSuggestion]:
        """Check for methods that are too long."""
        suggestions = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_length = node.end_lineno - node.lineno + 1
                
                # Threshold: methods over 50 lines should be considered for extraction
                if method_length > 50:
                    current = "\n".join(lines[node.lineno - 1 : min(node.end_lineno, len(lines))])
                    
                    suggestion = RefactoringSuggestion(
                        refactoring_type=RefactoringType.EXTRACT_METHOD.value,
                        location=f"{file_path.name}:{node.lineno}",
                        current_code=current[:200] + "..." if len(current) > 200 else current,
                        suggested_code=f"# Extract sub-functions:\n# def helper_1():\n#     ...\n# def helper_2():\n#     ...",
                        explanation=f"Method '{node.name}' is {method_length} lines long. Consider extracting logical sections into separate helper methods for better maintainability.",
                        impact_score=0.8,
                        difficulty="medium",
                        priority=2,
                    )
                    suggestions.append(suggestion)
        
        return suggestions

    def _check_complex_conditionals(
        self, tree: ast.AST, lines: List[str], file_path: Path
    ) -> List[RefactoringSuggestion]:
        """Check for overly complex conditionals."""
        suggestions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                # Count depth of nested conditionals
                depth = self._count_nesting_depth(node)
                
                if depth > 3:
                    current = "\n".join(
                        lines[node.lineno - 1 : min(node.lineno + 5, len(lines))]
                    )
                    
                    suggestion = RefactoringSuggestion(
                        refactoring_type=RefactoringType.REDUCE_COMPLEXITY.value,
                        location=f"{file_path.name}:{node.lineno}",
                        current_code=current,
                        suggested_code="# Use early returns or guard clauses\n# if not condition:\n#     return\n# Process main logic",
                        explanation=f"Nested conditional with depth {depth}. Consider using guard clauses or early returns to reduce complexity.",
                        impact_score=0.7,
                        difficulty="medium",
                        priority=2,
                    )
                    suggestions.append(suggestion)
        
        return suggestions

    def _check_poor_naming(
        self, tree: ast.AST, lines: List[str], file_path: Path
    ) -> List[RefactoringSuggestion]:
        """Check for variables with poor names."""
        suggestions = []
        
        poor_names = {"x", "y", "z", "tmp", "temp", "foo", "bar", "data", "val"}
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in poor_names:
                if isinstance(node.ctx, ast.Store):  # Assignment
                    suggestion = RefactoringSuggestion(
                        refactoring_type=RefactoringType.IMPROVE_NAMING.value,
                        location=f"{file_path.name}:{node.lineno}",
                        current_code=node.id,
                        suggested_code=f"# Use descriptive name like 'parsed_{node.id}' or similar",
                        explanation=f"Variable name '{node.id}' is too generic. Use more descriptive names to improve code clarity.",
                        impact_score=0.6,
                        difficulty="easy",
                        priority=4,
                    )
                    suggestions.append(suggestion)
        
        return suggestions

    def _check_duplicate_logic(
        self, tree: ast.AST, lines: List[str], file_path: Path
    ) -> List[RefactoringSuggestion]:
        """Check for duplicate logic patterns."""
        suggestions = []
        
        # Collect all assignment patterns
        patterns: Dict[str, int] = {}
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                # Simple pattern: create a hash of the assignment
                pattern = ast.unparse(node.value)[:50]  # First 50 chars
                patterns[pattern] = patterns.get(pattern, 0) + 1
        
        # If same pattern appears 3+ times, suggest extraction
        for pattern, count in patterns.items():
            if count >= 3:
                suggestion = RefactoringSuggestion(
                    refactoring_type=RefactoringType.REMOVE_DUPLICATION.value,
                    location=f"{file_path.name}",
                    current_code=pattern,
                    suggested_code=f"# Extract into helper function or class method",
                    explanation=f"Similar pattern appears {count} times in this file. Consider extracting into a reusable function.",
                    impact_score=0.75,
                    difficulty="medium",
                    priority=2,
                )
                suggestions.append(suggestion)
        
        return suggestions

    def _count_nesting_depth(self, node: ast.AST, depth: int = 0) -> int:
        """Recursively count nesting depth of conditionals."""
        if isinstance(node, ast.If):
            max_depth = depth
            for child in ast.iter_child_nodes(node):
                child_depth = self._count_nesting_depth(child, depth + 1)
                max_depth = max(max_depth, child_depth)
            return max_depth
        else:
            for child in ast.iter_child_nodes(node):
                depth = max(depth, self._count_nesting_depth(child, depth))
            return depth

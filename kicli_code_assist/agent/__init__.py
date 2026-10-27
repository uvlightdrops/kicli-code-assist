"""Programming Agent - Main orchestrator for code analysis and explanation."""

import logging
from pathlib import Path
from typing import Optional, Dict, Any

from kicli_code_assist.agent.analysis import (
    ASTAnalyzer,
    DependencyResolver,
    ProjectAnalysisService,
    SemanticIndexer,
    SmartSelector,
)

# Phase 2B: Export executor components
from kicli_code_assist.agent.executor import (
    ASTContext,
    AgentExecutor,
    ExecutorResult,
)

__all__ = [
    "ProgrammingAgent",
    "ASTContext",
    "AgentExecutor",
    "ExecutorResult",
]

logger = logging.getLogger("kicli-agent")


class ProgrammingAgent:
    """Main agent for code analysis and intelligent suggestions."""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        self.ast_analyzer = ASTAnalyzer()
        self.dependency_resolver = DependencyResolver(project_root)
        self.project_analyzer = ProjectAnalysisService(project_root)
        self.semantic_indexer = SemanticIndexer()
        self.smart_selector = SmartSelector(max_tokens=4000)

        logger.info(f"ProgrammingAgent initialized for {project_root}")

    def explain_code(self, file_path: Path, line_no: Optional[int] = None) -> Dict[str, Any]:
        """Explain a file or specific line of code.
        
        Args:
            file_path: Path to the file to explain
            line_no: Optional line number for targeted explanation
            
        Returns:
            Dict with:
            - summary: Brief explanation
            - details: Full explanation
            - context: Related code context
            - functions_affected: Functions in this file
            - dependents: Files that depend on this
        """
        file_path = Path(file_path).resolve()

        try:
            # Analyze the file
            functions, classes, imports = self.ast_analyzer.analyze_file(file_path)

            # If line specified, find the entity at that line
            target_entity = None
            if line_no:
                for func in functions:
                    if func.line_no <= line_no <= func.end_line:
                        target_entity = func
                        break
                if not target_entity:
                    for cls in classes:
                        if cls.line_no <= line_no <= cls.end_line:
                            target_entity = cls
                            break

            # Generate summary
            if target_entity:
                summary = self._generate_entity_summary(target_entity, imports)
            else:
                summary = self._generate_file_summary(file_path, len(functions), len(classes))

            # Get impact analysis
            impact = self.dependency_resolver.get_impact(file_path)

            # Select relevant context
            py_files = list(self.project_root.glob("**/*.py"))[:10]  # Limit for performance
            context = self.smart_selector.select_context(
                query=summary,
                relevant_files=py_files,
                max_lines=50,
            )

            return {
                "status": "ok",
                "file": str(file_path),
                "line": line_no,
                "summary": summary,
                "functions": [
                    {
                        "name": f.name,
                        "line": f.line_no,
                        "docstring": f.docstring,
                        "params": [p.name for p in f.parameters],
                        "complexity": f.complexity,
                    }
                    for f in functions
                ],
                "classes": [
                    {
                        "name": c.name,
                        "line": c.line_no,
                        "docstring": c.docstring,
                        "methods": [m.name for m in c.methods],
                    }
                    for c in classes
                ],
                "imports": [{"module": i.module, "name": i.name, "line": i.line_no} for i in imports],
                "affected_files": impact.get("affected_files", 0),
                "affected_file_list": impact.get("files", [])[:5],  # Top 5
                "context": {str(k): v[:200] for k, v in context.items()},  # Snippet preview
            }

        except Exception as e:
            logger.exception(f"Error explaining {file_path}: {e}")
            return {
                "status": "error",
                "file": str(file_path),
                "error": str(e),
            }

    def suggest_refactoring(self, file_path: Path) -> Dict[str, Any]:
        """Suggest refactorings for a file.
        
        Returns suggestions based on:
        - Code metrics (complexity, coupling)
        - Design patterns
        - Common smells
        """
        file_path = Path(file_path).resolve()

        try:
            functions, classes, _ = self.ast_analyzer.analyze_file(file_path)

            suggestions = []

            # Check function complexity
            for func in functions:
                if func.complexity > 5:
                    suggestions.append({
                        "type": "high_complexity",
                        "entity": func.name,
                        "line": func.line_no,
                        "message": f"Function '{func.name}' has cyclomatic complexity {func.complexity}. Consider breaking into smaller functions.",
                        "severity": "medium",
                    })

            # Check class size
            for cls in classes:
                if len(cls.methods) > 10:
                    suggestions.append({
                        "type": "large_class",
                        "entity": cls.name,
                        "line": cls.line_no,
                        "message": f"Class '{cls.name}' has {len(cls.methods)} methods. Consider splitting into smaller classes.",
                        "severity": "low",
                    })

            # Check impact
            impact = self.dependency_resolver.get_impact(file_path)
            if impact.get("affected_files", 0) > 5:
                suggestions.append({
                    "type": "high_coupling",
                    "entity": file_path.name,
                    "message": f"This file is imported by {impact['affected_files']} other files. Changes here affect many modules.",
                    "severity": "medium",
                })

            return {
                "status": "ok",
                "file": str(file_path),
                "suggestions": suggestions,
                "summary": f"Found {len(suggestions)} potential refactorings",
            }

        except Exception as e:
            logger.exception(f"Error suggesting refactorings for {file_path}: {e}")
            return {
                "status": "error",
                "file": str(file_path),
                "error": str(e),
            }

    def _generate_entity_summary(self, entity: Any, imports: list) -> str:
        """Generate summary for a function or class."""
        if hasattr(entity, "docstring") and entity.docstring:
            return entity.docstring.strip()

        entity_type = "Function" if hasattr(entity, "parameters") else "Class"
        return f"{entity_type} '{entity.name}' at line {entity.line_no}"

    def _generate_file_summary(self, file_path: Path, num_functions: int, num_classes: int) -> str:
        """Generate summary for a file."""
        return f"{file_path.name}: {num_functions} functions, {num_classes} classes"

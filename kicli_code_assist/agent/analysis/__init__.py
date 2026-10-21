"""Programming Agent - Code Analysis Module (Phase 1: Minimal).

Fast, iterative analysis components for the Programming Agent.
Started bare-bones, will be extended based on feedback.
"""

from .ast_analyzer import ASTAnalyzer, FunctionInfo, ClassInfo, ImportInfo
from .dependency_resolver import DependencyResolver, DependencyGraph
from .project_analyzer import ProjectAnalysisService, ProjectMetadata
from .semantic_indexer import SemanticIndexer
from .smart_selector import SmartSelector

__all__ = [
    "ASTAnalyzer",
    "FunctionInfo",
    "ClassInfo",
    "ImportInfo",
    "DependencyResolver",
    "DependencyGraph",
    "ProjectAnalysisService",
    "ProjectMetadata",
    "SemanticIndexer",
    "SmartSelector",
]

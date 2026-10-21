"""Multi-step reasoning agent with thinking process visualization."""

from __future__ import annotations

import time
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, List, Dict, Any
from enum import Enum

from kicli_code_assist.agent.analysis import ASTAnalyzer
from kicli_code_assist.agent.analysis.dependency_resolver import DependencyResolver


class ThinkingStatus(str, Enum):
    """Thinking step status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class ThinkingStep:
    """Individual thinking step."""
    step: int
    title: str
    content: str
    duration_ms: int = 0
    status: ThinkingStatus = ThinkingStatus.PENDING


@dataclass
class ReasoningResult:
    """Result of reasoning process."""
    status: str = "ok"
    request_id: str = ""
    file: str = ""
    query: str = ""
    thinking: List[ThinkingStep] = field(default_factory=list)
    conclusion: str = ""
    confidence: float = 0.0
    total_duration_ms: int = 0
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict, handling enums."""
        result = asdict(self)
        # Convert enum values to strings
        for step in result.get("thinking", []):
            if isinstance(step.get("status"), ThinkingStatus):
                step["status"] = step["status"].value
        return result


class ReasoningAgent:
    """Multi-step reasoning with thinking process visualization."""

    def __init__(self, project_root: Path):
        """Initialize reasoning agent."""
        self.project_root = project_root
        self.ast_analyzer = ASTAnalyzer()

    async def reason_about_code(
        self,
        file_path: Path,
        query: str = "How can this code be improved?",
        request_id: str = "",
    ) -> ReasoningResult:
        """
        Multi-step reasoning about code with thinking visualization.
        
        Args:
            file_path: Path to code file
            query: Question to reason about
            request_id: Request ID for tracking
            
        Returns:
            ReasoningResult with thinking steps and conclusion
        """
        result = ReasoningResult(
            request_id=request_id,
            file=str(file_path),
            query=query,
        )

        start_time = time.time()

        try:
            # Ensure file exists
            if not file_path.exists():
                result.status = "error"
                result.error = f"File not found: {file_path}"
                return result

            content = file_path.read_text(errors="replace")

            # Step 1: Analyze Code Structure
            result.thinking.append(
                ThinkingStep(
                    step=1,
                    title="Analyze Code Structure",
                    content="Parsing AST and extracting functions, classes, complexity metrics...",
                    status=ThinkingStatus.RUNNING,
                )
            )
            step1_start = time.time()

            analysis = self.ast_analyzer.analyze_file(file_path)
            # analyze_file returns (functions, classes, imports) tuple
            if isinstance(analysis, tuple):
                functions_info, classes_info, imports_info = analysis
                functions = [f.__dict__ if hasattr(f, '__dict__') else f for f in functions_info]
                classes = [c.__dict__ if hasattr(c, '__dict__') else c for c in classes_info]
            else:
                functions = analysis.get("functions", [])
                classes = analysis.get("classes", [])

            result.thinking[0].duration_ms = int((time.time() - step1_start) * 1000)
            result.thinking[0].status = ThinkingStatus.COMPLETE
            result.thinking[0].content = (
                f"Found {len(functions)} functions and {len(classes)} classes. "
                f"Average complexity: {sum(f.get('complexity', 0) for f in functions) / max(len(functions), 1):.1f}"
            )

            # Step 2: Identify Patterns
            result.thinking.append(
                ThinkingStep(
                    step=2,
                    title="Identify Patterns & Issues",
                    content="Detecting code patterns, complexity issues, and anti-patterns...",
                    status=ThinkingStatus.RUNNING,
                )
            )
            step2_start = time.time()

            # Heuristic: find high-complexity functions
            high_complexity = [f for f in functions if f.get("complexity", 0) > 7]
            patterns = []
            if high_complexity:
                patterns.append(
                    f"High cyclomatic complexity in {len(high_complexity)} function(s)"
                )

            # Check for repeated patterns (simplified)
            if len(functions) > 5:
                patterns.append(
                    "File contains multiple functions - consider breaking into modules"
                )

            result.thinking[1].duration_ms = int((time.time() - step2_start) * 1000)
            result.thinking[1].status = ThinkingStatus.COMPLETE
            result.thinking[1].content = f"Identified {len(patterns)} patterns: {'. '.join(patterns)}"

            # Step 3: Analyze Dependencies
            result.thinking.append(
                ThinkingStep(
                    step=3,
                    title="Analyze Dependencies",
                    content="Checking imports and external dependencies...",
                    status=ThinkingStatus.RUNNING,
                )
            )
            step3_start = time.time()

            # Initialize DependencyResolver with project_root
            dep_resolver = DependencyResolver(self.project_root)
            deps = dep_resolver.get_file_dependents(file_path)
            
            dep_count = len(deps)

            result.thinking[2].duration_ms = int((time.time() - step3_start) * 1000)
            result.thinking[2].status = ThinkingStatus.COMPLETE
            result.thinking[2].content = f"Found {dep_count} files depending on this file"

            # Step 4: Generate Recommendation
            result.thinking.append(
                ThinkingStep(
                    step=4,
                    title="Generate Recommendation",
                    content="Synthesizing recommendations based on analysis...",
                    status=ThinkingStatus.RUNNING,
                )
            )
            step4_start = time.time()

            recommendations = []

            # Build recommendations from patterns
            if high_complexity:
                recommendations.append(
                    f"Extract {len(high_complexity)} high-complexity function(s) into smaller, focused utilities"
                )

            if len(functions) > 5:
                recommendations.append("Consider organizing code into modules/classes")

            if dep_count > 5:
                recommendations.append(f"This file is critical: {dep_count} other files depend on it")

            if not recommendations:
                recommendations.append(
                    "Code structure looks reasonable. Consider adding docstrings and type hints."
                )

            conclusion = " | ".join(recommendations)

            result.thinking[3].duration_ms = int((time.time() - step4_start) * 1000)
            result.thinking[3].status = ThinkingStatus.COMPLETE
            result.thinking[3].content = conclusion

            # Calculate confidence based on clarity of patterns
            # 1.0 = very clear recommendation, 0.6 = vague
            confidence = 0.7 + (len(high_complexity) * 0.05) + (len(patterns) * 0.05)
            result.confidence = min(confidence, 0.99)

            result.conclusion = conclusion
            result.status = "ok"

        except Exception as e:
            result.status = "error"
            result.error = str(e)
            result.thinking.append(
                ThinkingStep(
                    step=len(result.thinking) + 1,
                    title="Error",
                    content=str(e),
                    status=ThinkingStatus.ERROR,
                )
            )

        finally:
            result.total_duration_ms = int((time.time() - start_time) * 1000)

        return result

    def get_thinking_steps_json(self, result: ReasoningResult) -> str:
        """Get JSON representation of reasoning steps."""
        return json.dumps(result.to_dict(), indent=2)

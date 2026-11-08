"""
Project Understanding Pipeline: Orchestrates comprehensive project analysis.

5-Stage Processing:
1. Discovery: Project structure & documentation (ExternalProjectAnalyzer)
2. Code Structure: AST analysis & architecture (ProjectStructureAnalyzer)
3. Context Aggregation: Combine findings into LLM-friendly summary
4. LLM Analysis: Send to LLM for insights and synthesis
5. Synthesis: Generate unified understanding report
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

from kicli_code_assist.agent.external_project_analyzer import (
    ExternalProjectAnalyzer,
    ExternalProjectAnalysis,
)
from kicli_code_assist.agent.project_structure_analyzer import (
    ProjectStructureAnalyzer,
    ProjectStructure,
)

logger = logging.getLogger(__name__)


class AnalysisDepth(Enum):
    """Analysis depth levels."""
    OVERVIEW = "overview"
    DETAILED = "detailed"
    DEEP = "deep"


@dataclass
class ProjectUnderstanding:
    """Complete project understanding with all analysis stages."""
    project_root: str
    project_name: str
    discovery: Optional[ExternalProjectAnalysis] = None
    structure: Optional[ProjectStructure] = None
    aggregated_context: Optional[str] = None
    llm_insights: Optional[str] = None
    synthesis_report: Optional[str] = None
    depth: str = "detailed"


class ProjectUnderstandingPipeline:
    """
    Orchestrates 5-stage pipeline for comprehensive project understanding.
    
    Stages:
    1. Discovery: Scans documentation and project metadata
    2. Code Analysis: Extracts code structure via AST
    3. Aggregation: Combines findings into structured context
    4. LLM Analysis: Sends context to LLM for synthesis
    5. Synthesis: Generates unified understanding report
    """

    def __init__(self, project_root: str, depth: AnalysisDepth = AnalysisDepth.DETAILED):
        """Initialize pipeline for project root."""
        self.project_root = Path(project_root)
        self.project_name = self.project_root.name
        self.depth = depth
        self.understanding = ProjectUnderstanding(
            project_root=str(self.project_root),
            project_name=self.project_name,
            depth=depth.value,
        )

    def run(self) -> ProjectUnderstanding:
        """Execute full pipeline."""
        logger.info(f"Starting project understanding pipeline for {self.project_name}")
        logger.info(f"Depth level: {self.depth.value}")

        # Stage 1: Discovery
        logger.info("Stage 1: Discovering project structure and documentation...")
        self.understanding.discovery = self._stage_discovery()

        # Stage 2: Code Structure Analysis
        logger.info("Stage 2: Analyzing code structure via AST...")
        self.understanding.structure = self._stage_code_analysis()

        # Stage 3: Context Aggregation
        logger.info("Stage 3: Aggregating analysis context...")
        self.understanding.aggregated_context = self._stage_aggregation()

        # Stage 4: LLM Analysis (would call LLM here in production)
        logger.info("Stage 4: Preparing LLM analysis...")
        self.understanding.llm_insights = self._stage_llm_analysis()

        # Stage 5: Synthesis
        logger.info("Stage 5: Synthesizing unified understanding...")
        self.understanding.synthesis_report = self._stage_synthesis()

        logger.info("Pipeline complete!")
        return self.understanding

    def _stage_discovery(self) -> Optional[ExternalProjectAnalysis]:
        """Stage 1: Discover project documentation and goals."""
        try:
            analyzer = ExternalProjectAnalyzer(str(self.project_root))
            discovery = analyzer.analyze()
            logger.info(f"Discovered {len(discovery.goals)} goals, {len(discovery.doc_files)} doc files")
            return discovery
        except Exception as e:
            logger.error(f"Discovery failed: {e}")
            return None

    def _stage_code_analysis(self) -> Optional[ProjectStructure]:
        """Stage 2: Analyze code structure using AST."""
        try:
            analyzer = ProjectStructureAnalyzer(str(self.project_root))
            structure = analyzer.analyze()
            logger.info(
                f"Analyzed {len(structure.modules)} modules, {structure.total_loc} LOC, "
                f"{len(structure.external_dependencies)} external deps"
            )
            return structure
        except Exception as e:
            logger.error(f"Code analysis failed: {e}")
            return None

    def _stage_aggregation(self) -> Optional[str]:
        """Stage 3: Aggregate findings into structured context."""
        if not self.understanding.discovery or not self.understanding.structure:
            logger.warning("Skipping aggregation: missing discovery or structure")
            return None

        try:
            discovery = self.understanding.discovery
            structure = self.understanding.structure

            # Build aggregated context
            context_parts = []

            # Project overview
            context_parts.append(f"# {structure.project_name.upper()} - Project Context\n")
            context_parts.append(f"Location: {discovery.project_root}\n")

            # Code metrics
            context_parts.append(f"## Code Metrics")
            context_parts.append(f"- Total Modules: {len(structure.modules)}")
            context_parts.append(f"- Total Lines of Code: {structure.total_loc}")
            context_parts.append(f"- External Dependencies: {len(structure.external_dependencies)}")
            context_parts.append(f"- Key Classes: {len(structure.key_abstractions)}")
            context_parts.append("")

            # Project goals
            if discovery.goals:
                context_parts.append(f"## Project Goals/Phases")
                for goal in discovery.goals[:5]:  # Top 5 for brevity
                    context_parts.append(f"- **{goal.title}** ({goal.phase}): {goal.description}")
                context_parts.append("")

            # Architecture
            if structure.architectural_patterns:
                context_parts.append(f"## Architectural Patterns")
                for pattern in structure.architectural_patterns:
                    context_parts.append(f"- {pattern}")
                context_parts.append("")

            # Key abstractions
            if structure.key_abstractions:
                context_parts.append(f"## Key Abstractions (Classes/Modules)")
                for abstraction in structure.key_abstractions[:12]:
                    context_parts.append(f"- {abstraction}")
                context_parts.append("")

            # Module overview
            context_parts.append(f"## Module Structure")
            for module in structure.modules[:10]:
                if module.classes or module.functions:
                    context_parts.append(
                        f"- **{module.name}**: {len(module.classes)} classes, {len(module.functions)} functions"
                    )
            context_parts.append("")

            # Dependencies
            if structure.external_dependencies:
                context_parts.append(f"## External Dependencies")
                deps_list = sorted(list(structure.external_dependencies))[:10]
                for dep in deps_list:
                    context_parts.append(f"- {dep}")
                context_parts.append("")

            # Summary from discovery
            context_parts.append(f"## Project Summary")
            context_parts.append(discovery.summary)
            context_parts.append("")

            aggregated = "\n".join(context_parts)
            logger.info(f"Aggregated context: {len(aggregated)} chars")
            return aggregated

        except Exception as e:
            logger.error(f"Aggregation failed: {e}")
            return None

    def _stage_llm_analysis(self) -> Optional[str]:
        """Stage 4: Prepare LLM analysis prompt."""
        if not self.understanding.aggregated_context:
            logger.warning("Skipping LLM analysis: missing aggregated context")
            return None

        try:
            # In full implementation, this would call LLM
            # For now, prepare the prompt structure
            prompt = f"""Analyze the following project and provide comprehensive insights across these 12 aspects:

1. **Purpose & Goals**: What is the project designed to accomplish?
2. **Core Architecture**: What is the main architectural approach?
3. **Key Abstractions**: What are the primary classes/modules and their roles?
4. **Design Patterns**: What design patterns are used?
5. **Data Flow**: How does data flow through the system?
6. **Dependencies**: What are critical dependencies and why?
7. **Complexity**: What is the overall code complexity and why?
8. **Strengths**: What are the design strengths?
9. **Potential Issues**: What architectural weaknesses or issues do you see?
10. **Maintainability**: How maintainable is the codebase?
11. **Scalability**: What scalability considerations exist?
12. **Recommendations**: What improvements would you suggest?

Project Context:
{self.understanding.aggregated_context}

Provide a detailed, structured analysis covering all 12 aspects. Each aspect should be 2-3 sentences."""

            logger.info(f"LLM analysis prompt prepared: {len(prompt)} chars")
            return prompt

        except Exception as e:
            logger.error(f"LLM analysis preparation failed: {e}")
            return None

    def _stage_synthesis(self) -> Optional[str]:
        """Stage 5: Synthesize final understanding report."""
        if not self.understanding.aggregated_context:
            logger.warning("Skipping synthesis: missing aggregated context")
            return None

        try:
            discovery = self.understanding.discovery
            structure = self.understanding.structure

            report_parts = []

            # Title
            report_parts.append(f"# {structure.project_name} - Comprehensive Project Understanding")
            report_parts.append("")

            # Quick summary
            report_parts.append("## Executive Summary")
            report_parts.append("")
            if discovery and discovery.summary:
                report_parts.append(discovery.summary)
            report_parts.append("")
            report_parts.append(
                f"The project comprises {len(structure.modules)} modules with {structure.total_loc} lines of code. "
                f"It follows {len(structure.architectural_patterns)} distinct architectural patterns "
                f"and depends on {len(structure.external_dependencies)} external packages."
            )
            report_parts.append("")

            # Purpose & Core Abstractions
            report_parts.append("## Purpose & Core Architecture")
            report_parts.append("")
            if structure.architectural_patterns:
                patterns_str = ", ".join(structure.architectural_patterns)
                report_parts.append(f"**Architectural Patterns**: {patterns_str}")
                report_parts.append("")

            if structure.key_abstractions:
                report_parts.append("**Key Abstractions**:")
                for abstraction in structure.key_abstractions[:12]:
                    report_parts.append(f"- {abstraction}")
                report_parts.append("")

            # Code Organization
            report_parts.append("## Code Organization")
            report_parts.append("")
            report_parts.append(f"- **Total Modules**: {len(structure.modules)}")
            report_parts.append(f"- **Total LOC**: {structure.total_loc}")
            report_parts.append(f"- **Average Module Size**: {structure.total_loc // len(structure.modules) if structure.modules else 0} LOC")
            report_parts.append("")

            # Module Breakdown
            if structure.modules:
                report_parts.append("**Module Breakdown**:")
                for module in structure.modules[:15]:
                    if module.classes or module.functions:
                        report_parts.append(
                            f"- `{module.name}`: {len(module.classes)} classes, "
                            f"{len(module.functions)} functions, {module.loc} LOC"
                        )
                report_parts.append("")

            # Dependencies
            report_parts.append("## External Dependencies")
            report_parts.append("")
            if structure.external_dependencies:
                deps_list = sorted(list(structure.external_dependencies))
                report_parts.append(f"The project uses {len(deps_list)} external packages:")
                for dep in deps_list[:10]:
                    report_parts.append(f"- {dep}")
                if len(deps_list) > 10:
                    report_parts.append(f"- ... and {len(deps_list) - 10} more")
                report_parts.append("")

            # Internal Structure
            if structure.internal_dependencies:
                report_parts.append("## Internal Dependencies")
                report_parts.append("")
                report_parts.append("Module dependency relationships:")
                for module, deps in list(structure.internal_dependencies.items())[:8]:
                    if deps:
                        report_parts.append(f"- `{module}` → {', '.join(deps)}")
                report_parts.append("")

            # Goals/Phases
            if discovery and discovery.goals:
                report_parts.append("## Project Goals & Phases")
                report_parts.append("")
                for goal in discovery.goals[:6]:
                    report_parts.append(f"### {goal.title} ({goal.phase})")
                    report_parts.append(goal.description)
                    if goal.requirements:
                        report_parts.append("**Requirements**:")
                        for req in goal.requirements:
                            report_parts.append(f"- {req}")
                    report_parts.append("")

            # Next Steps
            if discovery and discovery.next_steps:
                report_parts.append("## Recommended Next Steps")
                report_parts.append("")
                for step in discovery.next_steps[:5]:
                    report_parts.append(f"- {step}")
                report_parts.append("")

            # Analysis Metadata
            report_parts.append("## Analysis Details")
            report_parts.append("")
            report_parts.append(f"- **Project Root**: {structure.project_root}")
            report_parts.append(f"- **Analysis Depth**: {self.depth.value}")
            report_parts.append(f"- **Modules Analyzed**: {len(structure.modules)}")
            report_parts.append(f"- **Patterns Detected**: {len(structure.architectural_patterns)}")
            report_parts.append("")

            report = "\n".join(report_parts)
            logger.info(f"Synthesis complete: {len(report)} chars")
            return report

        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            return None


def create_understanding_pipeline(
    project_root: str,
    depth: AnalysisDepth = AnalysisDepth.DETAILED,
) -> ProjectUnderstandingPipeline:
    """Factory function for ProjectUnderstandingPipeline."""
    return ProjectUnderstandingPipeline(project_root, depth)

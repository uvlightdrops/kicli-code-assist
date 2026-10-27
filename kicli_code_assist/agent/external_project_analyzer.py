"""
External Project Analyzer: Autonomously explores and analyzes external projects.

Capabilities:
- Discovers documentation structure
- Reads and parses goals/phases from docs
- Extracts implementation requirements
- Returns structured analysis for agent execution
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class ProjectGoal:
    """Represents a single goal extracted from project documentation."""
    phase: str
    title: str
    description: str
    requirements: List[str]
    status: str = "pending"
    priority: int = 1


@dataclass
class ExternalProjectAnalysis:
    """Structured analysis of external project."""
    project_root: str
    project_name: str
    doc_files: List[str]
    goals: List[ProjectGoal]
    summary: str
    next_steps: List[str]


class ExternalProjectAnalyzer:
    """
    Analyzes external projects to extract goals, phases, and implementation requirements.
    Automatically discovers documentation and parses structured goals.
    """

    def __init__(self, project_root: str):
        """Initialize analyzer for external project."""
        self.project_root = Path(project_root)
        self.project_name = self.project_root.name

    def analyze(self) -> ExternalProjectAnalysis:
        """
        Perform comprehensive analysis of external project.
        Returns: ExternalProjectAnalysis with goals and next steps
        """
        # Discover docs
        doc_files = self._discover_documentation()
        
        # Extract goals from discovered docs
        goals = self._extract_goals(doc_files)
        
        # Generate summary and next steps
        summary = self._generate_summary(goals)
        next_steps = self._determine_next_steps(goals)

        return ExternalProjectAnalysis(
            project_root=str(self.project_root),
            project_name=self.project_name,
            doc_files=doc_files,
            goals=goals,
            summary=summary,
            next_steps=next_steps
        )

    def _discover_documentation(self) -> List[str]:
        """Find all markdown documentation files."""
        doc_paths = [
            self.project_root / "README.md",
            self.project_root / "doc",
            self.project_root / "docs",
        ]
        
        found_files = []
        
        # Check main README
        if (self.project_root / "README.md").exists():
            found_files.append(str(self.project_root / "README.md"))
        
        # Search doc directories
        for doc_dir in ["doc", "docs"]:
            doc_path = self.project_root / doc_dir
            if doc_path.exists() and doc_path.is_dir():
                for md_file in sorted(doc_path.glob("**/*.md")):
                    found_files.append(str(md_file))
        
        return found_files[:10]  # Limit to first 10 docs

    def _extract_goals(self, doc_files: List[str]) -> List[ProjectGoal]:
        """Parse goals from documentation files."""
        goals = []
        
        for doc_file in doc_files:
            if not os.path.exists(doc_file):
                continue
            
            with open(doc_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            # Parse Phase X patterns
            phase_goals = self._parse_phase_goals(content, doc_file)
            goals.extend(phase_goals)
        
        return goals

    def _parse_phase_goals(self, content: str, source_file: str) -> List[ProjectGoal]:
        """Extract Phase/Goal definitions from markdown content."""
        goals = []
        lines = content.split("\n")
        
        current_phase = "General"
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Detect Phase headers
            if line.startswith("## Phase") or line.startswith("# Phase"):
                current_phase = line.lstrip("#").strip()
            
            # Detect goal/objective headers
            if line.startswith("### ") or line.startswith("- [ ]") or line.startswith("- [x]"):
                title = line.lstrip("#").strip().lstrip("- []x ").strip()
                
                # Collect description from next lines
                description_lines = []
                i += 1
                while i < len(lines) and lines[i].strip() and not lines[i].startswith("#"):
                    description_lines.append(lines[i].strip())
                    i += 1
                    if len(description_lines) > 3:
                        break
                
                if title:
                    goal = ProjectGoal(
                        phase=current_phase,
                        title=title,
                        description=" ".join(description_lines)[:200],
                        requirements=[f"See {source_file}"],
                        status="pending"
                    )
                    goals.append(goal)
                continue
            
            i += 1
        
        return goals

    def _generate_summary(self, goals: List[ProjectGoal]) -> str:
        """Generate human-readable summary of project goals."""
        if not goals:
            return "No structured goals found in documentation."
        
        phases = {}
        for goal in goals:
            if goal.phase not in phases:
                phases[goal.phase] = []
            phases[goal.phase].append(goal.title)
        
        summary_lines = [f"Project: {self.project_name}"]
        summary_lines.append(f"Found {len(goals)} goals across {len(phases)} phases:")
        
        for phase, titles in sorted(phases.items()):
            summary_lines.append(f"\n{phase}:")
            for title in titles[:3]:  # Show first 3 per phase
                summary_lines.append(f"  • {title}")
            if len(titles) > 3:
                summary_lines.append(f"  ... and {len(titles)-3} more")
        
        return "\n".join(summary_lines)

    def _determine_next_steps(self, goals: List[ProjectGoal]) -> List[str]:
        """Determine prioritized next steps for agent execution."""
        steps = []
        
        # Find pending goals with highest priority
        pending = [g for g in goals if g.status == "pending"]
        pending_sorted = sorted(pending, key=lambda g: -g.priority)
        
        for goal in pending_sorted[:5]:  # First 5 pending goals
            steps.append(f"Implement: {goal.title}")
        
        if not steps:
            steps.append("Review project structure and documentation")
        
        return steps

    def get_goal_details(self, goal_title: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific goal.
        
        Searches documentation for more context about a goal.
        Returns enriched goal data with implementation hints.
        """
        # Re-analyze to get current goals
        analysis = self.analyze()
        
        # Find matching goal
        matching_goals = [g for g in analysis.goals if g.title.lower() == goal_title.lower()]
        
        if not matching_goals:
            return None
        
        goal = matching_goals[0]
        
        # Search documentation for more context
        additional_context = self._search_goal_context(goal_title, analysis.doc_files)
        
        return {
            "title": goal.title,
            "phase": goal.phase,
            "description": goal.description,
            "requirements": goal.requirements,
            "doc_files": analysis.doc_files,
            "additional_context": additional_context,
            "project_name": analysis.project_name
        }

    def _search_goal_context(self, goal_title: str, doc_files: List[str]) -> str:
        """Search documentation for additional context about a goal."""
        context_lines = []
        search_term = goal_title.lower()
        
        for doc_file in doc_files:
            if not os.path.exists(doc_file):
                continue
            
            with open(doc_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines):
                if search_term in line.lower():
                    # Found a match - capture surrounding context
                    start = max(0, i - 2)
                    end = min(len(lines), i + 5)
                    context = "".join(lines[start:end])
                    if context not in context_lines:
                        context_lines.append(context)
        
        return "\n---\n".join(context_lines[:3]) if context_lines else ""


def get_external_analyzer(project_root: str) -> ExternalProjectAnalyzer:
    """Factory function to create analyzer instance."""
    return ExternalProjectAnalyzer(project_root)

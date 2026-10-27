"""Phase 2C: ResultAggregator for intelligent synthesis of agent outputs.

Synthesizes results from parallel agents (ExecutorResult from Phase 2B) into:
1. Natural language summary (LLM-generated)
2. Tabbed results for UI (Structure, Metrics, Refactor, Dependencies)
3. Actionable next steps
4. File modifications

Design:
- Uses ki-core ProviderChain for LLM synthesis with automatic fallback
- Graceful degradation to template-based synthesis if LLM unavailable
- Type-safe data structures with 100% type hints
- Error isolation and comprehensive logging
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

try:
    from ki_core.adapters import ProviderChain
    from ki_core.core.models import ChatRequest, ChatResponse, Message, Role
except ImportError:
    ProviderChain = None
    ChatRequest = None
    ChatResponse = None
    Message = None
    Role = None

from kicli_code_assist.agent.executor import ExecutorResult

if TYPE_CHECKING:
    from ki_core.core.client import AIClient

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Types of actions that can be performed from synthesis results."""
    
    WRITE_FILE = "write_file"
    MODIFY_FILE = "modify_file"
    CREATE_DIRECTORY = "create_directory"
    ACCEPT_CHANGES = "accept_changes"
    REVIEW_DIFF = "review_diff"


@dataclass
class Action:
    """Represents an actionable item from synthesis.
    
    Actions can be file modifications, directory creation, or review steps.
    Each action includes its type, target, and optional details.
    """
    
    action_type: ActionType
    target: str  # file path or entity name
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    priority: str = "medium"  # "low", "medium", "high"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "action_type": self.action_type.value,
            "target": self.target,
            "description": self.description,
            "details": self.details,
            "priority": self.priority,
        }


@dataclass
class TabContent:
    """Content for a single tab in the UI results.
    
    Each agent's output is organized into a tab with a description
    and structured data that can be rendered in the UI.
    """
    
    title: str
    description: str
    data: Dict[str, Any]
    agent_type: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "title": self.title,
            "description": self.description,
            "data": self.data,
            "agent_type": self.agent_type,
        }


@dataclass
class AggregatedResult:
    """Complete synthesis of all agent outputs for UI rendering.
    
    Contains:
    - session_id: Session identifier for tracking
    - query: Original user query
    - summary: LLM-generated 1-2 sentence overview
    - tabs: Dict of TabContent for each agent (Structure, Metrics, etc.)
    - actions: List of recommended actions
    - next_steps: Suggested follow-up queries/actions
    - execution_time_ms: Total time for aggregation
    - synthesis_method: "llm" or "template" based on what was used
    
    Attributes:
        session_id: Session tracking identifier
        query: Original user query that triggered analysis
        summary: Natural language overview of findings
        tabs: Tabbed results organized by agent type
        actions: Actionable items extracted from results
        next_steps: Suggested follow-up analysis or queries
        execution_time_ms: Time taken to synthesize results
        synthesis_method: Whether LLM or template was used
    """
    
    session_id: str
    query: str
    summary: str
    tabs: Dict[str, TabContent] = field(default_factory=dict)
    actions: List[Action] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)
    execution_time_ms: float = 0.0
    synthesis_method: str = "template"  # "llm" or "template"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict for API responses."""
        return {
            "session_id": self.session_id,
            "query": self.query,
            "summary": self.summary,
            "tabs": {
                name: tab.to_dict() for name, tab in self.tabs.items()
            },
            "actions": [action.to_dict() for action in self.actions],
            "next_steps": self.next_steps,
            "execution_time_ms": self.execution_time_ms,
            "synthesis_method": self.synthesis_method,
        }


class ResultAggregator:
    """Synthesizes agent outputs into UI-ready aggregated results.
    
    Transforms ExecutorResult (multiple agent outputs) into:
    1. Natural language summary via LLM synthesis
    2. Organized tabs for each agent type
    3. Actionable next steps
    4. File modification recommendations
    
    Uses ki-core ProviderChain for LLM with fallback to template synthesis.
    
    Usage:
        aggregator = ResultAggregator(provider="openai")
        result = await aggregator.aggregate(
            executor_result=executor_result,
            file_path=Path("myfile.py"),
            query="Explain and optimize this function"
        )
        print(result.summary)  # LLM-generated overview
    """
    
    def __init__(
        self,
        provider: str = "openai",
        provider_chain: Optional[ProviderChain] = None,
        enable_llm: bool = True,
    ):
        """Initialize aggregator with optional LLM provider.
        
        Args:
            provider: LLM provider name ("openai" or other)
            provider_chain: Optional pre-initialized ProviderChain instance
            enable_llm: Whether to attempt LLM synthesis (vs template-only)
        """
        self.provider = provider
        self.provider_chain = provider_chain
        self.enable_llm = enable_llm and (provider_chain is not None or ProviderChain is not None)
        
        if not self.enable_llm and enable_llm:
            logger.warning(
                "LLM synthesis disabled: ki-core not available. "
                "Falling back to template-based synthesis."
            )
        
        logger.info(
            f"ResultAggregator initialized (provider={provider}, "
            f"llm={'enabled' if self.enable_llm else 'disabled'})"
        )
    
    async def aggregate(
        self,
        executor_result: ExecutorResult,
        file_path: Path,
        query: str,
    ) -> AggregatedResult:
        """Main aggregation method: synthesize all agent outputs.
        
        Flow:
        1. Extract results by agent type
        2. Generate tabs for each agent
        3. Generate LLM summary or template-based summary
        4. Extract actions and next steps
        5. Return AggregatedResult
        
        Args:
            executor_result: ExecutorResult from Phase 2B with all agent outputs
            file_path: Path to analyzed file
            query: Original user query
            
        Returns:
            AggregatedResult with synthesized findings
        """
        start_time = time.time()
        file_path = Path(file_path).resolve()
        
        logger.info(
            f"Aggregating results for query: '{query}' "
            f"on file: {file_path.name}"
        )
        
        try:
            # Step 1: Build tabs from agent results
            tabs = await self._build_tabs(executor_result)
            logger.info(f"Built {len(tabs)} tabs from agent results")
            
            # Step 2: Generate summary
            if self.enable_llm:
                summary, synthesis_method = await self._synthesize_with_llm(
                    executor_result=executor_result,
                    file_path=file_path,
                    query=query,
                    tabs=tabs,
                )
            else:
                summary, synthesis_method = await self._synthesize_with_template(
                    executor_result=executor_result,
                    query=query,
                    tabs=tabs,
                )
            
            logger.info(f"Summary synthesized using {synthesis_method}")
            
            # Step 3: Extract actions and next steps
            actions = await self._extract_actions(executor_result, tabs)
            next_steps = await self._extract_next_steps(executor_result, query)
            
            logger.info(f"Extracted {len(actions)} actions and {len(next_steps)} next steps")
            
            # Step 4: Build aggregated result
            execution_time_ms = (time.time() - start_time) * 1000
            
            result = AggregatedResult(
                session_id=executor_result.session_id or "unknown",
                query=query,
                summary=summary,
                tabs=tabs,
                actions=actions,
                next_steps=next_steps,
                execution_time_ms=execution_time_ms,
                synthesis_method=synthesis_method,
            )
            
            logger.info(
                f"Aggregation complete: {len(tabs)} tabs, "
                f"{len(actions)} actions, {len(next_steps)} next steps "
                f"({execution_time_ms:.1f}ms)"
            )
            
            return result
            
        except Exception as e:
            logger.exception(f"Error during aggregation: {e}")
            # Return minimal result on error
            execution_time_ms = (time.time() - start_time) * 1000
            return AggregatedResult(
                session_id=executor_result.session_id or "unknown",
                query=query,
                summary=f"Error during aggregation: {str(e)}",
                execution_time_ms=execution_time_ms,
                synthesis_method="error",
            )
    
    async def _build_tabs(
        self,
        executor_result: ExecutorResult,
    ) -> Dict[str, TabContent]:
        """Build organized tabs from agent results.
        
        Maps each agent type to a tab:
        - explain → Structure tab (classes, functions, imports)
        - metrics → Metrics tab (maintainability, complexity)
        - refactor → Refactor tab (recommendations, patterns)
        - dependencies → Dependencies tab (imports, relations)
        - suggest → Actions tab (file changes, modifications)
        
        Args:
            executor_result: Results from all agents
            
        Returns:
            Dict mapping agent names to TabContent
        """
        tabs: Dict[str, TabContent] = {}
        
        # Process each agent's results
        for agent_name, result in executor_result.results.items():
            if result is None:
                continue
            
            if isinstance(result, dict) and result.get("status") == "error":
                logger.warning(f"Skipping failed agent result: {agent_name}")
                continue
            
            try:
                if agent_name == "explain":
                    tabs["Structure"] = self._build_structure_tab(result)
                elif agent_name == "metrics":
                    tabs["Metrics"] = self._build_metrics_tab(result)
                elif agent_name == "refactor":
                    tabs["Refactor"] = self._build_refactor_tab(result)
                elif agent_name == "dependencies":
                    tabs["Dependencies"] = self._build_dependencies_tab(result)
                elif agent_name == "suggest":
                    # Suggest tab contains actions
                    tabs["Suggestions"] = self._build_suggestions_tab(result)
                    
            except Exception as e:
                logger.warning(
                    f"Error building tab for agent '{agent_name}': {e}"
                )
                continue
        
        return tabs
    
    def _build_structure_tab(self, result: Dict[str, Any]) -> TabContent:
        """Build Structure tab from explain agent results.
        
        Extracts and organizes code structure information.
        """
        data = {
            "classes": result.get("classes", []),
            "functions": result.get("functions", []),
            "imports": result.get("imports", []),
            "description": result.get("summary", ""),
        }
        
        return TabContent(
            title="Structure",
            description="Code structure overview",
            data=data,
            agent_type="explain",
        )
    
    def _build_metrics_tab(self, result: Dict[str, Any]) -> TabContent:
        """Build Metrics tab from metrics agent results.
        
        Extracts code quality metrics.
        """
        # Extract metrics from agent result
        maintainability_index = result.get("maintainability_index", 0)
        complexity = result.get("complexity", "UNKNOWN")
        issues = result.get("issues", [])
        improvements = result.get("improvements", [])
        
        data = {
            "maintainability_index": maintainability_index,
            "complexity": complexity,
            "issues": issues,
            "improvements": improvements,
            "overall_health": self._calculate_health_score(maintainability_index),
        }
        
        return TabContent(
            title="Metrics",
            description="Code quality and complexity analysis",
            data=data,
            agent_type="metrics",
        )
    
    def _build_refactor_tab(self, result: Dict[str, Any]) -> TabContent:
        """Build Refactor tab from refactoring agent results.
        
        Extracts refactoring recommendations.
        """
        data = {
            "recommendations": result.get("suggestions", []),
            "patterns": result.get("patterns", []),
            "priority": result.get("priority", "MEDIUM"),
            "improvement_potential": result.get("improvement_potential", 0.0),
        }
        
        return TabContent(
            title="Refactor",
            description="Refactoring recommendations and patterns",
            data=data,
            agent_type="refactor",
        )
    
    def _build_dependencies_tab(self, result: Dict[str, Any]) -> TabContent:
        """Build Dependencies tab from dependencies agent results.
        
        Extracts dependency information.
        """
        data = {
            "imports": result.get("imports", {}),
            "internals": result.get("internal_dependencies", {}),
            "externals": result.get("external_dependencies", {}),
            "dependency_graph": result.get("dependency_graph", {}),
        }
        
        return TabContent(
            title="Dependencies",
            description="Import and dependency analysis",
            data=data,
            agent_type="dependencies",
        )
    
    def _build_suggestions_tab(self, result: Dict[str, Any]) -> TabContent:
        """Build Suggestions tab from suggest agent results.
        
        Extracts file creation and modification suggestions.
        """
        data = {
            "suggested_files": result.get("suggested_files", []),
            "file_changes": result.get("file_changes", []),
            "implementation_steps": result.get("implementation_steps", []),
        }
        
        return TabContent(
            title="Suggestions",
            description="Recommended file modifications and creation",
            data=data,
            agent_type="suggest",
        )
    
    async def _synthesize_with_llm(
        self,
        executor_result: ExecutorResult,
        file_path: Path,
        query: str,
        tabs: Dict[str, TabContent],
    ) -> tuple[str, str]:
        """Generate summary using LLM synthesis.
        
        Uses ProviderChain to synthesize findings into 1-2 sentence overview
        with graceful fallback to template if LLM fails.
        
        Args:
            executor_result: Original execution result
            file_path: Analyzed file path
            query: Original user query
            tabs: Built tabs with organized results
            
        Returns:
            Tuple of (summary, "llm" or "template" on fallback)
        """
        try:
            if self.provider_chain is None:
                logger.info("No provider chain available, using template synthesis")
                return await self._synthesize_with_template(
                    executor_result, query, tabs
                )
            
            # Build synthesis prompt
            prompt = self._build_synthesis_prompt(
                executor_result=executor_result,
                file_path=file_path,
                query=query,
                tabs=tabs,
            )
            
            logger.debug(f"LLM synthesis prompt length: {len(prompt)} chars")
            
            # Create chat request
            if ChatRequest is None or Message is None or Role is None:
                logger.warning("ChatRequest/Message/Role not available, falling back to template")
                return await self._synthesize_with_template(
                    executor_result, query, tabs
                )
            
            # Build message with correct ki-core API
            message = Message(role=Role.USER, content=prompt)
            request = ChatRequest(
                messages=[message],
                temperature=0.7,
            )
            
            # Query LLM
            logger.info("Querying LLM for synthesis...")
            response = await self.provider_chain.achat(request)
            
            if response and hasattr(response, "message"):
                summary = response.message.content.strip()
                logger.info(f"LLM synthesis succeeded ({len(summary)} chars)")
                return summary, "llm"
            else:
                logger.warning("Invalid LLM response, falling back to template")
                return await self._synthesize_with_template(
                    executor_result, query, tabs
                )
                
        except Exception as e:
            logger.warning(
                f"LLM synthesis failed ({type(e).__name__}): {e}. "
                f"Falling back to template synthesis."
            )
            return await self._synthesize_with_template(
                executor_result, query, tabs
            )
    
    async def _synthesize_with_template(
        self,
        executor_result: ExecutorResult,
        query: str,
        tabs: Dict[str, TabContent],
    ) -> tuple[str, str]:
        """Generate summary using template-based synthesis.
        
        Fallback approach that constructs summary from structured results
        when LLM is unavailable.
        
        Args:
            executor_result: Original execution result
            query: Original user query
            tabs: Built tabs with organized results
            
        Returns:
            Tuple of (summary, "template")
        """
        parts = []
        
        # Add intent-based intro
        intent_type = executor_result.intent.intent_type.value
        parts.append(f"Analysis of your query ({intent_type}):")
        
        # Add tab summaries
        if "Structure" in tabs:
            struct_data = tabs["Structure"].data
            classes_count = len(struct_data.get("classes", []))
            funcs_count = len(struct_data.get("functions", []))
            parts.append(
                f"Code contains {classes_count} classes and {funcs_count} functions."
            )
        
        if "Metrics" in tabs:
            metrics_data = tabs["Metrics"].data
            health = metrics_data.get("overall_health", "Unknown")
            parts.append(f"Code health: {health}.")
        
        if "Refactor" in tabs:
            refactor_data = tabs["Refactor"].data
            recs_count = len(refactor_data.get("recommendations", []))
            priority = refactor_data.get("priority", "Medium")
            if recs_count > 0:
                parts.append(
                    f"Found {recs_count} refactoring opportunities ({priority} priority)."
                )
        
        summary = " ".join(parts)
        
        logger.info(f"Template synthesis generated {len(summary)} char summary")
        return summary, "template"
    
    def _build_synthesis_prompt(
        self,
        executor_result: ExecutorResult,
        file_path: Path,
        query: str,
        tabs: Dict[str, TabContent],
    ) -> str:
        """Build LLM synthesis prompt from all agent outputs.
        
        Constructs a detailed prompt that includes all findings for LLM to
        synthesize into a concise overview.
        
        Args:
            executor_result: Execution metadata
            file_path: Path to analyzed file
            query: Original user query
            tabs: Organized results from agents
            
        Returns:
            Formatted prompt string
        """
        prompt_parts = [
            "You are a code analysis assistant. Synthesize the following analysis results into a clear, concise 1-2 sentence summary.",
            "",
            f"File: {file_path.name}",
            f"User Query: {query}",
            f"Intent: {executor_result.intent.intent_type.value}",
            "",
            "Analysis Results:",
            "="*60,
        ]
        
        # Add tab contents to prompt
        for tab_name, tab in tabs.items():
            prompt_parts.append(f"\n{tab_name}:")
            prompt_parts.append("-" * 40)
            
            # Format tab data as JSON for clarity
            try:
                data_str = json.dumps(tab.data, indent=2, default=str)
                prompt_parts.append(data_str[:1000])  # Limit to 1000 chars per tab
            except Exception:
                prompt_parts.append(str(tab.data)[:500])
        
        prompt_parts.extend([
            "",
            "="*60,
            "",
            "Generate a concise 1-2 sentence summary that:",
            "1. Answers the user's original query",
            "2. Highlights key findings",
            "3. Notes any critical issues",
            "",
            "Summary:",
        ])
        
        return "\n".join(prompt_parts)
    
    async def _extract_actions(
        self,
        executor_result: ExecutorResult,
        tabs: Dict[str, TabContent],
    ) -> List[Action]:
        """Extract actionable items from synthesis results.
        
        Identifies recommended file modifications, creations, and other
        actions the user can take based on analysis.
        
        Args:
            executor_result: Execution result
            tabs: Organized results from agents
            
        Returns:
            List of recommended actions
        """
        actions: List[Action] = []
        
        # Extract from suggestions tab (suggest agent output)
        if "Suggestions" in tabs:
            suggestions_data = tabs["Suggestions"].data
            
            # File creation suggestions
            for suggested_file in suggestions_data.get("suggested_files", []):
                actions.append(Action(
                    action_type=ActionType.WRITE_FILE,
                    target=suggested_file.get("name", "new_file.py"),
                    description=suggested_file.get("description", "Create new file"),
                    details={
                        "content": suggested_file.get("content", ""),
                        "purpose": suggested_file.get("purpose", ""),
                    },
                    priority="high",
                ))
            
            # File modification suggestions
            for file_change in suggestions_data.get("file_changes", []):
                actions.append(Action(
                    action_type=ActionType.MODIFY_FILE,
                    target=file_change.get("file", ""),
                    description=file_change.get("change", "Modify file"),
                    details={
                        "diff": file_change.get("diff", ""),
                        "reason": file_change.get("reason", ""),
                    },
                    priority="medium",
                ))
        
        # Extract from refactor tab
        if "Refactor" in tabs:
            refactor_data = tabs["Refactor"].data
            
            # High-priority refactorings become actions
            for rec in refactor_data.get("recommendations", [])[:3]:  # Top 3
                actions.append(Action(
                    action_type=ActionType.REVIEW_DIFF,
                    target=rec.get("entity", "Code"),
                    description=rec.get("message", "Review and refactor"),
                    details=rec,
                    priority="high",
                ))
        
        return actions
    
    async def _extract_next_steps(
        self,
        executor_result: ExecutorResult,
        query: str,
    ) -> List[str]:
        """Extract suggested next steps from synthesis.
        
        Recommends follow-up analyses, queries, or actions based on findings.
        
        Args:
            executor_result: Execution result
            query: Original user query
            
        Returns:
            List of suggested next steps
        """
        next_steps: List[str] = []
        
        # Always suggest related analyses based on intent
        intent_type = executor_result.intent.intent_type.value
        
        if intent_type == "explain":
            next_steps.append("Run metrics analysis to check code quality")
            next_steps.append("Review dependencies to understand interactions")
        
        elif intent_type == "optimize":
            next_steps.append("Review refactoring recommendations")
            next_steps.append("Check performance impact with metrics")
        
        elif intent_type == "refactor":
            next_steps.append("Create unit tests before refactoring")
            next_steps.append("Review impact analysis on dependent files")
        
        elif intent_type == "review":
            next_steps.append("Check for security vulnerabilities")
            next_steps.append("Review test coverage")
        
        # Add query-specific suggestions
        if "test" in query.lower():
            next_steps.append("Review test coverage report")
        
        if "performance" in query.lower():
            next_steps.append("Run performance profiling")
            next_steps.append("Compare metrics before/after optimization")
        
        if "security" in query.lower():
            next_steps.append("Run security vulnerability scan")
            next_steps.append("Review authentication and authorization")
        
        return next_steps[:5]  # Limit to 5 suggestions
    
    def _calculate_health_score(self, maintainability_index: float) -> str:
        """Convert maintainability index to health score description.
        
        Args:
            maintainability_index: Index from 0-100
            
        Returns:
            Health score description
        """
        if maintainability_index >= 85:
            return "Excellent"
        elif maintainability_index >= 70:
            return "Good"
        elif maintainability_index >= 55:
            return "Fair"
        elif maintainability_index >= 40:
            return "Poor"
        else:
            return "Critical"

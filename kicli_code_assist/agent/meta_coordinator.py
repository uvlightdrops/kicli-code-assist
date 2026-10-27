"""Meta-coordination agent for orchestrating analysis and implementation workflows.

Phase 5.1: High-level agent orchestration

Responsibilities:
- Parse and classify developer intent
- Determine workflow type (analysis, coding, review, research)
- Select appropriate sub-agents
- Coordinate parallel execution
- Aggregate and synthesize results
- Stream progress via WebSocket
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from kicli_code_assist.agent.intent_detector import AgentIntentDetector, AgentIntent
from kicli_code_assist.agent.executor import AgentExecutor
from kicli_code_assist.agent.aggregator import ResultAggregator, AggregatedResult
from kicli_code_assist.agent.answer_generator import AnswerGenerator
from kicli_code_assist.agent.external_project_analyzer import (
    get_external_analyzer, ExternalProjectAnalysis
)


logger = logging.getLogger("kicli-web")


# ============================================================================
# Data Structures
# ============================================================================

class WorkflowType:
    """Workflow classification."""
    ANALYSIS = "analysis"  # Understand code (metrics, refactoring, dependencies)
    CODING = "coding"  # Implement changes
    REVIEW = "review"  # Code review and quality checks
    RESEARCH = "research"  # Research patterns and APIs
    HYBRID = "hybrid"  # Multi-step workflow


@dataclass
class CoordinationRequest:
    """Request to meta-coordination agent."""
    query: str
    file_path: str
    project_root: str
    scope: str = "project"  # "folder" or "project"
    session_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CoordinationResult:
    """Result from meta-coordination agent."""
    success: bool
    query: str
    intent: AgentIntent
    workflow: str  # WorkflowType
    agents_used: List[str]
    answer: str  # Conversational response
    tabs: Dict[str, Any] = field(default_factory=dict)  # Analysis tabs
    actions: List[Dict[str, Any]] = field(default_factory=list)  # Follow-up actions
    timing_ms: Dict[str, int] = field(default_factory=dict)
    error: Optional[str] = None


# ============================================================================
# Meta-Coordination Agent
# ============================================================================

class MetaCoordinationAgent:
    """Orchestrates analysis and implementation workflows.
    
    Workflow types:
    1. Analysis: Run analysis agents (metrics, refactoring, dependencies)
       Used for: "Explain this", "Show metrics", "Find issues"
    
    2. Coding: Execute coding agent with LLM
       Used for: "Implement this", "Add feature", "Fix bug"
    
    3. Review: Run review agent on changes
       Used for: "Review my code", "Quality check"
    
    4. Research: Run research agent
       Used for: "Find patterns", "Research API"
    
    5. Hybrid: Multi-step workflow
       Used for: Complex tasks requiring multiple steps
    """
    
    def __init__(self):
        """Initialize coordination agent with sub-components."""
        self.intent_detector = AgentIntentDetector()
        self.executor = None  # Lazy-initialized per request
        self.aggregator = None  # Lazy-initialized per request
        self.answer_generator = None  # Lazy-initialized per request
        
        logger.info("MetaCoordinationAgent initialized")
    
    def coordinate(self, request: CoordinationRequest) -> CoordinationResult:
        """Orchestrate a complete coordination workflow.
        
        Args:
            request: CoordinationRequest with query, file_path, etc.
            
        Returns:
            CoordinationResult with answer, tabs, and timing
        """
        timing = {}
        
        try:
            # Pre-Flight: Check if this is an external project analysis request
            external_analysis = None
            if self._is_external_project_query(request.query, request.project_root):
                logger.info(f"External project detected: {request.project_root}")
                external_analysis = self._analyze_external_project(request.project_root, request.query)
                # Enhance request context with external analysis
                request.context["external_analysis"] = external_analysis
            
            # Step 1: Intent Detection
            logger.info(f"Coordination: Detecting intent for query: {request.query[:50]}")
            intent_result = self._detect_intent(request)
            intent = intent_result["intent"]  # Now a dict with type, confidence, agents, reasoning
            timing["intent_ms"] = intent_result["timing_ms"]
            
            # Step 2: Workflow Determination
            workflow = self._determine_workflow(intent["type"])
            logger.info(f"Coordination: Determined workflow: {workflow}")
            
            # Step 3: Select Sub-Agents
            agents = self._select_agents(workflow, intent["type"])
            logger.info(f"Coordination: Selected agents: {agents}")
            
            # Step 4: Execute Selected Agents
            exec_result = self._execute_agents(
                agents, request, intent["type"]
            )
            timing.update(exec_result.get("timing", {}))
            
            # Step 5: Aggregate Results
            agg_result = self._aggregate_results(
                exec_result, request, intent["type"]
            )
            timing.update(agg_result.get("timing", {}))
            
            # Step 6: Generate Answer
            answer = self._generate_answer(
                request, intent["type"], agg_result
            )
            timing["answer_ms"] = answer.get("timing_ms", 0)
            
            # Step 7: Build Response
            # Convert external_analysis back to CoordinationResult format
            result = CoordinationResult(
                success=True,
                query=request.query,
                intent=intent,
                workflow=workflow,
                agents_used=agents,
                answer=answer.get("answer", ""),
                tabs=agg_result.get("tabs", {}),
                actions=self._determine_actions(workflow, intent["type"]),
                timing_ms=timing
            )
            
            logger.info(f"Coordination complete: {workflow} with {len(agents)} agents")
            return result
            
        except Exception as e:
            logger.error(f"Coordination failed: {e}", exc_info=True)
            # Return fallback response with simple intent dict
            fallback_intent = {
                "type": "error",
                "confidence": 0.0,
                "agents": ["error_handler"],
                "reasoning": str(e)
            }
            return CoordinationResult(
                success=False,
                query=request.query,
                intent=fallback_intent,
                workflow="error",
                agents_used=[],
                answer=f"Error during coordination: {str(e)}",
                error=str(e)
            )
    
    # ========================================================================
    # Workflow Stages
    # ========================================================================
    
    def _detect_intent(self, request: CoordinationRequest) -> Dict[str, Any]:
        """Step 1: Detect query intent.
        
        Uses Phase 2A intent detector to classify user intent.
        Synchronous wrapper around async detect_intent().
        """
        import time
        start = time.time()
        
        # Use keyword-based detection (synchronous fallback)
        # to avoid async/await issues in Flask route
        agent_intent = self.intent_detector._detect_intent_keywords(request.query)
        
        # Normalize to simple intent dict for easier use in coordination
        # Convert IntentType enum to string
        intent_type_str = agent_intent.intent_type.value if hasattr(agent_intent.intent_type, 'value') else str(agent_intent.intent_type)
        
        return {
            "intent": {
                "type": intent_type_str,
                "confidence": agent_intent.confidence,
                "agents": agent_intent.agents_to_run,
                "reasoning": agent_intent.reasoning
            },
            "timing_ms": int((time.time() - start) * 1000)
        }
    
    def _determine_workflow(self, intent_type: str) -> str:
        """Step 2: Determine workflow type based on intent.
        
        Maps intent types to workflows:
        - explain, suggest, metrics, analyze → analysis
        - implement, optimize, refactor → coding (future)
        - review, check → review (future)
        - research, find → research (future)
        """
        intent_to_workflow = {
            "explain": WorkflowType.ANALYSIS,
            "suggest": WorkflowType.ANALYSIS,
            "metrics": WorkflowType.ANALYSIS,
            "analyze": WorkflowType.ANALYSIS,
            "dependencies": WorkflowType.ANALYSIS,
            "structure": WorkflowType.ANALYSIS,
            
            "implement": WorkflowType.CODING,
            "optimize": WorkflowType.CODING,
            "refactor": WorkflowType.CODING,
            
            "review": WorkflowType.REVIEW,
            "check": WorkflowType.REVIEW,
            
            "research": WorkflowType.RESEARCH,
            "find": WorkflowType.RESEARCH,
        }
        
        return intent_to_workflow.get(intent_type, WorkflowType.ANALYSIS)
    
    def _select_agents(self, workflow: str, intent_type: str) -> List[str]:
        """Step 3: Select sub-agents for execution.
        
        Each workflow type selects different agents:
        - analysis: metrics, refactoring, dependencies (parallel)
        - coding: coding_agent (sequential with review)
        - review: review_agent + analysis (parallel)
        - research: research_agent
        """
        if workflow == WorkflowType.ANALYSIS:
            # Run analysis agents in parallel
            return ["metrics", "refactoring", "dependencies"]
        
        elif workflow == WorkflowType.CODING:
            # Coding agent with follow-up review
            return ["coding"]  # Review added as follow-up
        
        elif workflow == WorkflowType.REVIEW:
            # Review agent + supporting analysis
            return ["review", "metrics"]
        
        elif workflow == WorkflowType.RESEARCH:
            return ["research"]
        
        else:
            return []
    
    def _execute_agents(self, agents: List[str], request: CoordinationRequest,
                       intent_type: str) -> Dict[str, Any]:
        """Step 4: Execute selected agents.
        
        Currently uses existing AgentExecutor (Phase 2B) for analysis agents.
        Future: Will support coding, review, research agents.
        """
        # Lazy-initialize executor
        if self.executor is None:
            from kicli_code_assist.web.server_instances import get_executor
            self.executor = get_executor(Path(request.project_root))
        
        import time
        start = time.time()
        
        # Note: AgentExecutor.execute() is async, but we're in sync context.
        # For now, return minimal result - will be improved in Phase 5.2
        result = {
            "agents": agents,
            "results": {
                "analysis": f"Agents {agents} ready for execution",
                "external_context": request.context.get("external_analysis", {})
            },
            "timing": {
                "execution_ms": int((time.time() - start) * 1000)
            }
        }
        
        return result
    
    def _aggregate_results(self, exec_result: Dict[str, Any],
                          request: CoordinationRequest,
                          intent_type: str) -> Dict[str, Any]:
        """Step 5: Aggregate results from all agents.
        
        For now, pass through results with external analysis context.
        """
        import time
        start = time.time()
        
        # Simple aggregation: combine external analysis with execution results
        external_analysis = request.context.get("external_analysis", {})
        
        aggregated = {
            "summary": f"Analysis of {external_analysis.get('project_name', 'project')} complete",
            "tabs": {
                "analysis": {
                    "external_project": external_analysis,
                    "execution_results": exec_result.get("results", {})
                }
            },
            "timing": {
                "aggregation_ms": int((time.time() - start) * 1000)
            }
        }
        
        return aggregated
    
    def _generate_answer(self, request: CoordinationRequest, intent_type: str,
                        agg_result: Dict[str, Any]) -> Dict[str, Any]:
        """Step 6: Generate conversational response.
        
        Creates human-readable answer from aggregated results.
        Handles both project-overview and goal-specific queries.
        """
        import time
        start = time.time()
        
        # Extract external analysis data
        external_analysis = request.context.get("external_analysis", {})
        
        # Build answer from external project analysis
        if external_analysis:
            query_type = external_analysis.get("query_type", "project_overview")
            
            # Goal-specific analysis
            if query_type == "goal_specific" and "goal" in external_analysis:
                goal = external_analysis["goal"]
                lines = [
                    f"# Implementation Analysis: {goal.get('title', 'Goal')}",
                    f"\n**Phase:** {goal.get('phase', 'Unknown')}",
                    f"\n**Description:** {goal.get('description', 'N/A')}",
                ]
                
                # Add context from documentation
                if goal.get("additional_context"):
                    lines.append(f"\n## Documentation Context:")
                    context_preview = goal.get("additional_context", "")[:500]
                    lines.append(f"```\n{context_preview}\n```")
                
                # Add requirements
                if goal.get("requirements"):
                    lines.append(f"\n## Requirements:")
                    for req in goal.get("requirements", [])[:5]:
                        lines.append(f"- {req}")
                
                lines.append(f"\n## Implementation Steps:")
                lines.append("1. Analyze existing code structure")
                lines.append("2. Identify required modules to modify")
                lines.append("3. Create test cases")
                lines.append("4. Implement functionality")
                lines.append("5. Verify and document")
                
                answer = "\n".join(lines)
            
            # Project overview
            else:
                lines = [
                    f"# Analysis of {external_analysis.get('project_name', 'Project')}",
                    f"\n{external_analysis.get('summary', '')}",
                    "\n## Recommended Next Steps:",
                ]
                
                for step in external_analysis.get("next_steps", [])[:5]:
                    lines.append(f"- {step}")
                
                if external_analysis.get("goals"):
                    lines.append(f"\n## Implementation Goals ({len(external_analysis.get('goals', []))} total)")
                    for goal in external_analysis.get("goals", [])[:3]:
                        lines.append(f"- **{goal.get('title', '')}** ({goal.get('phase', 'Unknown')})")
                
                answer = "\n".join(lines)
        else:
            answer = f"Query: {request.query[:100]}"
        
        return {
            "answer": answer,
            "timing_ms": int((time.time() - start) * 1000)
        }
    
    def _determine_actions(self, workflow: str, intent_type: str) -> List[Dict[str, Any]]:
        """Step 7: Determine follow-up actions.
        
        Returns suggested next steps or actionable items.
        Examples:
        - "View refactoring suggestions" button
        - "Approve and implement" button for coding tasks
        - "Run tests" button after implementation
        """
        actions = []
        
        if workflow == WorkflowType.ANALYSIS:
            actions.append({
                "type": "view_details",
                "label": "View Analysis Details",
                "target": "analysis_tab"
            })
        
        elif workflow == WorkflowType.CODING:
            actions.append({
                "type": "review_changes",
                "label": "Review Changes",
                "target": "editor_tab"
            })
            actions.append({
                "type": "approve",
                "label": "Approve & Implement",
                "requires_confirmation": True
            })
        
        return actions

    # ========================================================================
    # External Project Analysis
    # ========================================================================
    
    def _is_external_project_query(self, query: str, project_root: str) -> bool:
        """Detect if query is asking to work on an external project."""
        keywords = ["load", "analyze", "read", "external", "project", "repository", "implement", "goal"]
        query_lower = query.lower()
        
        # Check if query mentions analyzing/loading a project
        has_project_keyword = any(kw in query_lower for kw in keywords)
        
        # Check if project_root differs from cwd
        cwd = Path.cwd()
        is_external = project_root != str(cwd)
        
        return has_project_keyword and is_external
    
    def _analyze_external_project(self, project_root: str, query: str = "") -> Dict[str, Any]:
        """Analyze external project structure and goals.
        
        If query mentions a specific goal, provide detailed goal info.
        """
        try:
            analyzer = get_external_analyzer(project_root)
            
            # Check if query mentions a specific goal
            query_lower = query.lower()
            
            # Look for specific goal keywords
            goal_keywords = ["help anzeigen", "infosite", "kommandos", "callback", "cli framework"]
            matched_goal = None
            for keyword in goal_keywords:
                if keyword in query_lower:
                    matched_goal = keyword
                    break
            
            # If specific goal found, get its details
            if matched_goal:
                goal_details = analyzer.get_goal_details(matched_goal.replace("\"", "").strip())
                if goal_details:
                    return {
                        "project_name": analyzer.project_name,
                        "query_type": "goal_specific",
                        "goal": goal_details,
                        "summary": f"Detailed analysis of goal: {matched_goal}"
                    }
            
            # Otherwise, do full project analysis
            analysis = analyzer.analyze()
            
            return {
                "project_name": analysis.project_name,
                "query_type": "project_overview",
                "summary": analysis.summary,
                "goals": [
                    {
                        "phase": g.phase,
                        "title": g.title,
                        "description": g.description,
                        "status": g.status
                    }
                    for g in analysis.goals
                ],
                "next_steps": analysis.next_steps,
                "doc_files": analysis.doc_files
            }
        except Exception as e:
            logger.error(f"External project analysis failed: {e}")
            return {
                "error": str(e),
                "project_name": Path(project_root).name
            }


# ============================================================================
# Singleton Access
# ============================================================================

_meta_coordinator: Optional[MetaCoordinationAgent] = None


def get_meta_coordinator() -> MetaCoordinationAgent:
    """Get or create singleton MetaCoordinationAgent instance."""
    global _meta_coordinator
    if _meta_coordinator is None:
        _meta_coordinator = MetaCoordinationAgent()
        logger.info("Initialized MetaCoordinationAgent (Phase 5.1)")
    return _meta_coordinator

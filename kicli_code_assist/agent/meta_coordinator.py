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
            # Step 1: Intent Detection
            logger.info(f"Coordination: Detecting intent for query: {request.query[:50]}")
            intent_result = self._detect_intent(request)
            intent = intent_result["intent"]
            timing["intent_ms"] = intent_result["timing_ms"]
            
            # Step 2: Workflow Determination
            workflow = self._determine_workflow(intent.type)
            logger.info(f"Coordination: Determined workflow: {workflow}")
            
            # Step 3: Select Sub-Agents
            agents = self._select_agents(workflow, intent.type)
            logger.info(f"Coordination: Selected agents: {agents}")
            
            # Step 4: Execute Selected Agents
            exec_result = self._execute_agents(
                agents, request, intent.type
            )
            timing.update(exec_result.get("timing", {}))
            
            # Step 5: Aggregate Results
            agg_result = self._aggregate_results(
                exec_result, request, intent.type
            )
            timing.update(agg_result.get("timing", {}))
            
            # Step 6: Generate Answer
            answer = self._generate_answer(
                request, intent.type, agg_result
            )
            timing["answer_ms"] = answer.get("timing_ms", 0)
            
            # Step 7: Build Response
            result = CoordinationResult(
                success=True,
                query=request.query,
                intent=intent,
                workflow=workflow,
                agents_used=agents,
                answer=answer.get("answer", ""),
                tabs=agg_result.get("tabs", {}),
                actions=self._determine_actions(workflow, intent.type),
                timing_ms=timing
            )
            
            logger.info(f"Coordination complete: {workflow} with {len(agents)} agents")
            return result
            
        except Exception as e:
            logger.error(f"Coordination failed: {e}", exc_info=True)
            return CoordinationResult(
                success=False,
                query=request.query,
                intent=AgentIntent(type="suggest", confidence=0.0),
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
        """
        import time
        start = time.time()
        
        result = self.intent_detector.detect(
            query=request.query,
            file_path=request.file_path,
            project_root=request.project_root
        )
        
        return {
            "intent": AgentIntent(
                type=result.get("type", "suggest"),
                confidence=result.get("confidence", 0.0)
            ),
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
        
        # Use existing executor for parallel execution
        result = self.executor.execute(
            query=request.query,
            file_path=request.file_path,
            intent_type=intent_type,
            project_root=request.project_root,
            scope=request.scope
        )
        
        return {
            "agents": agents,
            "results": result.get("results", {}),
            "timing": {
                "execution_ms": int((time.time() - start) * 1000)
            }
        }
    
    def _aggregate_results(self, exec_result: Dict[str, Any],
                          request: CoordinationRequest,
                          intent_type: str) -> Dict[str, Any]:
        """Step 5: Aggregate results from all agents.
        
        Uses Phase 2C aggregator to synthesize findings.
        """
        # Lazy-initialize aggregator
        if self.aggregator is None:
            from kicli_code_assist.web.server_instances import get_aggregator
            self.aggregator = get_aggregator()
        
        import time
        start = time.time()
        
        result = self.aggregator.aggregate(
            query=request.query,
            intent_type=intent_type,
            agent_results=exec_result.get("results", {}),
            agents_executed=exec_result.get("agents", [])
        )
        
        return {
            "summary": result.get("summary", ""),
            "tabs": result.get("tabs", {}),
            "timing": {
                "aggregation_ms": int((time.time() - start) * 1000)
            }
        }
    
    def _generate_answer(self, request: CoordinationRequest, intent_type: str,
                        agg_result: Dict[str, Any]) -> Dict[str, Any]:
        """Step 6: Generate conversational response.
        
        Uses Phase 2E answer generator to create detailed, human-readable answer.
        """
        # Lazy-initialize answer generator
        if self.answer_generator is None:
            from kicli_code_assist.web.server_instances import get_answer_generator
            self.answer_generator = get_answer_generator()
        
        import time
        start = time.time()
        
        answer = self.answer_generator.generate(
            query=request.query,
            file_path=request.file_path,
            project_root=request.project_root,
            intent_type=intent_type,
            agent_results=agg_result.get("tabs", {})
        )
        
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

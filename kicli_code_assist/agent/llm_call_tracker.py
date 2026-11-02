"""
Phase 5.5.2: LLM Call Tracker

Tracks every LLM API call: cost, tokens, latency, model, purpose.
Critical for cost tracking and understanding agent behavior.
"""

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pathlib import Path
import threading


class LLMModel(str, Enum):
    """Supported LLM models."""
    GPT_4O = "gpt-4o"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_35_TURBO = "gpt-3.5-turbo"
    CLAUDE_3_OPUS = "claude-3-opus"
    CLAUDE_3_SONNET = "claude-3-sonnet"
    CLAUDE_3_HAIKU = "claude-3-haiku"


class CallPurpose(str, Enum):
    """Why we called the LLM."""
    CODE_ANALYSIS = "code_analysis"
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    REFACTORING_SUGGESTION = "refactoring_suggestion"
    ERROR_DIAGNOSIS = "error_diagnosis"
    DEPENDENCY_ANALYSIS = "dependency_analysis"
    TEST_GENERATION = "test_generation"
    DOCUMENTATION = "documentation"
    REASONING = "reasoning"
    OTHER = "other"


@dataclass
class TokenUsage:
    """Token consumption for a single call."""
    input_tokens: int
    output_tokens: int
    total_tokens: int
    
    def __post_init__(self):
        """Validate token counts."""
        if self.total_tokens != self.input_tokens + self.output_tokens:
            self.total_tokens = self.input_tokens + self.output_tokens


@dataclass
class LLMCallRecord:
    """Single LLM API call."""
    call_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Identification
    agent_id: str = ""
    goal_id: str = ""
    session_id: str = ""
    
    # Call details
    model: LLMModel = LLMModel.GPT_4O
    purpose: CallPurpose = CallPurpose.OTHER
    prompt_description: str = ""
    prompt_length: int = 0
    
    # Response
    response_length: int = 0
    response_preview: str = ""  # First 500 chars
    response_complete: bool = True  # Didn't hit max_tokens
    
    # Performance
    latency_ms: int = 0  # Time from call to response
    
    # Tokens & cost
    token_usage: Optional[TokenUsage] = None
    estimated_input_cost: float = 0.0
    estimated_output_cost: float = 0.0
    estimated_total_cost: float = 0.0
    
    # Context
    context: Dict[str, Any] = field(default_factory=dict)
    
    # Outcomes
    success: bool = True
    error_message: Optional[str] = None


# Pricing as of Nov 2024 (in $/1K tokens)
PRICING_TABLE = {
    LLMModel.GPT_4O: {
        "input": 0.005,   # $5 per 1M input tokens
        "output": 0.015   # $15 per 1M output tokens
    },
    LLMModel.GPT_4_TURBO: {
        "input": 0.01,
        "output": 0.03
    },
    LLMModel.GPT_35_TURBO: {
        "input": 0.001,
        "output": 0.002
    },
    LLMModel.CLAUDE_3_OPUS: {
        "input": 0.015,
        "output": 0.075
    },
    LLMModel.CLAUDE_3_SONNET: {
        "input": 0.003,
        "output": 0.015
    },
    LLMModel.CLAUDE_3_HAIKU: {
        "input": 0.00025,
        "output": 0.00125
    }
}


@dataclass
class LLMCostSummary:
    """Aggregate cost metrics."""
    total_calls: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost: float
    average_cost_per_call: float
    most_expensive_call: Optional[LLMCallRecord]
    calls_by_purpose: Dict[CallPurpose, int] = field(default_factory=dict)
    calls_by_model: Dict[LLMModel, int] = field(default_factory=dict)
    average_latency_ms: int = 0


class LLMCallTracker:
    """
    Tracks all LLM calls for cost visibility and audit.
    
    Usage:
    ```python
    tracker = LLMCallTracker(agent_id="agent-1")
    
    # Record a call
    record = tracker.record_call(
        model=LLMModel.GPT_4O,
        purpose=CallPurpose.CODE_ANALYSIS,
        prompt="Analyze this function...",
        response="The function does...",
        token_usage=TokenUsage(input_tokens=500, output_tokens=200, total_tokens=700),
        latency_ms=1200
    )
    
    # Get summary
    summary = tracker.get_cost_summary()
    print(f"Total cost: ${summary.total_cost:.2f}")
    ```
    """
    
    def __init__(
        self,
        agent_id: str,
        output_dir: Optional[Path] = None
    ):
        """Initialize tracker."""
        self.agent_id = agent_id
        self.output_dir = Path(output_dir or "./llm_calls")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.calls: List[LLMCallRecord] = []
        self._lock = threading.RLock()
    
    def record_call(
        self,
        model: LLMModel,
        purpose: CallPurpose,
        prompt: str,
        response: str,
        token_usage: TokenUsage,
        latency_ms: int,
        goal_id: str = "",
        session_id: str = "",
        success: bool = True,
        error_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> LLMCallRecord:
        """Record an LLM API call."""
        
        # Calculate costs
        input_cost = (token_usage.input_tokens / 1000) * PRICING_TABLE[model]["input"]
        output_cost = (token_usage.output_tokens / 1000) * PRICING_TABLE[model]["output"]
        total_cost = input_cost + output_cost
        
        # Create record
        record = LLMCallRecord(
            timestamp=datetime.utcnow(),
            agent_id=self.agent_id,
            goal_id=goal_id,
            session_id=session_id,
            model=model,
            purpose=purpose,
            prompt_description=prompt[:100] + "..." if len(prompt) > 100 else prompt,
            prompt_length=len(prompt),
            response_length=len(response),
            response_preview=response[:500] + "..." if len(response) > 500 else response,
            response_complete=(
                len(response) < 4000  # Typical max for most models
            ),
            latency_ms=latency_ms,
            token_usage=token_usage,
            estimated_input_cost=input_cost,
            estimated_output_cost=output_cost,
            estimated_total_cost=total_cost,
            success=success,
            error_message=error_message,
            context=context or {}
        )
        
        with self._lock:
            self.calls.append(record)
        
        return record
    
    def get_cost_summary(self) -> LLMCostSummary:
        """Get aggregate cost metrics."""
        if not self.calls:
            return LLMCostSummary(
                total_calls=0,
                total_input_tokens=0,
                total_output_tokens=0,
                total_cost=0.0,
                average_cost_per_call=0.0,
                most_expensive_call=None
            )
        
        with self._lock:
            total_input = sum(c.token_usage.input_tokens for c in self.calls if c.token_usage)
            total_output = sum(c.token_usage.output_tokens for c in self.calls if c.token_usage)
            total_cost = sum(c.estimated_total_cost for c in self.calls)
            avg_latency = int(sum(c.latency_ms for c in self.calls) / len(self.calls))
            
            # Most expensive
            most_expensive = max(
                self.calls,
                key=lambda c: c.estimated_total_cost
            )
            
            # Aggregate by purpose
            by_purpose = {}
            for call in self.calls:
                by_purpose[call.purpose] = by_purpose.get(call.purpose, 0) + 1
            
            # Aggregate by model
            by_model = {}
            for call in self.calls:
                by_model[call.model] = by_model.get(call.model, 0) + 1
            
            return LLMCostSummary(
                total_calls=len(self.calls),
                total_input_tokens=total_input,
                total_output_tokens=total_output,
                total_cost=total_cost,
                average_cost_per_call=total_cost / len(self.calls),
                most_expensive_call=most_expensive,
                calls_by_purpose=by_purpose,
                calls_by_model=by_model,
                average_latency_ms=avg_latency
            )
    
    def get_calls_by_purpose(
        self,
        purpose: CallPurpose
    ) -> List[LLMCallRecord]:
        """Get all calls for a specific purpose."""
        with self._lock:
            return [c for c in self.calls if c.purpose == purpose]
    
    def get_calls_by_model(
        self,
        model: LLMModel
    ) -> List[LLMCallRecord]:
        """Get all calls for a specific model."""
        with self._lock:
            return [c for c in self.calls if c.model == model]
    
    def get_calls_by_session(
        self,
        session_id: str
    ) -> List[LLMCallRecord]:
        """Get all calls in a session."""
        with self._lock:
            return [c for c in self.calls if c.session_id == session_id]
    
    def save_to_file(self, filename: Optional[str] = None) -> Path:
        """Save all calls to JSON file."""
        if filename is None:
            filename = f"llm_calls_{datetime.utcnow().isoformat()}.json"
        
        filepath = self.output_dir / filename
        
        with self._lock:
            calls_dict = [asdict(c) for c in self.calls]
        
        # Convert datetime to ISO string
        for call in calls_dict:
            call["timestamp"] = call["timestamp"].isoformat()
            # token_usage is already a dict after asdict()
            # No need to call asdict() again
        
        with open(filepath, "w") as f:
            json.dump(calls_dict, f, indent=2, default=str)
        
        return filepath
    
    def generate_cost_report(self) -> str:
        """Generate human-readable cost report."""
        summary = self.get_cost_summary()
        
        report = f"""
LLM Cost Report for {self.agent_id}
{'='*50}

Summary:
  Total Calls: {summary.total_calls}
  Total Cost: ${summary.total_cost:.4f}
  Average Cost/Call: ${summary.average_cost_per_call:.6f}
  Average Latency: {summary.average_latency_ms}ms

Tokens:
  Input Tokens: {summary.total_input_tokens:,}
  Output Tokens: {summary.total_output_tokens:,}
  Total Tokens: {summary.total_input_tokens + summary.total_output_tokens:,}

By Purpose:
{self._format_by_purpose(summary.calls_by_purpose)}

By Model:
{self._format_by_model(summary.calls_by_model)}

Most Expensive Call:
  Model: {summary.most_expensive_call.model}
  Cost: ${summary.most_expensive_call.estimated_total_cost:.4f}
  Purpose: {summary.most_expensive_call.purpose}
  Latency: {summary.most_expensive_call.latency_ms}ms
  Timestamp: {summary.most_expensive_call.timestamp.isoformat()}
"""
        
        return report.strip()
    
    @staticmethod
    def _format_by_purpose(by_purpose: Dict[CallPurpose, int]) -> str:
        """Format purpose breakdown."""
        lines = []
        for purpose, count in sorted(by_purpose.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {purpose.value}: {count}")
        return "\n".join(lines) if lines else "  (none)"
    
    @staticmethod
    def _format_by_model(by_model: Dict[LLMModel, int]) -> str:
        """Format model breakdown."""
        lines = []
        for model, count in sorted(by_model.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {model.value}: {count}")
        return "\n".join(lines) if lines else "  (none)"

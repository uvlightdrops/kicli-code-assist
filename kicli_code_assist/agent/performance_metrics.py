"""
Phase 5.5.2: Performance Metrics & Observability

Tracks performance characteristics of agent execution:
- Wall-clock time by phase
- Memory usage
- Error rates
- Success metrics
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path
import json
import threading
import time
from enum import Enum


class MetricType(str, Enum):
    """Types of metrics."""
    TIMER = "timer"
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


@dataclass
class TimerMetric:
    """Wall-clock time measurement."""
    name: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[int] = None
    
    def stop(self) -> int:
        """Stop timer and return duration."""
        self.end_time = time.time()
        self.duration_ms = int((self.end_time - self.start_time) * 1000)
        return self.duration_ms


@dataclass
class CounterMetric:
    """Count occurrences."""
    name: str
    value: int = 0
    
    def increment(self, amount: int = 1) -> int:
        self.value += amount
        return self.value
    
    def decrement(self, amount: int = 1) -> int:
        self.value -= amount
        return self.value


@dataclass
class GaugeMetric:
    """Instantaneous value."""
    name: str
    value: float = 0.0
    unit: str = ""
    
    def set(self, value: float) -> float:
        self.value = value
        return self.value


@dataclass
class HistogramBucket:
    """Histogram bucket for distribution."""
    le: int  # less than or equal
    count: int


@dataclass
class HistogramMetric:
    """Distribution of values."""
    name: str
    values: List[int] = field(default_factory=list)
    buckets: List[HistogramBucket] = field(default_factory=list)
    
    def add_value(self, value: int):
        """Add value to histogram."""
        self.values.append(value)
        self._update_buckets()
    
    def _update_buckets(self):
        """Update bucket counts."""
        self.buckets = [
            HistogramBucket(le=100, count=len([v for v in self.values if v <= 100])),
            HistogramBucket(le=250, count=len([v for v in self.values if v <= 250])),
            HistogramBucket(le=500, count=len([v for v in self.values if v <= 500])),
            HistogramBucket(le=1000, count=len([v for v in self.values if v <= 1000])),
            HistogramBucket(le=2500, count=len([v for v in self.values if v <= 2500])),
            HistogramBucket(le=5000, count=len([v for v in self.values if v <= 5000])),
        ]


@dataclass
class PhaseMetrics:
    """Metrics for a single phase."""
    phase_name: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: int = 0
    success: bool = True
    error_count: int = 0
    warning_count: int = 0
    sub_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionMetrics:
    """Complete execution metrics."""
    execution_id: str
    agent_id: str
    goal_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    
    total_duration_ms: int = 0
    
    # Phase breakdown
    phases: Dict[str, PhaseMetrics] = field(default_factory=dict)
    
    # Cumulative counters
    total_errors: int = 0
    total_warnings: int = 0
    total_llm_calls: int = 0
    total_api_calls: int = 0
    
    # Custom metrics
    custom_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Results
    success: bool = False
    result_summary: str = ""


class PerformanceMetrics:
    """
    Track performance metrics during agent execution.
    
    Usage:
    ```python
    metrics = PerformanceMetrics(agent_id="agent-1", goal_id="goal-1")
    
    with metrics.phase("analysis"):
        # Do analysis work
        metrics.increment_counter("files_analyzed", 5)
        metrics.set_gauge("memory_usage_mb", 256)
    
    with metrics.timer("total_execution"):
        # Do work
        pass
    
    summary = metrics.finalize()
    print(f"Total time: {summary.total_duration_ms}ms")
    print(f"Errors: {summary.total_errors}")
    ```
    """
    
    def __init__(
        self,
        agent_id: str,
        goal_id: str,
        execution_id: Optional[str] = None
    ):
        """Initialize metrics."""
        self.execution_id = execution_id or f"{agent_id}-{datetime.utcnow().timestamp()}"
        self.agent_id = agent_id
        self.goal_id = goal_id
        
        self.started_at = datetime.utcnow()
        self.completed_at: Optional[datetime] = None
        
        self.phases: Dict[str, PhaseMetrics] = {}
        self._current_phase: Optional[str] = None
        
        self.timers: Dict[str, TimerMetric] = {}
        self.counters: Dict[str, CounterMetric] = {}
        self.gauges: Dict[str, GaugeMetric] = {}
        self.histograms: Dict[str, HistogramMetric] = {}
        
        self._lock = threading.RLock()
    
    def start_phase(self, phase_name: str) -> PhaseMetrics:
        """Start timing a phase."""
        with self._lock:
            phase = PhaseMetrics(
                phase_name=phase_name,
                started_at=datetime.utcnow()
            )
            self.phases[phase_name] = phase
            self._current_phase = phase_name
        
        return phase
    
    def end_phase(self, success: bool = True, error_count: int = 0, warning_count: int = 0):
        """End current phase."""
        if not self._current_phase:
            return
        
        with self._lock:
            phase = self.phases[self._current_phase]
            phase.completed_at = datetime.utcnow()
            phase.duration_ms = int(
                (phase.completed_at - phase.started_at).total_seconds() * 1000
            )
            phase.success = success
            phase.error_count = error_count
            phase.warning_count = warning_count
            self._current_phase = None
    
    def start_timer(self, name: str) -> TimerMetric:
        """Start a timer."""
        with self._lock:
            timer = TimerMetric(name=name, start_time=time.time())
            self.timers[name] = timer
        return timer
    
    def stop_timer(self, name: str) -> Optional[int]:
        """Stop a timer and return duration."""
        with self._lock:
            if name not in self.timers:
                return None
            return self.timers[name].stop()
    
    def increment_counter(self, name: str, amount: int = 1) -> int:
        """Increment a counter."""
        with self._lock:
            if name not in self.counters:
                self.counters[name] = CounterMetric(name=name)
            return self.counters[name].increment(amount)
    
    def set_gauge(self, name: str, value: float, unit: str = "") -> float:
        """Set a gauge value."""
        with self._lock:
            if name not in self.gauges:
                self.gauges[name] = GaugeMetric(name=name, unit=unit)
            return self.gauges[name].set(value)
    
    def record_histogram(self, name: str, value: int):
        """Add value to histogram."""
        with self._lock:
            if name not in self.histograms:
                self.histograms[name] = HistogramMetric(name=name)
            self.histograms[name].add_value(value)
    
    def record_custom_metric(self, name: str, value: Any):
        """Record custom metric."""
        with self._lock:
            self.timers[name] = value
    
    def finalize(
        self,
        success: bool = True,
        result_summary: str = ""
    ) -> ExecutionMetrics:
        """Finalize metrics and return summary."""
        self.completed_at = datetime.utcnow()
        
        total_duration = int(
            (self.completed_at - self.started_at).total_seconds() * 1000
        )
        
        total_errors = sum(p.error_count for p in self.phases.values())
        total_warnings = sum(p.warning_count for p in self.phases.values())
        
        # Build custom metrics dict
        custom_metrics = {}
        for name, timer in self.timers.items():
            custom_metrics[f"timer_{name}"] = {
                "duration_ms": timer.duration_ms,
                "type": "timer"
            }
        
        for name, counter in self.counters.items():
            custom_metrics[f"counter_{name}"] = {
                "value": counter.value,
                "type": "counter"
            }
        
        for name, gauge in self.gauges.items():
            custom_metrics[f"gauge_{name}"] = {
                "value": gauge.value,
                "unit": gauge.unit,
                "type": "gauge"
            }
        
        for name, histogram in self.histograms.items():
            custom_metrics[f"histogram_{name}"] = {
                "values": histogram.values,
                "buckets": [{"le": b.le, "count": b.count} for b in histogram.buckets],
                "type": "histogram"
            }
        
        return ExecutionMetrics(
            execution_id=self.execution_id,
            agent_id=self.agent_id,
            goal_id=self.goal_id,
            started_at=self.started_at,
            completed_at=self.completed_at,
            total_duration_ms=total_duration,
            phases=self.phases,
            total_errors=total_errors,
            total_warnings=total_warnings,
            custom_metrics=custom_metrics,
            success=success,
            result_summary=result_summary
        )
    
    def save_metrics(self, output_dir: Optional[Path] = None) -> Path:
        """Save metrics to JSON file."""
        if output_dir is None:
            output_dir = Path("./execution_metrics")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        metrics = self.finalize()
        
        # Convert to serializable format
        metrics_dict = {
            "execution_id": metrics.execution_id,
            "agent_id": metrics.agent_id,
            "goal_id": metrics.goal_id,
            "started_at": metrics.started_at.isoformat(),
            "completed_at": metrics.completed_at.isoformat() if metrics.completed_at else None,
            "total_duration_ms": metrics.total_duration_ms,
            "total_errors": metrics.total_errors,
            "total_warnings": metrics.total_warnings,
            "success": metrics.success,
            "result_summary": metrics.result_summary,
            "phases": {
                phase_name: {
                    "started_at": phase.started_at.isoformat(),
                    "completed_at": phase.completed_at.isoformat() if phase.completed_at else None,
                    "duration_ms": phase.duration_ms,
                    "success": phase.success,
                    "error_count": phase.error_count,
                    "warning_count": phase.warning_count,
                    "sub_metrics": phase.sub_metrics
                }
                for phase_name, phase in metrics.phases.items()
            },
            "custom_metrics": metrics.custom_metrics
        }
        
        filepath = output_dir / f"{metrics.execution_id}.json"
        
        with open(filepath, "w") as f:
            json.dump(metrics_dict, f, indent=2, default=str)
        
        return filepath
    
    def generate_report(self) -> str:
        """Generate human-readable performance report."""
        metrics = self.finalize()
        
        report = f"""
Execution Metrics Report
{'='*60}

Execution ID: {metrics.execution_id}
Agent: {metrics.agent_id}
Goal: {metrics.goal_id}

Timeline:
  Started: {metrics.started_at.isoformat()}
  Completed: {metrics.completed_at.isoformat() if metrics.completed_at else 'N/A'}
  Total Duration: {metrics.total_duration_ms}ms

Status:
  Success: {metrics.success}
  Errors: {metrics.total_errors}
  Warnings: {metrics.total_warnings}

Phase Breakdown:
"""
        
        for phase_name, phase in sorted(metrics.phases.items()):
            report += f"""
  {phase_name}:
    Duration: {phase.duration_ms}ms
    Status: {'✅ Success' if phase.success else '❌ Failed'}
    Errors: {phase.error_count}
    Warnings: {phase.warning_count}
"""
        
        if metrics.custom_metrics:
            report += "\nCustom Metrics:\n"
            for key, value in metrics.custom_metrics.items():
                if isinstance(value, dict):
                    report += f"  {key}: {value}\n"
                else:
                    report += f"  {key}: {value}\n"
        
        report += f"\nSummary: {metrics.result_summary}\n"
        
        return report

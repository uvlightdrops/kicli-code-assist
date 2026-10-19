"""Comprehensive logging and metrics tracking for LLM operations.

Provides observability into:
- API call patterns (provider, model, timestamp, status)
- Latency metrics (request time, token processing time, queue time)
- Token usage (prompt tokens, completion tokens, total cost estimation)
- Error tracking (error type, count, recovery actions)
- Performance baseline (P50, P95, P99 latencies by provider)

Metrics are written to structured log format (JSON lines or CSV) for analysis.
"""

import logging
import time
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
from enum import Enum


class ProviderType(str, Enum):
    """LLM provider types."""
    OPENAI = "openai"
    OLLAMA = "ollama"
    KI = "ki"
    MOCK = "mock"


class RequestStatus(str, Enum):
    """LLM request status outcomes."""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    RETRY = "retry"


@dataclass
class TokenMetrics:
    """Token usage tracking for a single request."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def estimated_cost_usd(self, provider: ProviderType, model: str) -> float:
        """Estimate API cost in USD based on token usage.
        
        Rates (2024 pricing, subject to change):
        - OpenAI GPT-4o: $0.005 input, $0.015 output per 1K tokens
        - OpenAI GPT-4o-mini: $0.00015 input, $0.0006 output per 1K tokens
        - Ollama: $0.00 (local, no API cost)
        - KI: $0.00 (internal, no API cost)
        """
        if provider == ProviderType.OPENAI:
            if "4o-mini" in model:
                return (self.prompt_tokens * 0.00015 + 
                       self.completion_tokens * 0.0006) / 1000
            else:  # GPT-4o or other
                return (self.prompt_tokens * 0.005 + 
                       self.completion_tokens * 0.015) / 1000
        else:
            return 0.0  # Ollama, KI, Mock have no cost


@dataclass
class LatencyMetrics:
    """Request latency breakdown."""
    total_ms: float = 0.0  # Total request time
    queue_ms: float = 0.0  # Time waiting in queue
    processing_ms: float = 0.0  # Provider processing time
    streaming_ms: float = 0.0  # Token streaming time


@dataclass
class APICallRecord:
    """Single API call metrics record."""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    provider: ProviderType = ProviderType.MOCK
    model: str = ""
    request_id: str = ""
    status: RequestStatus = RequestStatus.SUCCESS
    
    # Request details
    message_count: int = 0
    system_prompt_chars: int = 0
    
    # Token metrics
    tokens: TokenMetrics = field(default_factory=TokenMetrics)
    
    # Latency breakdown
    latency: LatencyMetrics = field(default_factory=LatencyMetrics)
    
    # Error tracking
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    
    # User action
    cancelled_by_user: bool = False
    
    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        data = asdict(self)
        # Convert enums to strings
        data["provider"] = self.provider.value
        data["status"] = self.status.value
        # Flatten nested dataclasses
        data.update({
            f"tokens_{k}": v for k, v in asdict(self.tokens).items()
        })
        data.update({
            f"latency_{k}": v for k, v in asdict(self.latency).items()
        })
        del data["tokens"]
        del data["latency"]
        return data


class MetricsCollector:
    """Collects and persists metrics from LLM operations."""

    def __init__(self, metrics_dir: Optional[Path] = None):
        """Initialize metrics collector.
        
        Args:
            metrics_dir: Directory to write metrics files (defaults to configured log dir)
        """
        if metrics_dir:
            self.metrics_dir = Path(metrics_dir)
        else:
            from kicli_code_assist.app_config import AppConfig
            config = AppConfig.from_env()
            if config.kicli_log_dir:
                self.metrics_dir = Path(config.kicli_log_dir)
            else:
                # Default: ~/dev_data/kicli-code-assist/log
                default_data_dir = Path.home() / "dev_data" / "kicli-code-assist"
                self.metrics_dir = default_data_dir / "log"
        
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger("kicli.metrics")
        self.records: List[APICallRecord] = []
        
        # Running statistics
        self.stats = {
            "total_calls": 0,
            "success_calls": 0,
            "error_calls": 0,
            "cancelled_calls": 0,
            "total_tokens": 0,
            "total_cost_usd": 0.0,
            "latencies_ms": [],  # For P50, P95, P99 calculation
        }

    def record_call(self, call: APICallRecord) -> None:
        """Record an API call and update running statistics.
        
        Args:
            call: APICallRecord with metrics
        """
        self.records.append(call)
        self.stats["total_calls"] += 1
        
        # Update stats by status
        if call.status == RequestStatus.SUCCESS:
            self.stats["success_calls"] += 1
        elif call.status == RequestStatus.ERROR:
            self.stats["error_calls"] += 1
        elif call.status == RequestStatus.CANCELLED:
            self.stats["cancelled_calls"] += 1
        
        # Token and cost tracking
        self.stats["total_tokens"] += call.tokens.total_tokens
        cost = call.tokens.estimated_cost_usd(call.provider, call.model)
        self.stats["total_cost_usd"] += cost
        
        # Latency tracking
        if call.latency.total_ms > 0:
            self.stats["latencies_ms"].append(call.latency.total_ms)
        
        # Log the call
        self._log_call(call)

    def _log_call(self, call: APICallRecord) -> None:
        """Write call record to metrics log (JSON lines format)."""
        metrics_file = self.metrics_dir / "kicli-metrics.jsonl"
        
        try:
            with open(metrics_file, "a") as f:
                f.write(json.dumps(call.to_dict()) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to write metrics: {e}")

    def get_percentile(self, percentile: float) -> float:
        """Calculate latency percentile.
        
        Args:
            percentile: 50, 95, or 99 for P50, P95, P99
            
        Returns:
            Latency in milliseconds
        """
        if not self.stats["latencies_ms"]:
            return 0.0
        
        sorted_latencies = sorted(self.stats["latencies_ms"])
        idx = int(len(sorted_latencies) * (percentile / 100.0))
        return sorted_latencies[min(idx, len(sorted_latencies) - 1)]

    def get_summary(self) -> Dict:
        """Get summary statistics.
        
        Returns:
            Dict with call counts, token totals, costs, latency percentiles
        """
        return {
            "total_calls": self.stats["total_calls"],
            "success_calls": self.stats["success_calls"],
            "error_calls": self.stats["error_calls"],
            "cancelled_calls": self.stats["cancelled_calls"],
            "success_rate": (
                self.stats["success_calls"] / self.stats["total_calls"]
                if self.stats["total_calls"] > 0 else 0.0
            ),
            "total_tokens": self.stats["total_tokens"],
            "total_cost_usd": round(self.stats["total_cost_usd"], 4),
            "latency_p50_ms": round(self.get_percentile(50), 2),
            "latency_p95_ms": round(self.get_percentile(95), 2),
            "latency_p99_ms": round(self.get_percentile(99), 2),
        }

    def export_csv(self) -> str:
        """Export metrics as CSV format.
        
        Returns:
            CSV-formatted string
        """
        if not self.records:
            return ""
        
        # CSV header
        first_record = self.records[0].to_dict()
        headers = list(first_record.keys())
        csv_lines = [",".join(headers)]
        
        # CSV rows
        for record in self.records:
            row_dict = record.to_dict()
            values = [str(row_dict.get(h, "")) for h in headers]
            csv_lines.append(",".join(values))
        
        return "\n".join(csv_lines)


# Global metrics collector instance
_collector: Optional[MetricsCollector] = None


def get_metrics_collector(metrics_dir: Optional[Path] = None) -> MetricsCollector:
    """Get or create global metrics collector.
    
    Args:
        metrics_dir: Optional metrics directory override
        
    Returns:
        MetricsCollector instance
    """
    global _collector
    if _collector is None:
        _collector = MetricsCollector(metrics_dir)
    return _collector


# Example usage:
# >>> from kicli_code_assist.metrics import (
# ...     get_metrics_collector, APICallRecord, TokenMetrics, 
# ...     LatencyMetrics, ProviderType, RequestStatus
# ... )
# >>> collector = get_metrics_collector()
# >>> record = APICallRecord(
# ...     provider=ProviderType.OPENAI,
# ...     model="gpt-4o-mini",
# ...     request_id="req-123",
# ...     status=RequestStatus.SUCCESS,
# ...     message_count=5,
# ...     tokens=TokenMetrics(prompt_tokens=150, completion_tokens=200, total_tokens=350),
# ...     latency=LatencyMetrics(total_ms=2500, processing_ms=2400),
# ... )
# >>> collector.record_call(record)
# >>> print(collector.get_summary())
# {'total_calls': 1, 'success_calls': 1, ..., 'total_cost_usd': 0.0045}

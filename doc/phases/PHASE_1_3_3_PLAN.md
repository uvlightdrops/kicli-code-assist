---
title: 3 3 Plan
project: kicli-code-assist
scope:
- phases
purpose: Document phase progress and strategy
created: '2026-11-06'
updated: '2026-11-07'
status: active
semantic_blocks:
- block-1
- block-2
- block-3
- block-4
- block-5
- block-6
- block-7
- block-8
---

# Phase 1.3.3: Performance Optimization & Streaming

**Objective:** Optimize TUI for large files, high-frequency updates, and real-time streaming responses.

**Est. LOC:** 1,200 production + 600 test  
**Est. Duration:** 4-6 hours  
**Dependencies:** Phase 1.3.2 (complete)

## Goals [block-goals]

1. ✅ Adaptive token buffering for WebSocket streams
2. ✅ Response caching (10MB per response)
3. ✅ Virtual scrolling for RichLog (large outputs)
4. ✅ Memory profiling and leak detection
5. ✅ Performance benchmarks (100/500/1000/5000 tokens)

## Sub-Phases [block-sub-phases]

### 1.3.3.1: Adaptive Token Buffering (200 LOC)

**Problem:** Streaming responses can overflow the RichLog widget if tokens arrive faster than rendering.

**Solution:**
- Implement TokenBuffer class with adaptive batching
- Monitor render queue depth and adjust batch size dynamically
- Min batch: 50 tokens, Max batch: 500 tokens
- Backpressure: Slow down consumption if queue depth > 80%

**Implementation:**
```python
# kicli_code_assist/ui/streaming.py - NEW

class TokenBuffer:
    def __init__(self, min_batch=50, max_batch=500):
        self.buffer = []
        self.min_batch = min_batch
        self.max_batch = max_batch
        self.queue_depth = 0
        
    def add_token(self, token: str) -> Optional[str]:
        """Add token, return batch if ready."""
        self.buffer.append(token)
        if len(self.buffer) >= self._current_batch_size():
            return self.flush()
        return None
    
    def _current_batch_size(self) -> int:
        """Adaptive batch size based on queue pressure."""
        if self.queue_depth > 0.8:  # 80% full
            return self.min_batch
        elif self.queue_depth > 0.5:  # 50% full
            return int((self.min_batch + self.max_batch) / 2)
        else:
            return self.max_batch
```

**Tests:**
- add_token() batching behavior
- Adaptive batch size adjustment
- Flush on buffer overflow
- Backpressure handling

### 1.3.3.2: Response Caching (150 LOC)

**Problem:** Large responses are re-rendered on every update.

**Solution:**
- Implement ResponseCache with 10MB limit per response
- Cache response by (file_path, agent_type) key
- TTL: 5 minutes per cache entry
- LRU eviction when limit exceeded

**Implementation:**
```python
# kicli_code_assist/ui/response_cache.py - NEW

from functools import lru_cache
from datetime import datetime, timedelta

class ResponseCache:
    def __init__(self, max_size_mb=10):
        self.cache = {}
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.current_size = 0
        self.ttl = timedelta(minutes=5)
        
    def get(self, key: str) -> Optional[str]:
        """Get cached response."""
        if key not in self.cache:
            return None
        
        entry, timestamp = self.cache[key]
        if datetime.now() - timestamp > self.ttl:
            self._evict(key)
            return None
        
        return entry
    
    def set(self, key: str, value: str) -> None:
        """Cache response with size limit."""
        size = len(value.encode('utf-8'))
        
        # Evict if necessary
        while self.current_size + size > self.max_size_bytes and self.cache:
            oldest = min(self.cache.items(), key=lambda x: x[1][1])
            self._evict(oldest[0])
        
        self.cache[key] = (value, datetime.now())
        self.current_size += size
```

**Tests:**
- Cache hit/miss
- TTL expiration
- LRU eviction
- Size limit enforcement

### 1.3.3.3: Virtual Scrolling (350 LOC)

**Problem:** RichLog renders ALL content in DOM, even off-screen items.

**Solution:**
- Implement ScrollWindow for RichLog
- Only render visible rows + buffer (50 above, 50 below)
- Lazy-load content as user scrolls
- Cull off-screen renderables

**Implementation:**
```python
# kicli_code_assist/ui/virtual_scroll.py - NEW

class ScrollWindow:
    def __init__(self, total_height: int, viewport_height: int, buffer_size: int = 50):
        self.total_height = total_height
        self.viewport_height = viewport_height
        self.buffer_size = buffer_size
        self.scroll_pos = 0
        
    def get_visible_range(self) -> Tuple[int, int]:
        """Get start and end indices of visible content."""
        start = max(0, self.scroll_pos - self.buffer_size)
        end = min(self.total_height, self.scroll_pos + self.viewport_height + self.buffer_size)
        return (start, end)
    
    def on_scroll(self, delta: int) -> Tuple[int, int]:
        """Update scroll position and return new visible range."""
        self.scroll_pos = max(0, min(self.total_height - self.viewport_height, self.scroll_pos + delta))
        return self.get_visible_range()
```

**Tests:**
- Visible range calculation
- Scroll boundary conditions
- Buffer size handling
- Performance with 10k+ lines

### 1.3.3.4: Memory Profiling (200 LOC)

**Problem:** TUI can leak memory during long sessions.

**Solution:**
- Implement MemoryTracker
- Monitor heap size, number of objects
- Detect growing object lists
- Emit warnings at thresholds (100MB, 500MB, 1GB)

**Implementation:**
```python
# kicli_code_assist/ui/memory_tracker.py - NEW

import tracemalloc
import psutil

class MemoryTracker:
    def __init__(self, warn_threshold_mb: int = 100):
        self.warn_threshold = warn_threshold_mb * 1024 * 1024
        self.peak_memory = 0
        tracemalloc.start()
        
    def check_memory(self) -> Dict[str, Any]:
        """Get current memory stats."""
        process = psutil.Process()
        current = process.memory_info().rss
        self.peak_memory = max(self.peak_memory, current)
        
        return {
            'current_mb': current / 1024 / 1024,
            'peak_mb': self.peak_memory / 1024 / 1024,
            'warning': current > self.warn_threshold,
            'top_allocations': tracemalloc.take_snapshot().statistics('lineno')[:5]
        }
```

**Tests:**
- Memory tracking accuracy
- Warning thresholds
- Snapshot generation
- Cleanup verification

### 1.3.3.5: Performance Benchmarks (300 LOC)

**Problem:** No baseline for performance regression detection.

**Solution:**
- Create benchmark suite for token streaming
- Measure: latency, throughput, memory usage
- 4 test cases: 100, 500, 1000, 5000 tokens
- Compare to baseline

**Implementation:**
```python
# tests/test_performance_benchmarks.py - NEW

import time
from kicli_code_assist.ui.streaming import TokenBuffer

def benchmark_token_buffer():
    """Benchmark token buffering performance."""
    buffer = TokenBuffer()
    
    for size in [100, 500, 1000, 5000]:
        tokens = [f"token_{i}" for i in range(size)]
        
        start = time.perf_counter()
        for token in tokens:
            buffer.add_token(token)
        elapsed = time.perf_counter() - start
        
        throughput = size / elapsed
        print(f"Tokens={size}: {elapsed*1000:.2f}ms, Throughput={throughput:.0f} tokens/sec")
```

**Benchmarks:**
- TokenBuffer: > 50k tokens/sec target
- Cache hit: < 1ms lookup
- Virtual scroll: < 16ms frame time (60fps)
- Memory: < 200MB baseline + streaming data

## Testing Strategy [block-testing-strategy]

### Unit Tests (600 lines)
- TokenBuffer batching logic
- ResponseCache eviction
- ScrollWindow range calculation
- MemoryTracker thresholds

### Integration Tests (200 lines)
- Streaming with adaptive buffering
- Cache invalidation on update
- Virtual scroll with real RichLog
- Memory tracking during session

### Benchmarks (300 lines)
- 4 token stream sizes
- Measure latency, throughput, memory
- Generate baseline JSON
- CI: fail if regression > 10%

## Files to Create/Modify [block-files-to-create-modify]

| File | Type | LOC | Purpose |
|------|------|-----|---------|
| kicli_code_assist/ui/streaming.py | Modify | +200 | TokenBuffer class |
| kicli_code_assist/ui/response_cache.py | Create | 150 | ResponseCache class |
| kicli_code_assist/ui/virtual_scroll.py | Create | 350 | ScrollWindow class |
| kicli_code_assist/ui/memory_tracker.py | Create | 200 | MemoryTracker class |
| tests/test_perf_streaming.py | Create | 200 | Unit tests |
| tests/test_perf_cache.py | Create | 150 | Cache tests |
| tests/test_perf_scroll.py | Create | 150 | Virtual scroll tests |
| tests/test_performance_benchmarks.py | Create | 300 | Benchmark suite |
| doc/PERFORMANCE_OPTIMIZATION.md | Create | 100 | Performance guide |

**Total:** ~1,800 LOC (1,200 production + 600 tests)

## Verification [block-verification]

```bash
# Unit tests
pytest tests/test_perf_*.py -v

# Benchmarks
python3 tests/test_performance_benchmarks.py

# Memory profiling during real session
python3 -m memory_profiler kicli-assist tui --project ~/dev_flow/ki-core
```

## Success Criteria [block-success-criteria]

✅ Token buffering achieves > 50k tokens/sec throughput
✅ Response caching provides < 1ms lookup time
✅ Virtual scrolling maintains 60fps with 10k+ lines
✅ Memory usage stays < 200MB baseline
✅ No performance regressions vs Phase 1.3.2 baseline
✅ All benchmarks passing
✅ Memory tracker detects leaks within 5 minutes

## Next Phase [block-next-phase]

**Phase 1.3.4 - Theme Customization:**
- Dark/Light theme toggle (config-driven)
- Custom color schemes
- Font size adjustments
- UI element visibility toggle

## References [block-references]

- Textual Docs: https://textual.textualize.io/
- Rich Docs: https://rich.readthedocs.io/
- Python Memory Profiling: https://docs.python.org/3/library/tracemalloc.html

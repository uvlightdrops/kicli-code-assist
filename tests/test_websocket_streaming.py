"""
Test WebSocket client for Phase 5.5.2.I2 Real-Time Events

Demonstrates WebSocket streaming from agent execution.
"""

import sys
import time
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from kicli_code_assist.web.server import create_app


def test_websocket_streaming():
    """Test real-time WebSocket event streaming."""
    
    # Create test app
    config = {
        'stack': {
            'services': {
                'frontend': {
                    'host': '127.0.0.1',
                    'port': 5173
                }
            }
        }
    }
    
    app, socketio = create_app(config=config)
    app.config['TESTING'] = True
    
    print("=" * 70)
    print("TEST: WebSocket Real-Time Event Streaming (Phase 5.5.2.I2)")
    print("=" * 70)
    
    # Simulate execution session
    from kicli_code_assist.web.execution_manager import get_execution_manager
    manager = get_execution_manager()
    
    session = manager.create_session("Test: Analyze Python project")
    execution_id = session.execution_id
    print(f"\n✓ Created execution session: {execution_id}")
    
    # Start execution
    print("\n--- Execution Lifecycle ---")
    session.start()
    print(f"✓ Execution started")
    print(f"  Status: {session.status}")
    
    # Simulate agent decisions
    print("\n--- Emitting Agent Events ---")
    
    # Decision 1
    session.emitter.emit_decision(
        options_considered=["analyze_ast", "parse_imports", "scan_metrics"],
        option_selected="analyze_ast",
        confidence_score=0.95,
        reasoning="AST analysis provides most detailed structure"
    )
    print("✓ Emitted agent:decision event")
    
    time.sleep(0.05)
    
    # Execution event
    session.emitter.emit_execution(
        action="read_file",
        result="success",
        duration_ms=145,
        details={"file": "utils.py", "lines": 342}
    )
    print("✓ Emitted agent:execution event")
    
    time.sleep(0.05)
    
    # LLM call
    session.emitter.emit_llm_call(
        model="gpt-4o",
        purpose="code_analysis",
        input_tokens=2048,
        output_tokens=1024,
        total_tokens=3072,
        cost=0.045,
        latency_ms=2340
    )
    print("✓ Emitted agent:llm_call event")
    
    time.sleep(0.05)
    
    # Metrics update
    session.emitter.emit_metric_update(
        phase="analysis",
        metrics={
            "files_processed": 42,
            "total_lines": 8392,
            "complexity_avg": 3.2
        }
    )
    print("✓ Emitted agent:metric_update event")
    
    time.sleep(0.05)
    
    # Complete
    print("\n--- Finalizing ---")
    session.complete(
        success=True,
        duration_ms=3500,
        summary="Successfully analyzed 42 Python files"
    )
    print(f"✓ Execution completed")
    print(f"  Status: {session.status}")
    print(f"  Total events emitted: {session.event_count}")
    print(f"  Duration: {session.get_duration_ms()}ms")
    
    # Verify session
    retrieved = manager.get_session(execution_id)
    print(f"\n✓ Session retrieval: {retrieved is not None}")
    
    print("\n" + "=" * 70)
    print("✅ WebSocket streaming infrastructure test completed!")
    print("=" * 70)
    print("\nEvent Flow:")
    print("  Agent records decision/execution → Tracer records + emits WebSocket")
    print("  WebSocket event → TransparencyEventEmitter → SocketIO.emit()")
    print("  SocketIO → Connected WebSocket clients in room 'execution:{id}'")
    print("\nTUI/Frontend Integration:")
    print("  1. POST /api/agent/route → Create execution session")
    print("  2. WebSocket subscribe to 'execution:{id}'")
    print("  3. Receive real-time agent:decision, agent:execution, agent:llm_call")
    print("  4. Display reasoning/costs/progress live")


if __name__ == "__main__":
    test_websocket_streaming()

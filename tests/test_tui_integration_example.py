"""Integration test example - run once backend is available."""

import asyncio
from pathlib import Path
from kicli_code_assist.ui.tui_agent_client import TUIAgentClient


async def test_agent_integration():
    """
    Integration test: TUI ↔ Backend API
    
    Run this once backend is available:
    
        KI_STAGE=development python -m stackenv start
        python tests/test_tui_integration_example.py
    """
    client = TUIAgentClient("http://localhost:8000")
    
    # Check backend health
    print("Checking backend health...")
    is_healthy = await client.health_check()
    assert is_healthy, "Backend not running! Start with: KI_STAGE=development python -m stackenv start"
    print("✅ Backend OK")
    
    # Test project file listing
    project_path = str(Path.cwd())
    print(f"\nFetching files from {project_path}...")
    files = await client.get_project_files(project_path)
    print(f"✅ Found {len(files)} files")
    assert len(files) > 0, "No files found"
    
    # Find a Python file to analyze
    py_files = [f for f in files if f.endswith(".py")]
    assert py_files, "No Python files found in project"
    test_file = py_files[0]
    print(f"\nTesting with: {test_file}")
    
    # Read file
    content = await client.read_file(test_file)
    assert content, f"Could not read {test_file}"
    print(f"✅ Read {len(content)} characters from {test_file}")
    
    # Call agent
    print("\nCalling agent_route...")
    print("-" * 50)
    
    events = []
    async for event in client.call_agent_route(
        project_path=project_path,
        selected_file=test_file,
        user_request="Analyze this file briefly",
    ):
        events.append(event)
        
        # Print event summary
        event_type = event.get("event_type", "unknown")
        if event_type == "error":
            print(f"❌ {event.get('message')}")
        elif event_type == "reasoning_step":
            print(f"→ {event.get('step_type')}: {event.get('content')[:60]}...")
        elif event_type in ["explain_result", "metrics_result"]:
            print(f"✓ Got {event_type}")
        else:
            print(f"• {event_type}")
    
    print("-" * 50)
    print(f"\n✅ Received {len(events)} events")
    assert len(events) > 0, "No events received from agent"
    
    # Check for result event
    result_events = [e for e in events if "result" in e.get("event_type", "")]
    assert result_events, "No result events received"
    print(f"✅ Got {len(result_events)} result events")
    
    await client.close()
    print("\n✅ Integration test PASSED")


if __name__ == "__main__":
    asyncio.run(test_agent_integration())

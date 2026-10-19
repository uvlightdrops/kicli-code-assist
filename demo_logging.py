#!/usr/bin/env python3
"""
Simple demo script showing the Logging Panel in action.
This creates some log entries and displays them.
"""

import os
import sys
from pathlib import Path

# Ensure we can import from the project
sys.path.insert(0, os.path.dirname(__file__))

def create_sample_logs():
    """Create sample log entries for demo."""
    from kicli_code_assist.logging_integration import (
        get_main_logger, get_llm_logger, get_context_logger,
        get_workflow_logger, get_error_logger
    )
    
    # Ensure log directory exists
    Path('log').mkdir(exist_ok=True)
    
    # Create sample logs
    main_logger = get_main_logger()
    llm_logger = get_llm_logger()
    context_logger = get_context_logger()
    workflow_logger = get_workflow_logger()
    error_logger = get_error_logger()
    
    print("📝 Creating sample log entries...")
    
    # Main log
    main_logger.info("Application started")
    main_logger.info("Config loaded from ~/.kicli/ki.yaml")
    
    # LLM log
    llm_logger.info("LLM Provider: OpenAI (GPT-4)")
    llm_logger.info("LLM URL: https://api.openai.com/v1/chat/completions")
    llm_logger.debug("Query sent: Suggest improvements for this code...")
    llm_logger.debug("Response received: 123 tokens, 0.042s latency")
    
    # Context log
    context_logger.info("Loading file: src/app.py (2.4 KB)")
    context_logger.info("File cached: src/app.py")
    context_logger.debug("Dedup check: file already in context, using cached version")
    
    # Workflow log
    workflow_logger.info("User clicked 'Approve' button")
    workflow_logger.info("Approval: 3/5 hunks approved")
    
    # Error log
    error_logger.warning("Config validation warning: unused setting 'legacy_mode'")
    
    print("\n✅ Sample logs created in log/ directory:")
    for f in sorted(Path('log').glob('*.log')):
        size = f.stat().st_size
        print(f"  - {f.name} ({size} bytes)")
    
    return True

def show_logs():
    """Display logs in a table format."""
    logfiles = [
        ("kicli.log", "📋 Main Log"),
        ("kicli-llm.log", "🤖 LLM Queries"),
        ("kicli-context.log", "📂 File Context"),
        ("kicli-workflow.log", "⚙️  Workflow"),
        ("kicli-errors.log", "❌ Errors"),
    ]
    
    print("\n" + "="*80)
    print("LOGGING PANEL PREVIEW")
    print("="*80)
    
    for filename, label in logfiles:
        path = Path('log') / filename
        if path.exists():
            print(f"\n[TAB] {label} ({filename})")
            print(f"Path: {path.resolve()}")
            print("-" * 80)
            
            with open(path, 'r') as f:
                lines = f.readlines()[-10:]  # Last 10 lines
                for line in lines:
                    # Color coding based on level
                    if " ERROR " in line or " CRITICAL " in line:
                        line_color = "\033[91m"  # Red
                    elif " WARNING " in line:
                        line_color = "\033[93m"  # Yellow
                    elif " DEBUG " in line:
                        line_color = "\033[96m"  # Cyan
                    else:
                        line_color = "\033[92m"  # Green
                    
                    print(f"{line_color}{line}\033[0m", end='')
            print()

if __name__ == "__main__":
    if create_sample_logs():
        show_logs()
        print("\n" + "="*80)
        print("🎯 How to use the Logging Tab in the TUI:")
        print("="*80)
        print("""
1. Launch the app: kicli-assist tui
2. Press Ctrl+G to open the Logging tab (default on startup)
3. Use the dropdown to switch between 5 logfiles
4. Watch logs auto-refresh every 2 seconds
5. See color-coded messages (Red=ERROR, Yellow=WARN, Cyan=DEBUG)

Features:
✅ Config-driven log levels (via logconf.ini)
✅ Lazy initialization (files created on first log)
✅ Thread-safe logging (RLock)
✅ Per-module logfiles (kicli, llm, context, workflow, errors)
✅ 1:1 display from logfile (not reformatted)
✅ Auto-scrolls to latest entries every 2 seconds
""")

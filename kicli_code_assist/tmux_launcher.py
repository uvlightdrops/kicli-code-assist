"""Launch KI Code Assistant in Tmux with split panes."""
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Optional


def launch_tmux_assistant(
    session_name: str = "ki-assist",
    config_file: Optional[str] = None
) -> None:
    """Launch KI Code Assistant in Tmux.
    
    Layout:
    ┌─────────────────────────────────────────┐
    │  Code Editor / View (40% height)        │
    ├─────────────────────────────────────────┤
    │  Chat + KI Response (30% height)        │
    ├─────────────────────────────────────────┤
    │  Input/Commands (30% height)            │
    └─────────────────────────────────────────┘
    
    Args:
        session_name: Tmux session name
        config_file: Optional config file path
    """
    
    if "TMUX" in os.environ:
        raise RuntimeError(
            "Do not run 'kicli-assist tmux' from inside an existing tmux session. "
            "Start it from a normal shell, or use 'tmux new-session -A -s <name>'."
        )

    # Kill existing session
    subprocess.run(["tmux", "kill-session", "-t", session_name], 
                   stderr=subprocess.DEVNULL)
    
    # Create new session with first pane (code view)
    subprocess.run([
        "tmux", "new-session", "-d",
        "-s", session_name,
        "-x", "200", "-y", "50",
        "-c", os.getcwd(),
    ])
    
    # Split horizontally - top pane for code (40%)
    subprocess.run([
        "tmux", "split-window", "-v",
        "-t", f"{session_name}:0.0",
        "-p", "40"
    ])
    
    # Split the bottom pane vertically (chat on left, input on right)
    subprocess.run([
        "tmux", "split-window", "-h",
        "-t", f"{session_name}:0.1",
        "-p", "50"
    ])
    
    # Pane layout:
    # 0: Code editor
    # 1: Chat display
    # 2: Input
    
    # Send commands to each pane
    
    # Pane 0: Code view (using `less` or `tail -f` for monitoring)
    subprocess.run([
        "tmux", "send-keys",
        "-t", f"{session_name}.0",
        "echo 'Code View (Pane 0) - Edit files here'",
        "Enter"
    ])
    
    # Pane 1: Chat view
    python_exe = shlex.quote(sys.executable)
    subprocess.run([
        "tmux", "send-keys",
        "-t", f"{session_name}:0.1",
        f"{python_exe} -c \"from kicli_code_assist.ui.tui_app import CodeAssistantTUI; app = CodeAssistantTUI(); app.run()\"",
        "Enter"
    ])
    
    # Pane 2: Input command
    subprocess.run([
        "tmux", "send-keys",
        "-t", f"{session_name}:0.2",
        "echo 'Commands: (y)es / (n)o / (e)dit / (q)uit'",
        "Enter"
    ])
    
    # Select pane 2 (input) as active
    subprocess.run([
        "tmux", "select-pane",
        "-t", f"{session_name}:0.2"
    ])
    
    # Attach to session
    subprocess.run(["tmux", "attach-session", "-t", session_name])


def launch_simple_tmux():
    """Simple Tmux launcher - just top/bottom split."""
    session = "ki-dev"

    if "TMUX" in os.environ:
        raise RuntimeError(
            "Do not run 'kicli-assist tmux --simple' from inside an existing tmux session. "
            "Start it from a normal shell, or attach/switch to an existing session."
        )
    
    # Kill existing
    subprocess.run(["tmux", "kill-session", "-t", session],
                   stderr=subprocess.DEVNULL)
    
    # New session
    subprocess.run([
        "tmux", "new-session", "-d",
        "-s", session,
        "-c", os.getcwd()
    ])
    
    # Split 40/60
    subprocess.run([
        "tmux", "split-window", "-v",
        "-t", f"{session}:0.0",
        "-p", "40"
    ])
    
    python_exe = shlex.quote(sys.executable)
    
    # Top: File tree / code
    subprocess.run([
        "tmux", "send-keys",
        "-t", f"{session}.0",
        "echo '📝 Code View - Use vim, nano, or ls to navigate'",
        "Enter"
    ])
    
    # Bottom: Chat/AI
    subprocess.run([
        "tmux", "send-keys",
        "-t", f"{session}:0.1",
        f"{python_exe} -m kicli_code_assist.examples.simple_chat",
        "Enter"
    ])
    
    # Select bottom pane
    subprocess.run([
        "tmux", "select-pane",
        "-t", f"{session}:0.1"
    ])
    
    # Attach
    subprocess.run(["tmux", "attach", "-t", session])


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Launch KI Code Assistant in Tmux"
    )
    parser.add_argument(
        "--simple",
        action="store_true",
        help="Use simple 2-pane layout instead of complex 3-pane"
    )
    parser.add_argument(
        "-s", "--session",
        default="ki-assist",
        help="Tmux session name"
    )
    parser.add_argument(
        "-c", "--config",
        help="Config file path"
    )
    
    args = parser.parse_args()
    
    if args.simple:
        launch_simple_tmux()
    else:
        launch_tmux_assistant(args.session, args.config)


if __name__ == "__main__":
    main()

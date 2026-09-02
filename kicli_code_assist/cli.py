def _detect_best_provider():
    """Detect best available LLM provider based on config.
    
    Priority:
    1. Ollama (if running locally)
    2. OpenAI (if API key available)
    3. Company KI (if configured)
    4. Mock (fallback for testing)
    """
    from ki_core import Config
    
    config = Config.from_env()
    
    # Check Ollama
    if config.ollama_base_url:
        try:
            import requests
            requests.head(config.ollama_base_url, timeout=2)
            return "ollama"
        except:
            pass
    
    # Check OpenAI
    if config.openai_api_key:
        return "openai"
    
    # Check Company KI
    if config.ki_api_key:
        return "ki"
    
    # Fallback to mock
    return "mock"


def main():
    """Main CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        prog="kicli-assist",
        description="KI Code Assistant - Interactive code generation and review"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # TUI command
    tui_parser = subparsers.add_parser("tui", help="Launch terminal UI")
    tui_parser.add_argument("-c", "--config", help="Config file")
    tui_parser.add_argument("--provider", help="LLM provider (auto-detect if not set)")
    
    # Tmux command
    tmux_parser = subparsers.add_parser("tmux", help="Launch in Tmux")
    tmux_parser.add_argument("--simple", action="store_true", help="Simple 2-pane layout")
    tmux_parser.add_argument("-s", "--session", default="ki-assist")
    
    # Chat command (simple)
    chat_parser = subparsers.add_parser("chat", help="Simple chat interface")
    chat_parser.add_argument("--model", help="Override model")
    chat_parser.add_argument("--provider", help="LLM provider (auto-detect if not set)")
    
    # OpenInterpreter command
    oi_parser = subparsers.add_parser("openinterpreter", help="Launch OpenInterpreter")
    oi_parser.add_argument("-y", "--auto-run", action="store_true", help="Auto-run code")
    oi_parser.add_argument("--model", help="Override model")
    
    args = parser.parse_args()
    
    if args.command == "tui":
        from kicli_code_assist.ui.textual_app import main as run_textual
        run_textual()
    
    elif args.command == "tmux":
        from kicli_code_assist.tmux_launcher import (
            launch_tmux_assistant, launch_simple_tmux
        )
        if args.simple:
            launch_simple_tmux()
        else:
            launch_tmux_assistant(args.session)
    
    elif args.command == "chat":
        from kicli_code_assist.examples.simple_chat import run_chat
        
        # Auto-detect provider if not specified
        provider = args.provider or _detect_best_provider()
        
        run_chat(model=args.model, provider=provider)
    
    elif args.command == "openinterpreter":
        from kicli_code_assist.executor.openinterpreter_provider import (
            OpenInterpreterProvider, OpenInterpreterConfig
        )
        from ki_core import Config
        
        # Use ki-core unified config
        ki_config = Config.from_env()
        
        # Create OpenInterpreter config from ki-core config
        config = OpenInterpreterConfig.from_dict({
            "base_url": ki_config.ki_base_url or ki_config.openai_base_url,
            "api_key": ki_config.ki_api_key or ki_config.openai_api_key,
            "model": args.model or ki_config.ki_model,
        })
        config.auto_run = args.auto_run
        
        # Launch
        provider = OpenInterpreterProvider(config)
        provider.start_interactive()
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

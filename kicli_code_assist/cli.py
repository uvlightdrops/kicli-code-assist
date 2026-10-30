import importlib
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List

import click
import yaml

from ki_core import ConfigManager, find_config_path


def _get_llm_provider(echo_fn: Callable[[str], None] = click.echo) -> str:
    """Get best available LLM provider using ConfigManager.

    ConfigManager.get_llm_provider() is the SINGLE SOURCE OF TRUTH for
    provider detection, consolidating logic that was previously scattered
    across multiple files (cli.py, llm_integration.py, etc.).
    """
    mgr = ConfigManager(echo_fn=echo_fn)
    return mgr.get_llm_provider()


def run_tui(config: str | None = None, provider: str | None = None) -> None:
    """Launch the terminal UI."""
    from kicli_code_assist.ui.textual_app import main as run_textual
    if provider:
        click.echo(f"Provider override: {provider}")
    run_textual()


def run_tmux(simple: bool = False, session: str = "ki-assist") -> None:
    """Launch the tmux-based layout."""
    from kicli_code_assist.tmux_launcher import launch_tmux_assistant, launch_simple_tmux
    if simple:
        launch_simple_tmux()
    else:
        launch_tmux_assistant(session)


def run_chat(model: str | None = None, provider: str | None = None) -> None:
    """Run the simple chat flow."""
    from kicli_code_assist.examples.simple_chat import run_chat as run_chat_flow
    run_chat_flow(model=model, provider=provider or _get_llm_provider())


def run_openinterpreter(auto_run: bool = False, model: str | None = None) -> None:
    """Launch OpenInterpreter mode."""
    from kicli_code_assist.app_config import AppConfig as Config
    from kicli_code_assist.executor.openinterpreter_provider import OpenInterpreterConfig, OpenInterpreterProvider

    ki_config = Config.from_env()
    config = OpenInterpreterConfig.from_dict({
        "base_url": ki_config.ki_base_url or ki_config.openai_base_url,
        "api_key": ki_config.ki_api_key or ki_config.openai_api_key,
        "model": model or ki_config.ki_model,
    })
    config.auto_run = auto_run
    provider = OpenInterpreterProvider(config)
    provider.start_interactive()


def run_doctor() -> None:
    """Display configuration diagnostics (delegates to ki-core base implementation)."""
    from ki_core.commands import run_doctor as ki_core_doctor
    
    ki_core_doctor(echo_fn=click.echo, show_config_path=False)


def run_config(subcommand: str | None = None, **kwargs: Any) -> None:
    """Config management (delegates to ki-core base implementation)."""
    from ki_core.commands import run_resolve, run_verify, run_skeleton, run_show
    
    subcommand = subcommand or "resolve"
    
    try:
        if subcommand == "resolve":
            run_resolve(echo_fn=click.echo)
        elif subcommand == "verify":
            run_verify(echo_fn=click.echo)
        elif subcommand == "skeleton":
            output_file = kwargs.get("output", "ki.yaml")
            run_skeleton(echo_fn=click.echo, output_file=output_file)
        elif subcommand == "show":
            key = kwargs.get("key")
            run_show(echo_fn=click.echo, key=key)
        else:
            click.echo(f"Unknown config subcommand: {subcommand}")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise


def run_profile(subcommand: str | None = None, **kwargs: Any) -> None:
    """Profile management (delegates to ki-core base implementation)."""
    from ki_core.commands import run_profile_list, run_profile_set, run_profile_active
    
    subcommand = subcommand or "active"
    
    try:
        if subcommand == "list":
            run_profile_list(echo_fn=click.echo)
        elif subcommand == "set":
            profile_name = kwargs.get("name", "")
            run_profile_set(echo_fn=click.echo, profile_name=profile_name)
        elif subcommand == "active":
            run_profile_active(echo_fn=click.echo)
        else:
            click.echo(f"Unknown profile subcommand: {subcommand}")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise


def run_stage(subcommand: str | None = None, **kwargs: Any) -> None:
    """Stage management (delegates to ki-core base implementation)."""
    from ki_core.commands import run_stage_list, run_stage_set, run_stage_active
    
    subcommand = subcommand or "active"
    
    try:
        if subcommand == "list":
            run_stage_list(echo_fn=click.echo)
        elif subcommand == "set":
            stage_name = kwargs.get("name", "")
            run_stage_set(echo_fn=click.echo, stage_name=stage_name)
        elif subcommand == "active":
            run_stage_active(echo_fn=click.echo)
        else:
            click.echo(f"Unknown stage subcommand: {subcommand}")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise


def run_server(subcommand: str | None = None, **kwargs: Any) -> None:
    """Server management (DEPRECATED - use 'kicli-assist server <subcommand>' instead)."""
    click.echo("❌ Error: Use 'kicli-assist server <subcommand>' instead of --subcommand", err=True)
    click.echo("Examples:")
    click.echo("  kicli-assist server status")
    click.echo("  kicli-assist server start --service backend")
    click.echo("  kicli-assist server stop --service backend")
    click.echo("  kicli-assist server restart --service backend")


# ============================================================================
# Server Management Click Group & Subcommands
# ============================================================================

@click.group()
@click.option("--project", help="Registered project root (defaults to current directory)")
@click.pass_context
def server(ctx, project):
    """Manage registered projects through their own stackctl."""
    ctx.ensure_object(dict)
    ctx.obj["server_project"] = project or str(Path.cwd().resolve())


def _stackctl_server(action, services=()):
    import json
    from ki_core.config import load_config
    from kicli_code_assist.web.stackctl_bridge import StackctlBridge, StackctlError

    try:
        manager = StackctlBridge(load_config())
        root = manager.project(click.get_current_context().obj["server_project"])
        if action == "status":
            payload = manager.status(root)
        else:
            names = manager.services(root, list(services))
            payload = manager.invoke(root, action, names, json_output=action == "logs")
        click.echo(json.dumps(payload, indent=2) if action in {"status", "logs"} else payload["output"])
    except StackctlError as exc:
        raise click.ClickException(str(exc)) from exc


@server.command()
@click.option('--verbose', '-v', is_flag=True, help='Show detailed info')
def status(verbose: bool):
    """Show live stackctl status (--verbose retained for compatibility)."""
    _stackctl_server("status")


@server.command()
@click.option('--service', '-s', multiple=True, help='Service name; omit for all')
def start(service):
    """Start project services through stackctl."""
    _stackctl_server("start", service)


@server.command()
@click.option('--service', '-s', multiple=True, help='Service name; omit for all')
def stop(service):
    """Stop project services through stackctl."""
    _stackctl_server("stop", service)


@server.command()
@click.option('--service', '-s', multiple=True, help='Service name; omit for all')
def restart(service):
    """Restart project services through stackctl."""
    _stackctl_server("restart", service)


@server.command()
@click.option('--service', '-s', multiple=True, help='Service name; omit for all')
def logs(service):
    """Read bounded project logs through stackctl."""
    _stackctl_server("logs", service)


@server.command()
@click.option('--name', '-n', required=True, help='Service name')
@click.option('--pid', '-p', type=int, required=True, help='Process ID')
@click.option('--port', type=int, help='Port number')
def register(name: str, pid: int, port: int | None):
    """Register a running service."""
    from ki_core.commands import run_server_register
    run_server_register(name, pid, port=port, echo_fn=click.echo)


@server.command()
@click.option('--name', '-n', required=True, help='Service name')
def unregister(name: str):
    """Unregister a service."""
    from ki_core.commands import run_server_unregister
    run_server_unregister(name, echo_fn=click.echo)


@server.command()
def detect_orphans():
    """Detect orphaned services."""
    from ki_core.commands import run_server_detect_orphans
    run_server_detect_orphans(echo_fn=click.echo)


@server.command()
def cleanup():
    """Clean up orphaned services."""
    from ki_core.commands import run_server_cleanup
    run_server_cleanup(echo_fn=click.echo)


@server.command()
def sync():
    """Sync registry with actual processes."""
    from ki_core.commands import run_server_sync
    run_server_sync(echo_fn=click.echo)



def _load_yaml_tree(path: str | None = None) -> Dict[str, Any]:
    """Load the YAML command tree, or fallback to the built-in default."""
    default_path = Path(__file__).with_name("cli_commands.yaml")
    yaml_path = Path(path).expanduser() if path else default_path
    if yaml_path.exists():
        with yaml_path.open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}
        if isinstance(payload, dict):
            return payload
    return {
        "name": "kicli-assist",
        "help": "KI Code Assistant - interactive code generation and review",
        "commands": [
            {
                "name": "tui",
                "help": "Launch the terminal UI",
                "callback": "kicli_code_assist.cli:run_tui",
            },
            {
                "name": "tmux",
                "help": "Launch the tmux-based layout",
                "callback": "kicli_code_assist.cli:run_tmux",
            },
            {
                "name": "chat",
                "help": "Run the simple chat flow",
                "callback": "kicli_code_assist.cli:run_chat",
            },
            {
                "name": "openinterpreter",
                "help": "Launch OpenInterpreter mode",
                "callback": "kicli_code_assist.cli:run_openinterpreter",
            },
            {
                "name": "doctor",
                "help": "Show CLI and environment diagnostics",
                "callback": "kicli_code_assist.cli:run_doctor",
            },
            {
                "name": "server",
                "help": "Manage services (backend, frontend, etc.)",
                "callback": "kicli_code_assist.cli:run_server",
                "options": [
                    {
                        "names": ["--subcommand"],
                        "param": "subcommand",
                        "default": "status",
                        "help": "Subcommand: status, register, unregister, detect-orphans, cleanup, sync",
                    },
                    {
                        "names": ["--name"],
                        "param": "name",
                        "default": None,
                        "help": "Service name (for register/unregister)",
                    },
                    {
                        "names": ["--pid"],
                        "param": "pid",
                        "type": "int",
                        "default": None,
                        "help": "Process ID (for register)",
                    },
                    {
                        "names": ["--port"],
                        "param": "port",
                        "type": "int",
                        "default": None,
                        "help": "Port number (for register)",
                    },
                    {
                        "names": ["-v", "--verbose"],
                        "param": "verbose",
                        "type": "bool",
                        "default": False,
                        "help": "Show detailed information",
                    },
                ],
            },
        ],
    }



def _resolve_callback(callback_ref: str | None) -> Callable[..., Any]:
    """Import and resolve a callback reference like module:function."""
    if not callback_ref:
        raise click.ClickException("Missing callback reference in CLI YAML")

    mod_name, _, func_name = callback_ref.partition(":")
    module = importlib.import_module(mod_name)
    callback = getattr(module, func_name)
    return callback


def _option_decorator(option_config: Dict[str, Any]) -> Callable[..., Any]:
    """Create a Click option decorator from a simple YAML schema."""
    names = option_config.get("names", [])
    if not names:
        raise click.ClickException("Each option needs at least one name")

    param_name = option_config.get("param") or names[-1].lstrip("-")
    param_name = param_name.replace("-", "_")
    option_type = option_config.get("type", "str")
    default = option_config.get("default")
    help_text = option_config.get("help", "")

    if option_type == "bool":
        return click.option(*names, param_name, default=bool(default), is_flag=True, help=help_text)

    if option_type == "int":
        return click.option(*names, param_name, default=default, type=int, help=help_text)

    return click.option(*names, param_name, default=default, help=help_text)


def _build_command(command_config: Dict[str, Any]) -> click.Command:
    """Build a click command from a YAML command definition."""
    callback = _resolve_callback(command_config.get("callback"))
    options = command_config.get("options", [])

    def _command_callback(**kwargs: Any) -> None:
        callback(**kwargs)

    for option in reversed(options):
        decorator = _option_decorator(option)
        _command_callback = decorator(_command_callback)

    return click.command(name=command_config["name"], help=command_config.get("help", ""))(_command_callback)


def _add_yaml_group(group: click.Group, commands: Iterable[Dict[str, Any]]) -> None:
    """Recursively add commands from YAML to a Click group."""
    for entry in commands:
        if entry.get("commands"):
            sub_group = click.Group(name=entry["name"], help=entry.get("help", ""))
            _add_yaml_group(sub_group, entry["commands"])
            group.add_command(sub_group)
            continue
        group.add_command(_build_command(entry))


@click.group(
    name="kicli-assist",
    help="KI Code Assistant - interactive code generation and review",
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.option("-q", "--quiet", is_flag=True, help="Suppress config file location output")
@click.pass_context
def cli(ctx: click.Context, quiet: bool) -> None:
    """Top-level Click entrypoint."""
    ctx.ensure_object(dict)
    ctx.obj["quiet"] = quiet

    # Display config location unless quiet mode is enabled
    if not quiet:
        try:
            config_file = find_config_path()
            config_abs = config_file.resolve()
            click.echo(f"Config: {config_abs}", err=True)
        except Exception:
            pass


def _register_yaml_commands(root: click.Group, config_path: str | None = None) -> click.Group:
    """Register commands from YAML on a Click group."""
    config = _load_yaml_tree(config_path)
    _add_yaml_group(root, config.get("commands", []))
    return root


_register_yaml_commands(cli)

# Register server subcommand group (native Click structure, not YAML-based)
cli.add_command(server)


def main() -> None:
    """Compatibility entrypoint for older callers."""
    cli()


if __name__ == "__main__":
    cli()

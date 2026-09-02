import importlib
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List

import click
import yaml


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

    if config.ollama_base_url:
        try:
            import requests
            requests.head(config.ollama_base_url, timeout=2)
            return "ollama"
        except Exception:
            pass

    if config.openai_api_key:
        return "openai"

    if config.ki_api_key:
        return "ki"

    return "mock"


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
    run_chat_flow(model=model, provider=provider or _detect_best_provider())


def run_openinterpreter(auto_run: bool = False, model: str | None = None) -> None:
    """Launch OpenInterpreter mode."""
    from ki_core import Config
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
    """Display quick environment diagnostics."""
    from ki_core import Config
    config = Config.from_env()
    click.echo("KI Code Assistant diagnostics")
    click.echo(f"- provider detection: {_detect_best_provider()}")
    click.echo(f"- ki_base_url: {config.ki_base_url or '<unset>'}")
    click.echo(f"- openai_api_key: {'set' if config.openai_api_key else 'missing'}")
    click.echo(f"- kicli_cache_dir: {config.kicli_cache_dir or '<unset>'}")


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


@click.group(name="kicli-assist", help="KI Code Assistant - interactive code generation and review")
def cli() -> None:
    """Top-level Click entrypoint."""


def _register_yaml_commands(root: click.Group, config_path: str | None = None) -> click.Group:
    """Register commands from YAML on a Click group."""
    config = _load_yaml_tree(config_path)
    _add_yaml_group(root, config.get("commands", []))
    return root


_register_yaml_commands(cli)


def main() -> None:
    """Compatibility entrypoint for older callers."""
    cli()


if __name__ == "__main__":
    cli()

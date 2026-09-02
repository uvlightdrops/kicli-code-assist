from click.testing import CliRunner

from kicli_code_assist.cli import cli


def test_cli_help_lists_main_commands():
    result = CliRunner().invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "chat" in result.output
    assert "tui" in result.output
    assert "tmux" in result.output
    assert "openinterpreter" in result.output
    assert "doctor" in result.output


def test_tui_help_uses_yaml_configured_options():
    result = CliRunner().invoke(cli, ["tui", "--help"])
    assert result.exit_code == 0
    assert "--config" in result.output
    assert "--provider" in result.output

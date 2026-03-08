import pytest
from typer.testing import CliRunner
from deluge_export.cli import app

runner = CliRunner()


def test_extract_command():
    result = runner.invoke(
        app, ["extract", "--path-match", "2025/11", "--dest", "/tmp/extracted"]
    )
    assert result.exit_code == 0
    assert "Extracting torrents matching '2025/11' to '/tmp/extracted'" in result.stdout


def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Extracts torrents from a deluge server" in result.stdout

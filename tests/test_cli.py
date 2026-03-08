import pytest
from unittest.mock import patch, MagicMock
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
    assert "list" in result.stdout
    assert "extract" in result.stdout


@patch("deluge_export.cli.client.get_client")
@patch("deluge_export.cli.client.get_matching_torrents")
def test_list_command_mocked(mock_get_torrents, mock_get_client):
    # Setup mock responses
    mock_client_instance = MagicMock()
    mock_get_client.return_value = mock_client_instance
    
    mock_get_torrents.return_value = [
        {
            "id": "abc123def",
            "name": "Ubuntu 24.04",
            "save_path": "/downloads/iso/Ubuntu 24.04",
            "size": 2500000000,
            "state": "Seeding"
        }
    ]
    
    result = runner.invoke(
        app, 
        ["list", "--path-match", "iso", "--user", "test", "--password", "test"]
    )
    
    assert result.exit_code == 0
    assert "Connecting to Deluge at 127.0.0.1:58846..." in result.stdout
    assert "Found 1 matching torrents" in result.stdout
    assert "Ubuntu 24.04" in result.stdout
    
    # Verify the mocked functions were called with correct arguments
    mock_get_client.assert_called_once_with("127.0.0.1", 58846, "test", "test")
    mock_get_torrents.assert_called_once_with(mock_client_instance, "iso")

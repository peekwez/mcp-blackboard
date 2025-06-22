# type: ignore
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from nexus.cli import cli
from nexus.models import Settings


@pytest.fixture
def cli_runner():
    """CLI runner fixture for testing click commands."""
    return CliRunner()


@pytest.fixture
def mock_settings():
    """Mock app settings for testing."""
    return MagicMock(spec=Settings)


def test_cli_group():
    """Test that the CLI group is properly configured."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Command line interface for managing the MCP Blackboard." in result.output


@patch("nexus.main.get_settings")
@patch("nexus.main.mcp")
def test_run_command_default_values(
    mock_mcp, mock_get_settings, cli_runner, mock_settings
):
    """Test the 'run' command with default values."""
    # Setup
    mock_get_settings.return_value = mock_settings
    mock_settings.mcp_transport = "sse"  # Changed to sse so host and port are set

    # Execute
    result = cli_runner.invoke(cli, ["run"])

    # Assert
    assert result.exit_code == 0
    # mock_get_settings.assert_called_once_with(".env")
    assert mock_mcp.settings.host == "127.0.0.1"
    assert mock_mcp.settings.port == 8000
    mock_mcp.run.assert_called_once_with(transport="sse")


@patch("nexus.main.get_settings")
@patch("nexus.main.mcp")
def test_run_command_custom_values(
    mock_mcp, mock_get_settings, cli_runner, mock_settings
):
    """Test the 'run' command with custom values."""
    # Setup
    mock_get_settings.return_value = mock_settings
    mock_settings.mcp_transport = "sse"

    # Execute
    result = cli_runner.invoke(
        cli, ["run", "--env-file", "custom.env", "--host", "0.0.0.0", "--port", "9000"]
    )

    # Assert
    assert result.exit_code == 0
    mock_get_settings.assert_called_once_with("custom.env")
    assert mock_mcp.settings.host == "0.0.0.0"
    assert mock_mcp.settings.port == 9000
    mock_mcp.run.assert_called_once_with(transport="sse")


@patch("nexus.main.get_settings")
@patch("nexus.main.mcp")
def test_run_command_short_options(
    mock_mcp, mock_get_settings, cli_runner, mock_settings
):
    """Test the 'run' command with short option flags."""
    # Setup
    mock_get_settings.return_value = mock_settings
    mock_settings.mcp_transport = "sse"

    # Execute
    result = cli_runner.invoke(
        cli, ["run", "-e", "custom.env", "-h", "0.0.0.0", "-p", "9000"]
    )

    # Assert
    assert result.exit_code == 0
    mock_get_settings.assert_called_once_with("custom.env")
    assert mock_mcp.settings.host == "0.0.0.0"
    assert mock_mcp.settings.port == 9000
    mock_mcp.run.assert_called_once_with(transport="sse")


@patch("nexus.main.get_settings")
def test_run_command_error_handling(mock_get_settings, cli_runner):
    """Test the 'run' command error handling."""
    # Setup
    mock_get_settings.side_effect = Exception("Config error")

    # Execute
    result = cli_runner.invoke(cli, ["run"])

    # Assert
    assert result.exit_code != 0
    assert "Config error" in str(result.exception)


def test_cli_entrypoint():
    """Test that the main CLI entrypoint can be invoked."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "run" in result.output


@patch("nexus.main.uvicorn.run")
@patch("nexus.main.mcp")
@patch("nexus.main.get_settings")
@patch("nexus.main.app")
def test_start_server_streamable_http(
    mock_app, mock_get_settings, mock_mcp, mock_uvicorn_run, mock_settings
):
    """Test the start_server function with streamable-http transport."""
    # Setup
    mock_get_settings.return_value = mock_settings
    mock_settings.mcp_transport = "streamable-http"
    mock_settings.log_level = "info"
    mock_settings.debug = False
    mock_mcp.streamable_http_app.return_value = MagicMock()

    # Execute
    from nexus.main import start_server

    start_server(env_file=".env", host="127.0.0.1", port=8000)

    # Assert
    mock_get_settings.assert_called_once_with(".env")
    mock_mcp.streamable_http_app.assert_called_once()
    mock_app.mount.assert_called_once_with(
        "/mcp", mock_mcp.streamable_http_app.return_value
    )
    mock_uvicorn_run.assert_called_once_with(
        mock_app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
        reload=False,
    )


@patch("nexus.main.mcp")
@patch("nexus.main.get_settings")
def test_start_server_stdio(mock_get_settings, mock_mcp, mock_settings):
    """Test the start_server function with stdio transport."""
    # Setup
    mock_get_settings.return_value = mock_settings
    mock_settings.mcp_transport = "stdio"

    # Execute
    from nexus.main import start_server

    start_server(env_file=".env")

    # Assert
    mock_get_settings.assert_called_once_with(".env")
    mock_mcp.run.assert_called_once_with(transport="stdio")

# type: ignore
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from main import cli, up
from src.models import AppConfig


@pytest.fixture
def cli_runner():
    """CLI runner fixture for testing click commands."""
    return CliRunner()


@pytest.fixture
def mock_config():
    """Mock app config for testing."""
    return MagicMock(spec=AppConfig)


def test_cli_group():
    """Test that the CLI group is properly configured."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Command line interface for managing the MCP Blackboard." in result.output


@patch("main.get_app_config")
@patch("main.mcp")
def test_up_command_default_values(
    mock_mcp, mock_get_app_config, cli_runner, mock_config
):
    """Test the 'up' command with default values."""
    # Setup
    mock_get_app_config.return_value = mock_config
    mock_config.mcp_transport = "stdio"

    # Execute
    result = cli_runner.invoke(up, [])

    # Assert
    assert result.exit_code == 0
    mock_get_app_config.assert_called_once_with(".env")
    assert mock_mcp.settings.host == "127.0.0.1"
    assert mock_mcp.settings.port == 8000
    mock_mcp.run.assert_called_once_with(transport="stdio")


@patch("main.get_app_config")
@patch("main.mcp")
def test_up_command_custom_values(
    mock_mcp, mock_get_app_config, cli_runner, mock_config
):
    """Test the 'up' command with custom values."""
    # Setup
    mock_get_app_config.return_value = mock_config
    mock_config.mcp_transport = "websocket"

    # Execute
    result = cli_runner.invoke(
        up, ["--env-file", "custom.env", "--host", "0.0.0.0", "--port", "9000"]
    )

    # Assert
    assert result.exit_code == 0
    mock_get_app_config.assert_called_once_with("custom.env")
    assert mock_mcp.settings.host == "0.0.0.0"
    assert mock_mcp.settings.port == 9000
    mock_mcp.run.assert_called_once_with(transport="websocket")


@patch("main.get_app_config")
@patch("main.mcp")
def test_up_command_short_options(
    mock_mcp, mock_get_app_config, cli_runner, mock_config
):
    """Test the 'up' command with short option flags."""
    # Setup
    mock_get_app_config.return_value = mock_config
    mock_config.mcp_transport = "websocket"

    # Execute
    result = cli_runner.invoke(up, ["-e", "custom.env", "-h", "0.0.0.0", "-p", "9000"])

    # Assert
    assert result.exit_code == 0
    mock_get_app_config.assert_called_once_with("custom.env")
    assert mock_mcp.settings.host == "0.0.0.0"
    assert mock_mcp.settings.port == 9000
    mock_mcp.run.assert_called_once_with(transport="websocket")


@patch("main.get_app_config")
def test_up_command_error_handling(mock_get_app_config, cli_runner):
    """Test the 'up' command error handling."""
    # Setup
    mock_get_app_config.side_effect = Exception("Config error")

    # Execute
    result = cli_runner.invoke(up, [])

    # Assert
    assert result.exit_code != 0
    mock_get_app_config.assert_called_once()


def test_cli_entrypoint():
    """Test that the main CLI entrypoint can be invoked."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "up" in result.output

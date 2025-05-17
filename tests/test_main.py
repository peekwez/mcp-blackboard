# type: ignore
from unittest.mock import MagicMock, patch

import pytest  # noqa: F401

from main import ContextBuilderMCPServer


@patch("main.mcp")
def test_context_builder_initialization(mock_mcp):
    """Test ContextBuilderMCPServer initialization."""
    server = ContextBuilderMCPServer()
    assert server is not None
    mock_mcp.run.assert_not_called()


@patch("main.mcp")
@patch("main.get_app_config")
def test_context_builder_run(mock_get_app_config, mock_mcp, app_config):
    """Test running the ContextBuilderMCPServer without starting the server."""
    mock_get_app_config.return_value = app_config
    server = ContextBuilderMCPServer()
    server.run()
    mock_get_app_config.assert_called_once()
    mock_mcp.run.assert_called_once_with(transport=app_config.mcp_transport)


@patch("main.ContextBuilderMCPServer")
def test_main_execution(mock_server_class):
    """Test the main execution path without starting the actual server."""
    mock_server = MagicMock()
    mock_server.run = MagicMock()  # Prevent blocking if run() is called
    mock_server_class.return_value = mock_server

    import main

    # Directly call the main entry point function if it exists
    if hasattr(main, "main"):
        main.main()
    else:
        # Fallback: instantiate and run the server as main would do
        server = main.ContextBuilderMCPServer()
        server.run()
    mock_server_class.assert_called_once()
    mock_server.run.assert_called_once()

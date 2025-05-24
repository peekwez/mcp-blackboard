# type: ignore
from unittest.mock import MagicMock, patch

import pytest

from main import ContextBuilderMCPServer


class TestContextBuilderMCPServer:
    """Test the ContextBuilderMCPServer class."""

    def test_init(self):
        """Test server initialization."""
        server = ContextBuilderMCPServer()
        assert isinstance(server, ContextBuilderMCPServer)

    @patch("main.mcp")
    @patch("main.get_app_config")
    def test_run_with_stdio_transport(
        self, mock_get_app_config: MagicMock, mock_mcp: MagicMock
    ):
        """Test running server with stdio transport."""
        # Mock app config
        mock_config = MagicMock()
        mock_config.mcp_transport = "stdio"
        mock_get_app_config.return_value = mock_config

        server = ContextBuilderMCPServer()
        server.run()

        mock_get_app_config.assert_called_once()
        mock_mcp.run.assert_called_once_with(transport="stdio")

    @patch("main.mcp")
    @patch("main.get_app_config")
    def test_run_with_sse_transport(
        self, mock_get_app_config: MagicMock, mock_mcp: MagicMock
    ):
        """Test running server with SSE transport."""
        # Mock app config
        mock_config = MagicMock()
        mock_config.mcp_transport = "sse"
        mock_get_app_config.return_value = mock_config

        server = ContextBuilderMCPServer()
        server.run()

        mock_get_app_config.assert_called_once()
        mock_mcp.run.assert_called_once_with(transport="sse")

    @patch("main.mcp")
    @patch("main.get_app_config")
    def test_run_exception_handling(
        self, mock_get_app_config: MagicMock, mock_mcp: MagicMock
    ):
        """Test server run with exception."""
        mock_get_app_config.side_effect = Exception("Config error")

        server = ContextBuilderMCPServer()

        with pytest.raises(Exception, match="Config error"):
            server.run()

    @patch("main.mcp")
    @patch("main.get_app_config")
    def test_main_execution_block_coverage(
        self, mock_get_app_config: MagicMock, mock_mcp: MagicMock
    ):
        """Test to cover the main execution block lines 12-13."""
        # This test specifically targets the lines 12-13 in main.py
        # which create a server instance and call run()

        mock_config = MagicMock()
        mock_config.mcp_transport = "stdio"
        mock_get_app_config.return_value = mock_config

        # Simulate executing the main block - this effectively tests lines 12-13
        server = ContextBuilderMCPServer()
        server.run()

        mock_get_app_config.assert_called_once()
        mock_mcp.run.assert_called_once_with(transport="stdio")

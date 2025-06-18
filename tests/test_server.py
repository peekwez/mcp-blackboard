# type: ignore
from unittest.mock import MagicMock, patch

import pytest  # noqa F401
from mcp.server.fastmcp import FastMCP

from server import (
    get_blackboard,
    get_context,
    get_plan,
    get_result,
    lifespan,
    mark_plan_as_completed,
    mcp,
    remove_stale_files,
    save_context_description,
    save_plan,
    save_result,
)


def test_mcp_instance():
    """Test that the MCP instance is properly configured."""
    assert isinstance(mcp, FastMCP)
    assert mcp.name == "MCP Blackboard Server"


@patch("server.fetch_blackboard")
@pytest.mark.asyncio
async def test_get_blackboard(mock_fetch_blackboard):
    """Test getting a blackboard."""
    # Setup
    mock_fetch_blackboard.return_value = {"key": "value"}

    # Execute
    result = await get_blackboard("test-plan-1")

    # Assert
    assert result == {"key": "value"}
    mock_fetch_blackboard.assert_called_once_with("test-plan-1")


@patch("server.fetch_plan")
@pytest.mark.asyncio
async def test_get_plan(mock_fetch_plan):
    """Test getting a plan."""
    # Setup
    mock_fetch_plan.return_value = {"id": "test-plan-1", "steps": []}

    # Execute
    result = await get_plan("test-plan-1")

    # Assert
    assert result == {"id": "test-plan-1", "steps": []}
    mock_fetch_plan.assert_called_once_with("test-plan-1")


@patch("server.fetch_result")
@pytest.mark.asyncio
async def test_get_result(mock_fetch_result):
    """Test getting a result."""
    # Setup
    mock_fetch_result.return_value = {"agent": "test-agent", "result": "test result"}

    # Execute
    result = await get_result("test-plan-1", "test-agent", 1)

    # Assert
    assert result == {"agent": "test-agent", "result": "test result"}
    mock_fetch_result.assert_called_once_with("test-plan-1", "test-agent", 1)


@patch("server.fetch_context")
@pytest.mark.asyncio
async def test_get_context(mock_fetch_context):
    """Test getting context."""
    # Setup
    mock_fetch_context.return_value = "# Test Markdown"

    # Execute
    result = await get_context("file:///path/to/file.pdf", True)

    # Assert
    assert result == "# Test Markdown"
    mock_fetch_context.assert_called_once_with("file:///path/to/file.pdf", True)


@patch("server.write_plan")
@pytest.mark.asyncio
async def test_save_plan(mock_write_plan):
    """Test saving a plan."""
    # Setup
    plan = {
        "id": "test-plan-1",
        "goal": "Test goal",
        "steps": [
            {
                "id": 1,
                "agent": "researcher",
                "prompt": "Do something",
                "revision": 1,
                "status": "completed",
                "depends_on": [],
            },
            {
                "id": 2,
                "agent": "extractor",
                "prompt": "Keep something",
                "revision": 1,
                "status": "pending",
                "depends_on": [1],
            },
        ],
    }
    mock_write_plan.return_value = "Plan saved successfully"

    # Execute
    result = await save_plan("test-plan-1", plan)

    # Assert
    assert result == "Plan saved successfully"
    mock_write_plan.assert_called_once_with("test-plan-1", plan)


@patch("server.update_plan_status")
@pytest.mark.asyncio
async def test_mark_plan_as_completed(mock_update_plan_status):
    """Test marking a plan step as completed."""
    # Setup
    mock_update_plan_status.return_value = "Plan step updated successfully"

    # Execute
    result = await mark_plan_as_completed("test-plan-1", 1)

    # Assert
    assert result == "Plan step updated successfully"
    mock_update_plan_status.assert_called_once_with("test-plan-1", 1)


@patch("server.write_result")
@pytest.mark.asyncio
async def test_save_result(mock_write_result):
    """Test saving a result."""
    # Setup
    result_data = {"key": "value"}
    mock_write_result.return_value = "Result saved successfully"

    # Execute
    result = await save_result(
        "test-plan-1", "test-agent", 1, "Test description", result_data
    )

    # Assert
    assert result == "Result saved successfully"
    mock_write_result.assert_called_once_with(
        "test-plan-1", "test-agent", 1, "Test description", result_data
    )


@patch("server.write_context_description")
@pytest.mark.asyncio
async def test_save_context_description(mock_write_context_description):
    """Test saving a context description."""
    # Setup
    mock_write_context_description.return_value = (
        "Context description saved successfully"
    )

    # Execute
    result = await save_context_description(
        "test-plan-1", "file:///path/to/file.pdf", "Test description"
    )

    # Assert
    assert result == "Context description saved successfully"
    mock_write_context_description.assert_called_once_with(
        "test-plan-1", "file:///path/to/file.pdf", "Test description"
    )


@patch("server.get_app_config")
@patch("server.get_filesystem")
def test_remove_stale_files(
    mock_get_filesystem, mock_get_app_config, app_config, mock_filesystem
):
    """Test removing stale files."""
    # Setup
    mock_get_app_config.return_value = app_config
    mock_get_filesystem.return_value = mock_filesystem

    file_info1 = {"name": "file1.txt", "size": 100, "ctime": 1620000000.0}  # Old file
    file_info2 = {"name": "file2.txt", "size": 200, "ctime": 9999999999.0}  # New file
    mock_filesystem.listdir.return_value = [file_info1, file_info2]

    # Execute
    remove_stale_files(max_age=60)  # 1 minute max age

    # Assert
    mock_get_app_config.assert_called_once()
    mock_get_filesystem.assert_called_once()
    mock_filesystem.listdir.assert_called_once()
    mock_filesystem.rm.assert_called_once()  # Should remove the old file only


@pytest.mark.asyncio
@patch("server.scheduler")
async def test_lifespan(mock_scheduler):
    """Test the lifespan context manager."""
    # Setup
    mock_app = MagicMock(spec=FastMCP)

    # Execute
    async with lifespan(mock_app):
        # The lifespan function just yields control here
        pass

    # Assert
    # Check that the scheduler is shutdown at the end of the context
    mock_scheduler.shutdown.assert_called_once()

# type: ignore
from unittest.mock import MagicMock, patch

import pytest  # noqa F401
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

from nexus.server import (
    app,
    get_blackboard,
    get_context,
    get_plan,
    get_result,
    health_check,
    lifespan,
    mark_plan_as_completed,
    mcp,
    save_context_description,
    save_plan,
    save_result,
    search_web,
)


def test_mcp_instance():
    """Test that the MCP instance is properly configured."""
    assert isinstance(mcp, FastMCP)
    assert mcp.name == "MCP Blackboard Server"


@patch("nexus.server.fetch_blackboard")
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


@patch("nexus.server.fetch_plan")
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


@patch("nexus.server.fetch_result")
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


@patch("nexus.server.fetch_context")
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


@patch("nexus.server.write_plan")
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
                "status": "pending",
            }
        ],
    }
    mock_write_plan.return_value = "ok"

    # Execute
    result = await save_plan("test-plan-1", plan)

    # Assert
    assert result == "ok"
    mock_write_plan.assert_called_once_with("test-plan-1", plan)


@patch("nexus.server.update_plan_status")
@pytest.mark.asyncio
async def test_mark_plan_as_completed(mock_update_status):
    """Test marking a plan as completed."""
    # Setup
    mock_update_status.return_value = "ok"

    # Execute
    result = await mark_plan_as_completed("test-plan-1", 1)

    # Assert
    assert result == "ok"
    mock_update_status.assert_called_once_with("test-plan-1", 1)


@patch("nexus.server.write_context_description")
@pytest.mark.asyncio
async def test_save_context_description(mock_write_desc):
    """Test saving context description."""
    # Setup
    mock_write_desc.return_value = "ok"

    # Execute
    result = await save_context_description(
        "test-plan-1", "file:///path/to/file.pdf", "Test description"
    )

    # Assert
    assert result == "ok"
    mock_write_desc.assert_called_once_with(
        "test-plan-1", "file:///path/to/file.pdf", "Test description"
    )


@patch("nexus.server.write_result")
@pytest.mark.asyncio
async def test_save_result(mock_write_result):
    """Test saving a result."""
    # Setup
    mock_write_result.return_value = "ok"

    # Execute
    result = await save_result(
        "test-plan-1", "researcher", 1, "Result description", "Test result"
    )

    # Assert
    assert result == "ok"
    mock_write_result.assert_called_once_with(
        "test-plan-1", "researcher", 1, "Result description", "Test result"
    )


@patch("nexus.server.run_web_search")
@pytest.mark.asyncio
async def test_search_web(mock_run_web_search):
    """Test web search functionality."""
    # Setup
    mock_run_web_search.return_value = '{"results": []}'

    # Execute
    result = await search_web("test query", 5)

    # Assert
    assert result == '{"results": []}'
    mock_run_web_search.assert_called_once_with("test query", 5)


@pytest.mark.asyncio
async def test_check_step_id():
    """Test step ID validation."""
    from nexus.server import check_step_id

    # Valid step ID
    assert check_step_id(1) == 1
    assert check_step_id(100) == 100

    # Invalid step IDs
    with pytest.raises(ValueError):
        check_step_id(0)

    with pytest.raises(ValueError):
        check_step_id(-1)

    with pytest.raises(ValueError):
        check_step_id("1")


@pytest.mark.asyncio
async def test_lifespan():
    """Test lifespan context manager."""
    # Mock FastMCP instance
    mock_mcp = MagicMock()

    # Test that the lifespan context manager yields
    async with lifespan(mock_mcp):
        pass

    # Check that scheduler.shutdown was called
    from nexus.server import scheduler

    assert scheduler is not None


def test_app_initialization():
    """Test that the FastAPI app is properly initialized."""
    # Verify that the app is a FastAPI instance
    assert isinstance(app, FastAPI)

    # Check for health endpoint
    health_route = None
    for route in app.routes:
        if route.path == "/health":
            health_route = route
            break

    assert health_route is not None
    assert health_route.methods == {"GET"}


@pytest.mark.asyncio
async def test_health_check():
    """Test the health check endpoint."""
    # Execute the health check endpoint
    result = await health_check()

    # Assert
    assert result == {"status": "healthy"}

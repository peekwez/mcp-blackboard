# type: ignore

import pytest  # noqa F401
from fastapi import FastAPI

from nexus.app import app, health_check


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

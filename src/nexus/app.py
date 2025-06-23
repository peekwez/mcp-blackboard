from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI

from nexus.server import mcp


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore
    async with AsyncExitStack() as stack:
        await stack.enter_async_context(mcp.session_manager.run())
        yield


app = FastAPI(
    title="Blackboard MCP Server",
    description=(
        "A blackboard server for storing and retrieving static "
        "and dynamic data for an agent task"
    ),
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """
    Health check endpoint to verify the server is running.

    Returns:
        dict: A dictionary indicating the server is healthy.
    """
    return {"status": "healthy"}

import uvicorn

from nexus.app import app
from nexus.common import get_settings
from nexus.server import mcp


def start_server(env_file: str, host: str = "127.0.0.1", port: int = 8000) -> None:
    """
    Run the MCP Blackboard with the specified environment file.

    Args:
        env_file (str): Path to the environment file.

    Returns:
        None
    """

    settings = get_settings(env_file)

    if settings.mcp_transport == "streamable-http":
        mcp.settings.mount_path = "/mcp"
        mcp_app = mcp.streamable_http_app()
        app.mount("/blackboard", mcp_app)
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level=settings.logging.level,
            reload=settings.debug,
        )
    elif settings.mcp_transport == "sse":
        mcp.settings.host = host
        mcp.settings.port = port
        mcp.run(transport="sse")
    elif settings.mcp_transport == "stdio":
        mcp.run(transport="stdio")

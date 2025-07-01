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
    mcp.settings.host = host  # type: ignore
    mcp.settings.port = port  # type: ignore
    mcp.run(transport=settings.mcp_transport)

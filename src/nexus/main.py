from nexus.common import get_settings
from nexus.server import mcp


def start_server(env_file: str, host: str, port: int) -> None:
    """
    Run the MCP Blackboard with the specified environment file.

    Args:
        env_file (str): Path to the environment file.

    Returns:
        None
    """

    settings = get_settings(env_file)
    mcp.settings.host = host
    mcp.settings.port = port
    mcp.run(transport=settings.mcp_transport)

import click

from common import get_app_config
from server import mcp


@click.group()
def cli() -> None:
    """Command line interface for managing the MCP Blackboard."""
    pass


@cli.command()
@click.option(
    "--env-file",
    "-e",
    default=".env",
    help="Path to the environment file.",
)
@click.option(
    "--host",
    "-h",
    default="127.0.0.1",
    help="Host address for the MCP Blackboard server.",
)
@click.option(
    "--port",
    "-p",
    default=8000,
    help="Port for the MCP Blackboard server.",
)
def up(env_file: str, host: str, port: int) -> None:
    """
    Run the MCP Blackboard with the specified environment file.

    Args:
        env_file (str): Path to the environment file.

    Returns:
        None
    """

    config = get_app_config(env_file)
    mcp.settings.host = host
    mcp.settings.port = port
    mcp.run(transport=config.mcp_transport)


if __name__ == "__main__":
    cli()

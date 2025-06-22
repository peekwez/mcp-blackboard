import click

from nexus.main import start_server


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
def run(env_file: str, host: str, port: int) -> None:
    """
    Run the MCP Blackboard with the specified environment file.

    Args:
        env_file (str): Path to the environment file.

    Returns:
        None
    """

    start_server(env_file, host, port)


if __name__ == "__main__":
    cli()

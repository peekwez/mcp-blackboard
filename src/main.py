from common import get_app_config
from server import mcp


class ContextBuilderMCPServer:
    def run(self) -> None:
        app_config = get_app_config()
        mcp.run(transport=app_config.mcp_transport)


if __name__ == "__main__":
    server = ContextBuilderMCPServer()
    server.run()

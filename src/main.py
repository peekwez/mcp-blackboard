from common import get_app_config
from server import mcp
from tools import fetch_memory, update_memory


class ContextBuilderMCPServer:
    def run(self):
        app_config = get_app_config()
        mcp.run(transport=app_config.mcp_transport)


if __name__ == "__main__":
    # server = ContextBuilderMCPServer()
    # server.run()
    key = "plan|6e292ce5fab04477a2b5335b7992f108"
    print(update_memory(key, "test", "test"))
    print(fetch_memory(key))

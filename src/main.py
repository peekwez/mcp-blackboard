from server import mcp


class MarkitdownMCPServer:
    def run(self):
        mcp.run(transport="sse")


if __name__ == "__main__":
    server = MarkitdownMCPServer()
    server.run()

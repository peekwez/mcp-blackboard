from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "Markitdown MCP Server",
    instructions="",
    dependencies=[
        "fsspec",
        "markitdown",
        "tenacity",
        "jinja2",
        "openai",
        "pydantic",
        "pydantic-settings",
    ],
)

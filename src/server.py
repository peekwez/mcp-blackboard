from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from mcp.server.fastmcp import FastMCP

from common import remove_stale_files
from tools import fetch_context, fetch_memory, update_memory

# Set up the scheduler
scheduler = BackgroundScheduler()
trigger = CronTrigger(minute=0)  # every hour at the start of the hour
scheduler.add_job(remove_stale_files, trigger)
scheduler.start()


@asynccontextmanager
async def lifespan(mcp: FastMCP):
    yield
    scheduler.shutdown()


mcp = FastMCP(
    "Context Builder MCP Server",
    lifespan=lifespan,
    dependencies=[
        "apscheduler",
        "dotenv",
        "fsspec",
        "jinja2",
        "markitdown",
        "openai",
        "pydantic",
        "pydantic-settings",
        "pyyaml",
        "tenacity",
    ],
)


@mcp.tool()
async def load_context(key: str, use_cache: bool = True) -> str:
    """
    Load the contents of a media location and convert the contents
    to Markdown.

    The tool supports various media formats such including:
        - pdf, png, jpg, html, docx, pptx, xlsx, txt, csv.

    It also supports the following storage protocols:
        - file:// -  Local file system
        - https:// - HTTP/HTTPS URLs
        - s3:// - Amazon S3 storage
        - gcs:// - Google Cloud Storage
        - abfs:// - Azure Blob Storage
        - smb:// - SMB/CIFS storage
        - sftp:// - FTP/SFTP storage.

    The tool uses the python `markitdown` library to convert the file
    to Markdown format.

    Args:
        key (str): The context key to load. It should be in the format
            "context|<url>" where <url> is the media location.
        use_cache (bool): Whether to use the cache for loading the file.
            Defaults to True.

    Returns:
        str: The media content in Markdown format.

    Raises:
        OSError: If there is an I/O error while loading the file.
        ValueError: If the URL is not valid or the conversion fails.
    """
    return fetch_context(key, use_cache)


@mcp.tool()
def read_memory(key: str) -> str:
    """
    Fetch a JSON-serializable value from shared Redis.

    Args:
        key (str): The key to fetch from Redis.

    Returns:
        str | None: The value associated with the key, or None if not found.
    """
    return fetch_memory(key)


@mcp.tool()
def write_memory(key: str, description: str, value: str) -> str:
    """
    Write a JSON-serializable value to shared Redis.

    Args:
        key (str): The key to write to Redis.
        description (str): A description of the value being written.
        value (str): The value to write to Redis.

    Returns:
        str: A confirmation message.

    Raises:
        ValueError: If the key is not constructed properly.
    """
    return update_memory(key, description, value)

from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.server import Settings

from common import get_app_config, get_file_age, get_filesystem
from tools import fetch_context, fetch_memory, update_memory


# Set up the scheduler
def remove_stale_files(max_age: int = 3600) -> None:
    """
    Remove all files in the cache directory that are older than 1 hour.

    Args:
        max_age (int): The maximum age of files to keep in seconds.
            Default is 3600 seconds (1 hour).

    Returns:
        None
    """

    app_config = get_app_config()
    _, cache_path = app_config.cache_path.split("://")
    fs = get_filesystem(app_config.cache_path, app_config)

    # remove all files older than 1 day
    for file_info in fs.listdir(cache_path):
        file_age = get_file_age(file_info)
        if file_age > max_age:
            fs.rm(f"{file_info['name']}")


scheduler = BackgroundScheduler()
trigger = CronTrigger(minute=0)  # every hour at the start of the hour
scheduler.add_job(remove_stale_files, trigger)
scheduler.start()


@asynccontextmanager
async def lifespan(mcp: FastMCP):
    yield
    scheduler.shutdown()


mcp = FastMCP(
    name="MCP Blackboard Server",
    instructions=(
        "A blackboard server for storing and retrieving "
        "static and dynamic data for an agent task"
    ),
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
async def read_context(key: str, use_cache: bool = True) -> str:
    """
    Reads the contents of a media location and convert the contents
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
async def read_memory(key: str) -> str | dict | list | None:
    """
    Fetch a JSON-serializable value from shared Redis.

    Args:
        key (str): The key to fetch from Redis. Key format should be
            "blackboard|<plan id>" or "plan|<plan_id>" or
            "context|<plan_id>|<url>" or "result|<plan_id>|<agent_name>|<step id>".

    Returns:
        str |dict| list| None: The value associated with the key, or None if not found.

    Raises:
        ValueError: If the key is not constructed properly.
    """
    return fetch_memory(key)


@mcp.tool()
async def write_memory(key: str, description: str, value: str | dict | list) -> str:
    """
    Write a JSON-serializable value to shared Redis.

    Args:
        key (str): The key to write to Redis. Key format should be
            "blackboard|<plan id>" or "plan|<plan_id>" or
            "context|<plan_id>|<url>" or "result|<plan_id>|<agent_name>|<step id>".
        description (str): A description of the value being written.
        value (str | dict | list): The value to write to Redis. It must be
            JSON-serializable.

    Returns:
        str: A confirmation message indicating that the value has been written.

    Raises:
        ValueError: If the key is not constructed properly.
    """
    return update_memory(key, description, value)
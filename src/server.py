from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from mcp.server.fastmcp import FastMCP

from common import get_app_config
from tools.context import fetch_context, get_file_age, get_filesystem
from tools.memory import (
    fetch_blackboard,
    fetch_plan,
    fetch_result,
    update_plan_status,
    write_context_description,
    write_plan,
    write_result,
)


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
async def save_plan(plan_id: str, plan: dict | str) -> str:
    """
    Save a plan to the shared state

    Args:
        plan_id (str): The ID of the plan.
        plan (dict|str): The plan to save. It should be a JSON-serializable object.

    Returns:
        str: A confirmation message indicating that the plan has been saved.

    Raises:
        ValueError: If the plan is not in the correct format.
    """
    return write_plan(plan_id, plan)


@mcp.tool()
async def mark_plan_as_completed(plan_id: str, step_id: str) -> str:
    """
    Mark a plan as completed in the shared state

    Args:
        plan_id (str): The ID of the plan to mark as completed.
        step_id (str): The ID of the step to mark as completed.

    Returns:
        str: A confirmation message indicating that the plan has been marked as done.
    """
    return update_plan_status(plan_id, step_id)


@mcp.tool()
async def save_result(
    plan_id: str, agent_name: str, step_id: str, description: str, result: str | dict
) -> str:
    """
    Save a result to the shared state

    Args:
        plan_id (str): The ID of the plan.
        agent_name (str): The name of the agent.
        step_id (str): The ID of the step.
        description (str): A description of the result being saved.
        result (str | dict): The result to save. It must be JSON-serializable.

    Returns:
        str: A confirmation message indicating that the result has been saved.

    Raises:
        ValueError: If the result is not in the correct format.
    """
    return write_result(plan_id, agent_name, step_id, description, result)


@mcp.tool()
async def save_context_description(
    plan_id: str, file_path_or_url: str, description: str
) -> str:
    """
    Write a context description to the shared state

    Args:
        plan_id (str): The ID of the plan.
        file_path_or_url (str): The file path or URL of the context.
        description (str): A description of the context.

    Returns:
        str: A confirmation message indicating that the context has been saved.
    """
    return write_context_description(plan_id, file_path_or_url, description)


@mcp.tool()
async def get_blackboard(plan_id: str) -> str | dict | None:
    """
    Fetch a blackboard entry for a plan from the shared state

    Args:
        plan_id (str): The ID of the plan to fetch.

    Returns:
        str | dict | None: The blackboard entry associated with the ID,
            or None if not found.
    """
    return fetch_blackboard(plan_id)


@mcp.tool()
async def get_plan(plan_id: str) -> str | dict | None:
    """
    Fetch a plan from the shared state

    Args:
        plan_id (str): The ID of the plan to fetch.

    Returns:
        str | dict | None: The plan associated with the ID, or None if not found.
    """
    return fetch_plan(plan_id)


@mcp.tool()
async def get_result(plan_id: str, agent_name: str, step_id: str) -> str | dict | None:
    """
    Fetch a result from the shared state

    Args:
        plan_id (str): The ID of the plan.
        agent_name (str): The name of the agent.
        step_id (str): The ID of the step.

    Returns:
        str | dict | None: The result associated with the ID, or None if not found.
    """
    return fetch_result(plan_id, agent_name, step_id)


@mcp.tool()
async def get_context(file_path_or_url: str, use_cache: bool = True) -> str:
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
        file_path_or_url (str): The file path or URL of the file to load.
            The URL should be in the format of a supported protocol.
        use_cache (bool): Whether to use the cache for loading the file.
            Defaults to True.

    Returns:
        str: The media content in Markdown format.

    Raises:
        OSError: If there is an I/O error while loading the file.
        ValueError: If the URL is not valid or the conversion fails.
    """

    return fetch_context(file_path_or_url, use_cache)

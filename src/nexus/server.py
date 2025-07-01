# type: ignore
import json
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from mcp.server.fastmcp import FastMCP

from nexus.models import AgentName
from nexus.scheduler import get_scheduler
from nexus.tools.context import fetch_context
from nexus.tools.memory import (
    fetch_blackboard,
    fetch_evaluation,
    fetch_plan,
    fetch_result,
    update_plan_status,
    write_context_description,
    write_evaluation,
    write_plan,
    write_result,
)
from nexus.tools.web import run_web_search

scheduler: BackgroundScheduler | None = None


@asynccontextmanager
async def lifespan(mcp: FastMCP):
    global scheduler

    scheduler = get_scheduler()
    if not scheduler:
        raise RuntimeError("Scheduler is not initialized.")

    if not scheduler.running:
        scheduler.start()
    yield
    if scheduler and scheduler.running:
        scheduler.shutdown()


mcp = FastMCP(
    name="MCP Blackboard Server",
    instructions=(
        "A blackboard server for storing and retrieving "
        "static and dynamic data for an agent task"
    ),
    lifespan=lifespan,
    stateless_http=True,
)


def check_step_id(step_id: int) -> int:
    """
    Check if the step ID is valid.

    Args:
        step_id (int): The ID of the step to check.

    Raises:
        ValueError: If the step ID is not a positive integer.
    """
    if not isinstance(step_id, int) or step_id <= 0:
        raise ValueError("step_id must be a positive integer.")
    return step_id


@mcp.tool(name="SearchWeb")
async def search_web(query: str, num_results: int = 10) -> str:
    """
    Perform a web search using the provided query and number of results.

    Args:
        query (str): The search query.
        num_results (int): The number of search results to return.

    Returns:
        str: A JSON string containing the search results.
    """
    return run_web_search(query, num_results)


@mcp.tool(name="SavePlan")
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
    data = json.loads(plan) if isinstance(plan, str) else plan
    return write_plan(plan_id, data)


@mcp.tool(name="MarkStepAsCompleted")
async def mark_step_as_completed(plan_id: str, step_id: int) -> str:
    """
    Mark a step as completed in the shared state

    Args:
        plan_id (str): The ID of the plan to mark the step as completed.
        step_id (int): The ID of the step to mark as completed.

    Returns:
        str: A confirmation message indicating that the step has been marked as done.
    """
    step_id = check_step_id(step_id)
    return update_plan_status(plan_id, step_id)


@mcp.tool(name="MarkStepAsRunning")
async def mark_step_as_running(plan_id: str, step_id: int) -> str:
    """
    Mark a step as running in the shared state

    Args:
        plan_id (str): The ID of the plan to mark the step as running.
        step_id (int): The ID of the step to mark as running.

    Returns:
        str: A confirmation message indicating that the step has been marked as running.
    """
    step_id = check_step_id(step_id)
    return update_plan_status(plan_id, step_id, status="running")


@mcp.tool(name="MarkStepAsFailed")
async def mark_step_as_failed(plan_id: str, step_id: int, message: str) -> str:
    """
    Mark a step as failed in the shared state

    Args:
        plan_id (str): The ID of the plan to mark the step as failed.
        step_id (int): The ID of the step to mark as failed.
        message (str): An message describe the failure reason. It should include
            the tool or action that was being attempted, the error message, and any
            relevant context that might help in diagnosing the issue.

    Returns:
        str: A confirmation message indicating that the step has been marked as failed.
    """
    step_id = check_step_id(step_id)
    return update_plan_status(plan_id, step_id, status="failed", message=message)


@mcp.tool(name="SaveResult")
async def save_result(
    plan_id: str,
    agent_name: AgentName,
    step_id: int,
    description: str,
    result: str | dict,
) -> str:
    """
    Save a result to the shared state

    Args:
        plan_id (str): The ID of the plan.
        agent_name (AgentName): The name of the agent.
        step_id (int): The ID of the step.
        description (str): A description of the result being saved.
        result (str | dict): The result to save. It must be JSON-serializable.

    Returns:
        str: A confirmation message indicating that the result has been saved.

    Raises:
        ValueError: If the result is not in the correct format.
    """
    step_id = check_step_id(step_id)
    return write_result(plan_id, str(agent_name), step_id, description, result)


@mcp.tool(name="SaveContextDescription")
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


@mcp.tool(name="GetBlackboard")
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


@mcp.tool(name="GetPlan")
async def get_plan(plan_id: str) -> str | dict | None:
    """
    Fetch a plan from the shared state

    Args:
        plan_id (str): The ID of the plan to fetch.

    Returns:
        str | dict | None: The plan associated with the ID, or None if not found.
    """
    return fetch_plan(plan_id)


@mcp.tool(name="GetResult")
async def get_result(
    plan_id: str, agent_name: AgentName, step_id: int
) -> str | dict | None:
    """
    Fetch a result from the shared state

    Args:
        plan_id (str): The ID of the plan.
        agent_name (AgentName): The name of the agent.
        step_id (int): The ID of the step.

    Returns:
        str | dict | None: The result associated with the ID, or None if not found.
    """
    step_id = check_step_id(step_id)
    return fetch_result(plan_id, str(agent_name), step_id)


@mcp.tool(name="GetContext")
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


@mcp.tool(name="SaveEvaluation")
async def save_evaluation(
    plan_id: str, step_evaluated: int, check_number: int, evaluation_result: dict | str
) -> str:
    """
    Save evaluation data for a specific plan and step.

    Args:
        plan_id (str): The ID of the plan.
        step_evaluated (int): The ID of the step being evaluated.
        check_number (int): The check number for the evaluation.
        evaluation_result (dict|str): The JSON serializable data of the evaluation
            result to save.

    Returns:
        str: A confirmation message indicating that the evaluation has been saved.
    """
    return write_evaluation(plan_id, step_evaluated, check_number, evaluation_result)


@mcp.tool(name="GetEvaluation")
async def get_evaluation(
    plan_id: str, step_evaluated: int, check_number: int
) -> str | dict | None:
    """
    Fetch evaluation data for a specific plan and step.

    Args:
        plan_id (str): The ID of the plan.
        step_evaluated (int): The ID of the step being evaluated.
        check_number (int): The check number for the evaluation.

    Returns:
        str | dict | None: The evaluation data associated with the ID,
            or None if not found.
    """
    return fetch_evaluation(plan_id, step_evaluated, check_number)

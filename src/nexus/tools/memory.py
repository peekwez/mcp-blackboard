# type: ignore
from __future__ import annotations

import json
from typing import Any

from azure.identity import DefaultAzureCredential
from redis import Redis
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from nexus.common import get_settings
from nexus.logging import get_logger
from nexus.models import ActionStream, Settings, StateUpdates

redis_client: None | Redis = None


def get_redis_client(settings: Settings | None = None) -> Redis:
    """
    Get the Redis client for shared memory.

    Returns:
        Redis: The Redis client for shared memory.
    """
    settings = get_settings() if settings is None else settings
    global redis_client
    if redis_client is None:
        if "windows.net" in settings.redis.host:
            cred = DefaultAzureCredential()
            token = cred.get_token("https://redis.azure.com/.default")
            settings.redis.password = token.token
        redis_client = Redis(**settings.redis.model_dump())
    return redis_client


@retry(
    stop=stop_after_attempt(3),
    wait=wait_random_exponential(multiplier=1, max=10),
    retry=retry_if_exception_type(OSError),
    reraise=True,
)
def add_to_stream(stream: ActionStream) -> str:
    """
    Add an action to the Redis stream for state updates.

    Args:
        stream (ActionStream): The action stream to add.

    Returns:
        str: A confirmation message.
    """

    client = get_redis_client()
    logger = get_logger(__name__)
    stream_key = f"task-updates:{stream.plan_id}"
    try:
        client.xadd(stream_key, stream.model_dump(mode="json"))  # type:ignore
        logger.info(
            f"Added to stream {stream_key}: {stream.action} for plan {stream.plan_id}"
        )
    except Exception as e:
        logger.error(f"Failed to add to stream {stream_key}: {e}")
        return f"error: {str(e)}"
    return "ok"


@retry(
    stop=stop_after_attempt(3),
    wait=wait_random_exponential(multiplier=1, max=10),
    retry=retry_if_exception_type(OSError),
    reraise=True,
)
def write_plan(plan_id: str, plan: dict[str, Any] | str) -> str:
    """
    Write a plan to the shared state

    Args:
        plan_id (str): The ID of the plan.
        plan (dict|str): The plan to save. It should be a JSON-serializable object.

    Returns:
        str: A confirmation message.

    Raises:
        ValueError: If the plan is not in the correct format.
    """
    logger = get_logger(__name__)

    if isinstance(plan, str):
        try:
            plan = json.loads(plan)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode plan JSON: {e}")
            raise ValueError("Plan must be a JSON-serializable object") from e

    client = get_redis_client()
    client.json().set(plan_id, "$", plan)
    client.expire(plan_id, 3600)
    logger.info(f"Plan {plan_id} written to shared state")

    stream = ActionStream(
        plan_id=plan_id, action=StateUpdates.write_plan, data=json.dumps(plan)
    )
    add_to_stream(stream)
    return "ok"


@retry(
    stop=stop_after_attempt(3),
    wait=wait_random_exponential(multiplier=1, max=10),
    retry=retry_if_exception_type(OSError),
    reraise=True,
)
def update_plan_status(
    plan_id: str,
    step_id: int,
    agent_name: str,
    status: str,
    message: str | None = None,
) -> str:
    """
    Mark a plan step as done in the shared state

    Args:
        plan_id (str): The ID of the plan to mark as done.
        step_id (int): The ID of the step to mark as done.
        agent_name (str): The name of the agent performing the step.
        status (str): The status to set for the step. Defaults to "completed".
        message (str | None): An optional message to include with the status update.

    Returns:
        str: A confirmation message.
    """
    logger = get_logger(__name__)
    client = get_redis_client()
    path = f".steps.[{step_id - 1}].status"
    client.json().set(plan_id, path, status)
    logger.info(f"Plan {plan_id} step {step_id} marked as {status} in shared state")

    data = json.dumps(
        {"step_id": step_id, "agent": agent_name, "status": status, "message": message}
    )
    stream = ActionStream(plan_id=plan_id, action=StateUpdates.update_status, data=data)
    add_to_stream(stream)
    return "ok"


@retry(
    stop=stop_after_attempt(3),
    wait=wait_random_exponential(multiplier=1, max=10),
    retry=retry_if_exception_type(OSError),
    reraise=True,
)
def write_context_description(
    plan_id: str, file_path_or_url: str, description: str
) -> str:
    """
    Write a context description to the shared state

    Args:
        plan_id (str): The ID of the plan.
        file_path_or_url (str): The file path or URL of the context.
        description (str): A description of the context.

    Returns:
        str: A confirmation message.
    """
    logger = get_logger(__name__)
    client = get_redis_client()

    _b_key = f"blackboard|{plan_id}".lower()
    _v_key = f"context|{plan_id}|{file_path_or_url}"
    client.hset(_b_key, _v_key, description)  # type: ignore
    client.expire(_b_key, 3600)
    logger.info(
        f"Context description for {file_path_or_url} written to"
        f"shared state for plan {plan_id}"
    )

    data = json.dumps({"context_url": file_path_or_url, "description": description})
    stream = ActionStream(
        plan_id=plan_id, action=StateUpdates.describe_context, data=data
    )
    add_to_stream(stream)
    return "ok"


@retry(
    stop=stop_after_attempt(3),
    wait=wait_random_exponential(multiplier=1, max=10),
    retry=retry_if_exception_type(OSError),
    reraise=True,
)
def write_result(
    plan_id: str,
    agent_name: str,
    step_id: int,
    description: str,
    result: dict[str, Any] | str,
) -> str:
    """
    Save a result to the shared state

    Args:
        plan_id (str): The ID of the plan.
        agent_name (str): The name of the agent.
        step_id (int): The ID of the step.
        description (str): A description of the result being saved.
        result (dict|str): The result to save. It should be a JSON-serializable object.

    Returns:
        str: A confirmation message.

    Raises:
        ValueError: If the result is not in the correct format.
    """
    logger = get_logger(__name__)

    if isinstance(result, dict):
        try:
            result = json.dumps(result)
        except TypeError as e:
            logger.error(f"Failed to serialize result: {e}")
            raise ValueError("Result must be a JSON-serializable object") from e

    client = get_redis_client()
    _b_key = f"blackboard|{plan_id}".lower()
    _v_key = f"result|{plan_id}|{step_id}|{agent_name}".lower()
    client.hset(_b_key, _v_key, description)  # type:ignore
    client.expire(_b_key, 3600)
    client.set(_v_key, result)
    client.expire(_v_key, 3600)

    logger.info(
        f"Result for step {step_id} by agent {agent_name} "
        f"written to shared state for plan {plan_id}"
    )

    data = json.dumps(
        {
            "step_id": step_id,
            "agent_name": agent_name,
            "description": description,
            "result": result,
        }
    )
    stream = ActionStream(plan_id=plan_id, action=StateUpdates.write_result, data=data)
    add_to_stream(stream)
    return "ok"


@retry(
    stop=stop_after_attempt(3),
    wait=wait_random_exponential(multiplier=1, max=10),
    retry=retry_if_exception_type(OSError),
    reraise=True,
)
def fetch_plan(plan_id: str) -> str | dict[str, Any] | None:
    """
    Fetch a plan from the shared state

    Args:
        plan_id (str): The ID of the plan to fetch.

    Returns:
        str | dict | None: The plan associated with the ID, or None if not found.
    """
    logger = get_logger(__name__)
    client = get_redis_client()
    data = client.json().get(plan_id)  # type:ignore
    logger.info(f"Plan data for {plan_id}")
    return json.dumps(data) if data else None


@retry(
    stop=stop_after_attempt(3),
    wait=wait_random_exponential(multiplier=1, max=10),
    retry=retry_if_exception_type(OSError),
    reraise=True,
)
def fetch_blackboard(plan_id: str) -> str | dict[str, Any] | None:
    """
    Fetch a blackboard from the shared state

    Args:
        plan_id (str): The ID of the plan to fetch.

    Returns:
        str | dict | None: The blackboard associated with the ID, or None if not found.
    """
    logger = get_logger(__name__)
    client = get_redis_client()
    _b_key = f"blackboard|{plan_id}".lower()
    data = json.dumps(client.hgetall(_b_key))  # type:ignore
    logger.info(f"Blackboard data for {plan_id}")
    return data if data else None


@retry(
    stop=stop_after_attempt(3),
    wait=wait_random_exponential(multiplier=1, max=10),
    retry=retry_if_exception_type(OSError),
    reraise=True,
)
def fetch_result(
    plan_id: str, agent_name: str, step_id: int
) -> str | dict[str, Any] | None:
    """
    Fetch a result from the shared state

    Args:
        plan_id (str): The ID of the plan.
        agent_name (str): The name of the agent.
        step_id (int): The ID of the step.

    Returns:
        str | dict | None: The result associated with the plan, agent, and step,
        or None if not found.
    """
    logger = get_logger(__name__)
    client = get_redis_client()
    _v_key = f"result|{plan_id}|{step_id}|{agent_name}".lower()
    data = json.dumps(client.get(_v_key))
    logger.info(
        f"Result data for  plan {plan_id}, {agent_name} agent,  and step {step_id}"
    )
    return data if data else None


@retry(
    stop=stop_after_attempt(3),
    wait=wait_random_exponential(multiplier=1, max=10),
    retry=retry_if_exception_type(OSError),
    reraise=True,
)
def write_evaluation(
    plan_id: str,
    step_evaluated: int,
    check_number: int,
    evaluation_result: dict[str, Any] | str,
) -> str:
    """
    Write an evaluation to the shared state

    Args:
        plan_id (str): The ID of the plan.
        step_evaluated (int): The ID of the step who's results is being evaluated.
        check_number (int): The number of the check being performed.
        evaluation_result (dict|str): The JSON serializable data of the evaluation
            result to save.

    Returns:
        str: A confirmation message.

    Raises:
        ValueError: If the plan is not in the correct format.
    """
    logger = get_logger(__name__)

    if isinstance(evaluation_result, str):
        try:
            evaluation_result = json.loads(evaluation_result)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode evaluation result JSON: {e}")
            raise ValueError(
                "Evaluation result must be a JSON-serializable object"
            ) from e

    client = get_redis_client()

    _b_key = f"blackboard|{plan_id}".lower()
    _v_key = f"evaluation|{plan_id}|{step_evaluated}|{check_number}".lower()

    description = (
        f"Evaluation number {check_number} for step {step_evaluated} "
        f"in plan {plan_id} by the evaluator agent"
    )
    client.hset(_b_key, _v_key, description)  # type:ignore
    client.expire(_b_key, 3600)

    client.json().set(_v_key, "$", evaluation_result)
    client.expire(_v_key, 3600)

    logger.info(f"Evaluation {_v_key} written to shared state")

    stream = ActionStream(
        plan_id=plan_id,
        action=StateUpdates.evaluate_result,
        data=json.dumps(evaluation_result),
    )
    add_to_stream(stream)
    return "ok"


def fetch_evaluation(
    plan_id: str, step_evaluated: int, check_number: int
) -> str | dict[str, Any] | None:
    """
    Fetch an evaluation from the shared state

    Args:
        plan_id (str): The ID of the plan.
        step_evaluated (int): The ID of the step who's results is being evaluated.
        check_number (int): The number of the check being performed.

    Returns:
        str | dict | None: The evaluation associated with the plan, step,
            and check number, or None if not found.
    """
    logger = get_logger(__name__)
    client = get_redis_client()
    _v_key = f"evaluation|{plan_id}|{step_evaluated}|{check_number}".lower()
    data = json.dumps(client.json().get(_v_key))  # type:ignore
    logger.info(
        f"Evaluation data for {plan_id}, step {step_evaluated}, check {check_number}"
    )
    return data if data else None

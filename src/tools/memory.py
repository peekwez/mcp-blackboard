# type: ignore
import json

from azure.identity import DefaultAzureCredential
from redis import Redis

from common import get_app_config
from models import ActionStream, AppConfig, StateUpdates

redis_client: None | Redis = None


def get_redis_client(app_config: AppConfig) -> Redis:
    """
    Get the Redis client for shared memory.

    Returns:
        Redis: The Redis client for shared memory.
    """

    global redis_client
    if redis_client is None:
        if "windows.net" in app_config.redis.host:
            cred = DefaultAzureCredential()
            token = cred.get_token("https://redis.azure.com/.default")
            app_config.redis.password = token.token
        redis_client = Redis(**app_config.redis.model_dump())
    return redis_client


def add_to_stream(stream: ActionStream) -> str:
    """
    Add an action to the Redis stream for state updates.

    Args:
        stream (ActionStream): The action stream to add.

    Returns:
        str: A confirmation message.
    """
    client = get_redis_client(get_app_config())
    stream_key = f"task-updates:{stream.plan_id}"
    try:
        client.xadd(stream_key, stream.model_dump(mode="json"))
    except Exception as e:
        import logging

        logging.error(f"Failed to add to stream {stream_key}: {e}")
        return f"error: {str(e)}"
    return "ok"


def write_plan(plan_id: str, plan: dict | str) -> str:
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
    if not isinstance(plan, dict | str):
        raise ValueError("Plan must be a JSON-serializable object")

    if isinstance(plan, str):
        plan = json.loads(plan)

    client = get_redis_client(get_app_config())
    client.json().set(plan_id, "$", plan)
    client.expire(plan_id, 3600)

    stream = ActionStream(
        plan_id=plan_id, action=StateUpdates.write_plan, data=json.dumps(plan)
    )
    add_to_stream(stream)
    return "ok"


def update_plan_status(plan_id: str, step_id: int, status: str = "completed") -> str:
    """
    Mark a plan step as done in the shared state

    Args:
        plan_id (str): The ID of the plan to mark as done.
        step_id (int): The ID of the step to mark as done.
        status (str): The status to set for the step. Defaults to "completed".

    Returns:
        str: A confirmation message.
    """
    client = get_redis_client(get_app_config())
    path = f".steps.[{step_id - 1}].status"
    client.json().set(plan_id, path, status)

    data = json.dumps({"step_id": step_id, "status": status})
    stream = ActionStream(plan_id=plan_id, action=StateUpdates.update_status, data=data)
    add_to_stream(stream)
    return "ok"


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
    client = get_redis_client(get_app_config())

    _b_key = f"blackboard|{plan_id}".lower()
    _v_key = f"context|{plan_id}|{file_path_or_url}"
    client.hset(_b_key, _v_key, description)
    client.expire(_b_key, 3600)

    data = json.dumps({"context_url": file_path_or_url, "description": description})
    stream = ActionStream(
        plan_id=plan_id, action=StateUpdates.describe_context, data=data
    )
    add_to_stream(stream)
    return "ok"


def write_result(
    plan_id: str, agent_name: str, step_id: int, description: str, result: dict | str
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
    if not isinstance(result, dict | str):
        raise ValueError("Result must be a JSON-serializable object")

    if isinstance(result, dict):
        result = json.dumps(result)

    client = get_redis_client(get_app_config())
    _b_key = f"blackboard|{plan_id}".lower()
    _v_key = f"result|{plan_id}|{step_id}|{agent_name}".lower()
    client.hset(_b_key, _v_key, description)
    client.expire(_b_key, 3600)
    client.set(_v_key, result)
    client.expire(_v_key, 3600)

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


def fetch_plan(plan_id: str) -> str | dict | None:
    """
    Fetch a plan from the shared state

    Args:
        plan_id (str): The ID of the plan to fetch.

    Returns:
        str | dict | None: The plan associated with the ID, or None if not found.
    """
    client = get_redis_client(get_app_config())
    return client.json().get(plan_id)


def fetch_blackboard(plan_id: str) -> str | dict | None:
    """
    Fetch a blackboard from the shared state

    Args:
        plan_id (str): The ID of the plan to fetch.

    Returns:
        str | dict | None: The blackboard associated with the ID, or None if not found.
    """
    client = get_redis_client(get_app_config())
    _b_key = f"blackboard|{plan_id}".lower()
    return json.dumps(client.hgetall(_b_key))


def fetch_result(plan_id: str, agent_name: str, step_id: int) -> str | dict | None:
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
    client = get_redis_client(get_app_config())
    _v_key = f"result|{plan_id}|{step_id}|{agent_name}".lower()
    return json.dumps(client.get(_v_key))

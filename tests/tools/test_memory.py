# type: ignore
import json
from unittest.mock import MagicMock, patch

import pytest  # noqa F401

from tools.memory import (
    fetch_blackboard,
    fetch_plan,
    fetch_result,
    update_plan_status,
    write_context_description,
    write_plan,
    write_result,
)


@patch("tools.memory.get_app_config")
@patch("tools.memory.get_redis_client")
def test_write_plan(mock_get_redis, mock_get_app_config, app_config, mock_redis):
    """Test writing a plan to Redis."""
    # Setup
    mock_get_app_config.return_value = app_config
    mock_get_redis.return_value = mock_redis
    mock_redis.json = MagicMock()
    plan = {"id": "test-plan", "steps": [{"id": "step-1", "status": "pending"}]}

    # Execute
    result = write_plan("test-plan-1", plan)

    # Assert
    mock_redis.json().set.assert_called_once_with("test-plan-1", "$", plan)
    mock_redis.expire.assert_called_once_with("test-plan-1", 3600)
    assert result == "ok"


@patch("tools.memory.get_app_config")
@patch("tools.memory.get_redis_client")
def test_write_plan_string(mock_get_redis, mock_get_app_config, app_config, mock_redis):
    """Test writing a plan as string to Redis."""
    # Setup
    mock_get_app_config.return_value = app_config
    mock_get_redis.return_value = mock_redis
    mock_redis.json = MagicMock()
    plan_str = '{"id": "test-plan", "steps": [{"id": "step-1", "status": "pending"}]}'
    plan_dict = json.loads(plan_str)

    # Execute
    result = write_plan("test-plan-1", plan_str)

    # Assert
    mock_redis.json().set.assert_called_once_with("test-plan-1", "$", plan_dict)
    mock_redis.expire.assert_called_once_with("test-plan-1", 3600)
    assert result == "ok"


@patch("tools.memory.get_app_config")
@patch("tools.memory.get_redis_client")
@patch("tools.memory.fetch_plan")
def test_update_plan_status(
    mock_fetch_plan,
    mock_get_redis,
    mock_get_app_config,
    app_config,
    mock_redis,
    sample_plan,
):
    """Test updating plan step status."""
    # Setup
    mock_get_app_config.return_value = app_config
    mock_get_redis.return_value = mock_redis
    mock_redis.json = MagicMock()
    mock_fetch_plan.return_value = sample_plan

    # Execute
    result = update_plan_status("test-plan-1", "1", "completed")

    # Assert
    mock_redis.json().set.assert_called_once_with(
        "test-plan-1", ".steps.[0].status", "completed"
    )
    assert result == "ok"


@patch("tools.memory.get_app_config")
@patch("tools.memory.get_redis_client")
def test_write_context_description(
    mock_get_redis, mock_get_app_config, app_config, mock_redis
):
    """Test writing context description to Redis."""
    # Setup
    mock_get_app_config.return_value = app_config
    mock_get_redis.return_value = mock_redis

    # Execute
    result = write_context_description(
        "test-plan-1", "file:///path/to/file.pdf", "Test description"
    )

    # Assert
    _b_key = "blackboard|test-plan-1"
    _v_key = "context|test-plan-1|file:///path/to/file.pdf"
    mock_redis.hset.assert_called_once_with(_b_key, _v_key, "Test description")
    mock_redis.expire.assert_called_once_with(_b_key, 3600)
    assert result == "ok"


@patch("tools.memory.get_app_config")
@patch("tools.memory.get_redis_client")
def test_write_result(mock_get_redis, mock_get_app_config, app_config, mock_redis):
    """Test writing a result to Redis."""
    # Setup
    mock_get_app_config.return_value = app_config
    mock_get_redis.return_value = mock_redis
    result_data = {"key": "value"}

    # Execute
    result = write_result("test-plan-1", "test-agent", "1", "Test result", result_data)

    # Assert
    _b_key = "blackboard|test-plan-1"
    _v_key = "result|test-plan-1|1|test-agent"
    mock_redis.hset.assert_called_once_with(_b_key, _v_key, "Test result")
    mock_redis.set.assert_called_once_with(_v_key, json.dumps(result_data))

    # Check that expire was called for both keys, but don't enforce order
    assert mock_redis.expire.call_count == 2
    mock_redis.expire.assert_any_call(_b_key, 3600)
    mock_redis.expire.assert_any_call(_v_key, 3600)
    assert result == "ok"


@patch("tools.memory.get_app_config")
@patch("tools.memory.get_redis_client")
def test_fetch_plan_found(
    mock_get_redis, mock_get_app_config, app_config, mock_redis, sample_plan
):
    """Test fetching a plan from Redis that exists."""
    # Setup
    mock_get_app_config.return_value = app_config
    mock_get_redis.return_value = mock_redis
    mock_redis.json = MagicMock()
    mock_redis.json().get.return_value = sample_plan

    # Execute
    result = fetch_plan("test-plan-1")

    # Assert
    mock_redis.json().get.assert_called_once_with("test-plan-1")
    assert result == sample_plan


@patch("tools.memory.get_app_config")
@patch("tools.memory.get_redis_client")
def test_fetch_plan_not_found(
    mock_get_redis, mock_get_app_config, app_config, mock_redis
):
    """Test fetching a plan from Redis that doesn't exist."""
    # Setup
    mock_get_app_config.return_value = app_config
    mock_get_redis.return_value = mock_redis
    mock_redis.json = MagicMock()
    mock_redis.json().get.return_value = None

    # Execute
    result = fetch_plan("test-plan-1")

    # Assert
    mock_redis.json().get.assert_called_once_with("test-plan-1")
    assert result is None


@patch("tools.memory.get_app_config")
@patch("tools.memory.get_redis_client")
def test_fetch_blackboard(mock_get_redis, mock_get_app_config, app_config, mock_redis):
    """Test fetching blackboard entries from Redis."""
    # Setup
    mock_get_app_config.return_value = app_config
    mock_get_redis.return_value = mock_redis
    mock_redis.hgetall.return_value = {
        "file1": json.dumps({"file": "file1", "description": "desc1"}),
        "file2": json.dumps({"file": "file2", "description": "desc2"}),
    }

    # Execute
    result = fetch_blackboard("test-plan-1")

    # Assert
    mock_redis.hgetall.assert_called_once_with("blackboard|test-plan-1")
    # Since fetch_blackboard returns a JSON string, parse it for assertions
    result_dict = json.loads(result)
    assert len(result_dict) == 2
    # The values are already JSON strings in mock_redis.hgetall.return_value
    file1_data = json.loads(result_dict["file1"])
    file2_data = json.loads(result_dict["file2"])
    assert file1_data["description"] == "desc1"
    assert file2_data["description"] == "desc2"


@patch("tools.memory.get_app_config")
@patch("tools.memory.get_redis_client")
def test_fetch_result(mock_get_redis, mock_get_app_config, app_config, mock_redis):
    """Test fetching a result from Redis."""
    # Setup
    mock_get_app_config.return_value = app_config
    mock_get_redis.return_value = mock_redis
    expected_result = {
        "agent": "test-agent",
        "step": "1",
        "description": "Test result",
        "result": {"key": "value"},
    }
    # In the actual implementation, we set the value as a JSON string
    mock_redis.get.return_value = json.dumps(expected_result)

    # Execute
    result = fetch_result("test-plan-1", "test-agent", "1")

    # Assert
    key = "result|test-plan-1|1|test-agent"
    mock_redis.get.assert_called_once_with(key)
    # The fetch_result function does json.dumps(client.get(_v_key)),
    # which means it's doing json.dumps(json.dumps(expected_result))
    # So we need to parse it twice
    result_dict = json.loads(json.loads(result))
    assert result_dict == expected_result

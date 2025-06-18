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
    plan = {
        "id": "test-plan",
        "goal": "Test goal",
        "steps": [
            {
                "id": 1,
                "agent": "test-agent",
                "prompt": "Test prompt",
                "revision": 1,
                "status": "pending",
            }
        ],
    }

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
    plan_str = """
        {
            "id": "test-plan",
            "goal": "Test goal",
            "steps": [
                {
                    "id": 1,
                    "agent": "test-agent",
                    "prompt": "Test prompt",
                    "revision": 1,
                    "status": "pending"
                }
            ]
        }
    """
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
    result = update_plan_status("test-plan-1", 1, "completed")

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
    result = write_result("test-plan-1", "test-agent", 1, "Test result", result_data)

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
        "step": 1,
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


@patch("tools.memory.get_app_config")
@patch("tools.memory.get_redis_client")
def test_write_plan_invalid_input(
    mock_get_redis, mock_get_app_config, app_config, mock_redis
):
    """Test writing an invalid plan to Redis."""
    # Setup
    mock_get_app_config.return_value = app_config
    mock_get_redis.return_value = mock_redis
    mock_redis.json = MagicMock()
    invalid_plan = 123  # Not a dict or string

    # Execute & Assert
    with pytest.raises(ValueError, match="Plan must be a JSON-serializable object"):
        write_plan("test-plan-1", invalid_plan)

    # Verify no Redis calls were made
    mock_redis.json().set.assert_not_called()
    mock_redis.expire.assert_not_called()


@patch("tools.memory.get_app_config")
@patch("tools.memory.get_redis_client")
def test_write_result_invalid_input(
    mock_get_redis, mock_get_app_config, app_config, mock_redis
):
    """Test writing an invalid result to Redis."""
    # Setup
    mock_get_app_config.return_value = app_config
    mock_get_redis.return_value = mock_redis
    invalid_result = 123  # Not a dict or string

    # Execute & Assert
    with pytest.raises(ValueError, match="Result must be a JSON-serializable object"):
        write_result("test-plan-1", "test-agent", "1", "Test result", invalid_result)

    # Verify no Redis calls were made
    mock_redis.hset.assert_not_called()
    mock_redis.expire.assert_not_called()
    mock_redis.set.assert_not_called()


@patch("tools.memory.get_app_config")
@patch("tools.memory.get_redis_client")
def test_write_result_string_input(
    mock_get_redis, mock_get_app_config, app_config, mock_redis
):
    """Test writing a string result to Redis."""
    # Setup
    mock_get_app_config.return_value = app_config
    mock_get_redis.return_value = mock_redis
    result_data = "test result as string"

    # Execute
    result = write_result("test-plan-1", "test-agent", "1", "Test result", result_data)

    # Assert
    _b_key = "blackboard|test-plan-1"
    _v_key = "result|test-plan-1|1|test-agent"
    mock_redis.hset.assert_called_once_with(_b_key, _v_key, "Test result")
    mock_redis.set.assert_called_once_with(_v_key, result_data)

    # Check that expire was called for both keys, but don't enforce order
    assert mock_redis.expire.call_count == 2
    mock_redis.expire.assert_any_call(_b_key, 3600)
    mock_redis.expire.assert_any_call(_v_key, 3600)
    assert result == "ok"


@patch("tools.memory.get_app_config")
@patch("tools.memory.Redis")
@patch("tools.memory.DefaultAzureCredential")
def test_get_redis_client_azure(
    mock_azure_cred, mock_redis_class, mock_get_app_config, app_config, mock_redis
):
    """Test getting Redis client with Azure credentials."""
    # Setup
    mock_redis_class.return_value = mock_redis
    mock_get_app_config.return_value = app_config

    # Create a copy of app_config with Azure host
    app_config_azure = app_config.model_copy(deep=True)
    app_config_azure.redis.host = "test.windows.net"
    mock_get_app_config.return_value = app_config_azure

    # Mock Azure credential
    mock_cred = MagicMock()
    mock_azure_cred.return_value = mock_cred
    mock_token = MagicMock()
    mock_token.token = "azure-token"
    mock_cred.get_token.return_value = mock_token

    # Reset the global redis_client to None to force creation of a new client
    import tools.memory

    tools.memory.redis_client = None

    # Execute
    result = tools.memory.get_redis_client(app_config_azure)

    # Assert
    assert result == mock_redis
    mock_azure_cred.assert_called_once()
    mock_cred.get_token.assert_called_once_with("https://redis.azure.com/.default")
    mock_redis_class.assert_called_once()
    # Check that the password was set to the Azure token
    assert any(
        call_kwargs.get("password") == "azure-token"
        for _, call_kwargs in mock_redis_class.call_args_list
    )

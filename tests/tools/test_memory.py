# type: ignore
import json
from unittest.mock import MagicMock, patch

import pytest  # noqa F401

from nexus.models import ActionStream, StateUpdates
from nexus.tools.memory import (
    add_to_stream,
    fetch_blackboard,
    fetch_plan,
    fetch_result,
    get_redis_client,
    update_plan_status,
    write_context_description,
    write_plan,
    write_result,
)


@patch("nexus.tools.memory.get_settings")
@patch("nexus.tools.memory.get_redis_client")
def test_write_plan(mock_get_redis, mock_get_settings, settings, mock_redis):
    """Test writing a plan to Redis."""
    # Setup
    mock_get_settings.return_value = settings
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


@patch("nexus.tools.memory.get_settings")
@patch("nexus.tools.memory.get_redis_client")
def test_write_plan_string(mock_get_redis, mock_get_settings, settings, mock_redis):
    """Test writing a plan as string to Redis."""
    # Setup
    mock_get_settings.return_value = settings
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


@patch("nexus.tools.memory.get_settings")
@patch("nexus.tools.memory.get_redis_client")
def test_update_plan_status(
    mock_get_redis,
    mock_get_settings,
    settings,
    mock_redis,
):
    """Test updating plan step status."""
    # Setup
    mock_get_settings.return_value = settings
    mock_get_redis.return_value = mock_redis
    mock_redis.json = MagicMock()

    # Execute
    result = update_plan_status("test-plan-1", 1)

    # Assert
    mock_redis.json().set.assert_called_once_with(
        "test-plan-1", ".steps.[0].status", "completed"
    )
    assert result == "ok"


@patch("nexus.tools.memory.get_settings")
@patch("nexus.tools.memory.get_redis_client")
def test_write_context_description(
    mock_get_redis, mock_get_settings, settings, mock_redis
):
    """Test writing context description to Redis."""
    # Setup
    mock_get_settings.return_value = settings
    mock_get_redis.return_value = mock_redis

    # Execute
    result = write_context_description(
        "test-plan-1", "file:///path/to/file.pdf", "Test description"
    )

    # Assert
    mock_redis.hset.assert_called_once_with(
        "blackboard|test-plan-1",
        "context|test-plan-1|file:///path/to/file.pdf",
        "Test description",
    )
    assert result == "ok"


@patch("nexus.tools.memory.get_settings")
@patch("nexus.tools.memory.get_redis_client")
def test_write_result(mock_get_redis, mock_get_settings, settings, mock_redis):
    """Test writing result to Redis."""
    # Setup
    mock_get_settings.return_value = settings
    mock_get_redis.return_value = mock_redis

    # Execute
    result = write_result(
        "test-plan-1", "researcher", 1, "Result description", "Test result"
    )

    # Assert
    mock_redis.hset.assert_called_once_with(
        "blackboard|test-plan-1",
        "result|test-plan-1|1|researcher",
        "Result description",
    )
    assert result == "ok"


@patch("nexus.tools.memory.get_settings")
@patch("nexus.tools.memory.get_redis_client")
def test_fetch_plan(mock_get_redis, mock_get_settings, settings, mock_redis):
    """Test fetching plan from Redis."""
    # Setup
    mock_get_settings.return_value = settings
    mock_get_redis.return_value = mock_redis
    mock_redis.json = MagicMock()
    mock_redis.json().get.return_value = {"id": "test-plan-1", "steps": []}

    # Execute
    result = fetch_plan("test-plan-1")

    # Assert
    mock_redis.json().get.assert_called_once_with("test-plan-1")
    assert result == {"id": "test-plan-1", "steps": []}


@patch("nexus.tools.memory.get_settings")
@patch("nexus.tools.memory.get_redis_client")
def test_fetch_plan_not_found(mock_get_redis, mock_get_settings, settings, mock_redis):
    """Test fetching plan when not found in Redis."""
    # Setup
    mock_get_settings.return_value = settings
    mock_get_redis.return_value = mock_redis
    mock_redis.json = MagicMock()
    mock_redis.json().get.return_value = None

    # Execute
    result = fetch_plan("test-plan-1")

    # Assert
    mock_redis.json().get.assert_called_once_with("test-plan-1")
    assert result is None


@patch("nexus.tools.memory.get_settings")
@patch("nexus.tools.memory.get_redis_client")
def test_fetch_result(mock_get_redis, mock_get_settings, settings, mock_redis):
    """Test fetching result from Redis."""
    # Setup
    mock_get_settings.return_value = settings
    mock_get_redis.return_value = mock_redis
    mock_redis.get.return_value = "Test result"

    # Execute
    result = fetch_result("test-plan-1", "researcher", 1)

    # Assert
    mock_redis.get.assert_called_once_with("result|test-plan-1|1|researcher")
    assert result == '"Test result"'


@patch("nexus.tools.memory.get_settings")
@patch("nexus.tools.memory.get_redis_client")
def test_fetch_result_not_found(
    mock_get_redis, mock_get_settings, settings, mock_redis
):
    """Test fetching result when not found in Redis."""
    # Setup
    mock_get_settings.return_value = settings
    mock_get_redis.return_value = mock_redis
    mock_redis.get.return_value = None

    # Execute
    result = fetch_result("test-plan-1", "researcher", 1)

    # Assert
    mock_redis.get.assert_called_once_with("result|test-plan-1|1|researcher")
    assert result == "null"


@patch("nexus.tools.memory.get_settings")
@patch("nexus.tools.memory.get_redis_client")
def test_fetch_blackboard(
    mock_get_redis,
    mock_get_settings,
    settings,
    mock_redis,
):
    """Test fetching blackboard data."""
    # Setup
    mock_get_settings.return_value = settings
    mock_get_redis.return_value = mock_redis
    mock_redis.hgetall.return_value = {
        "context|test-plan-1|file:///path/to/file.pdf": "Context description",
        "result|test-plan-1|1|researcher": "Result 1",
    }

    # Execute
    result = fetch_blackboard("test-plan-1")

    # Assert
    mock_redis.hgetall.assert_called_once_with("blackboard|test-plan-1")
    assert result == json.dumps(
        {
            "context|test-plan-1|file:///path/to/file.pdf": "Context description",
            "result|test-plan-1|1|researcher": "Result 1",
        }
    )


@patch("nexus.tools.memory.Redis")
@patch("nexus.tools.memory.DefaultAzureCredential")
def test_get_redis_client_azure(
    mock_default_azure_credential, mock_redis_class, settings
):
    """Test getting Redis client with Azure Redis Cache."""
    # Setup
    mock_azure_instance = MagicMock()
    mock_default_azure_credential.return_value = mock_azure_instance
    mock_token = MagicMock()
    mock_token.token = "mock-azure-token"
    mock_azure_instance.get_token.return_value = mock_token

    # Modify settings to use Azure Redis
    settings_azure = settings.model_copy(deep=True)
    settings_azure.redis.host = "test.redis.windows.net"

    # Execute
    with patch("nexus.tools.memory.redis_client", None):
        client = get_redis_client(settings_azure)

    # Assert
    mock_default_azure_credential.assert_called_once()
    mock_azure_instance.get_token.assert_called_once_with(
        "https://redis.azure.com/.default"
    )
    mock_redis_class.assert_called_once()
    assert settings_azure.redis.password == "mock-azure-token"
    assert client is not None


@patch("nexus.tools.memory.Redis")
def test_get_redis_client_regular(mock_redis_class, settings):
    """Test getting Redis client for non-Azure Redis."""
    # Execute
    with patch("nexus.tools.memory.redis_client", None):
        client = get_redis_client(settings)

    # Assert
    mock_redis_class.assert_called_once()
    assert client is not None


@patch("nexus.tools.memory.Redis")
def test_get_redis_client_cached(mock_redis_class, settings):
    """Test getting cached Redis client."""
    # Setup
    mock_instance = MagicMock()

    # Execute
    with patch("nexus.tools.memory.redis_client", mock_instance):
        client = get_redis_client(settings)

    # Assert
    mock_redis_class.assert_not_called()
    assert client is mock_instance


@patch("nexus.tools.memory.get_redis_client")
def test_add_to_stream_success(mock_get_redis, mock_redis):
    """Test successfully adding to a Redis stream."""
    # Setup
    mock_get_redis.return_value = mock_redis
    stream = ActionStream(
        plan_id="test-plan-1",
        action=StateUpdates.write_plan,
        data=json.dumps({"test": "data"}),
    )

    # Execute
    result = add_to_stream(stream)

    # Assert
    mock_redis.xadd.assert_called_once()
    assert result == "ok"


@patch("nexus.tools.memory.get_redis_client")
def test_add_to_stream_error(mock_get_redis, mock_redis):
    """Test handling errors when adding to a Redis stream."""
    # Setup
    mock_get_redis.return_value = mock_redis
    mock_redis.xadd.side_effect = Exception("Test error")
    stream = ActionStream(
        plan_id="test-plan-1",
        action=StateUpdates.write_plan,
        data=json.dumps({"test": "data"}),
    )

    # Execute
    result = add_to_stream(stream)

    # Assert
    mock_redis.xadd.assert_called_once()
    assert "error: Test error" in result


@patch("nexus.tools.memory.get_settings")
@patch("nexus.tools.memory.get_redis_client")
def test_write_plan_invalid_type(mock_get_redis, mock_get_settings, settings):
    """Test writing a plan with invalid type."""
    # Setup
    mock_get_settings.return_value = settings

    # Execute & Assert
    with pytest.raises(ValueError, match="Plan must be a JSON-serializable object"):
        write_plan("test-plan-1", 123)  # Integer is not dict or str


@patch("nexus.tools.memory.get_settings")
@patch("nexus.tools.memory.get_redis_client")
def test_write_result_invalid_type(mock_get_redis, mock_get_settings, settings):
    """Test writing a result with invalid type."""
    # Setup
    mock_get_settings.return_value = settings

    # Execute & Assert
    with pytest.raises(ValueError, match="Result must be a JSON-serializable object"):
        write_result(
            "test-plan-1", "researcher", 1, "Test description", 123
        )  # Integer is not dict or str


@patch("nexus.tools.memory.get_settings")
@patch("nexus.tools.memory.get_redis_client")
def test_write_result_dict(mock_get_redis, mock_get_settings, settings, mock_redis):
    """Test writing a result as dict to Redis."""
    # Setup
    mock_get_settings.return_value = settings
    mock_get_redis.return_value = mock_redis
    result_dict = {"key": "value"}

    # Execute
    result = write_result(
        "test-plan-1", "researcher", 1, "Result description", result_dict
    )

    # Assert
    mock_redis.hset.assert_called_once()
    mock_redis.set.assert_called_once_with(
        "result|test-plan-1|1|researcher", json.dumps(result_dict)
    )
    assert result == "ok"

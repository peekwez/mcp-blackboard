# type: ignore
import json
from unittest.mock import MagicMock, patch

import pytest

from tools.memory import (
    fetch_blackboard,
    fetch_plan,
    fetch_result,
    get_redis_client,
    update_plan_status,
    write_context_description,
    write_plan,
    write_result,
)


class TestGetRedisClient:
    """Test the get_redis_client function."""

    @patch("tools.memory.Redis")
    def test_get_redis_client_first_call(
        self, mock_redis_class: MagicMock, mock_app_config
    ):
        """Test first call to get_redis_client creates new client."""
        mock_redis_instance = MagicMock()
        mock_redis_class.return_value = mock_redis_instance

        result = get_redis_client(mock_app_config)

        assert result == mock_redis_instance
        mock_redis_class.assert_called_once_with(**mock_app_config.redis.model_dump())

    @patch("tools.memory.Redis")
    def test_get_redis_client_azure_redis(
        self, mock_redis_class: MagicMock, mock_app_config
    ):
        """Test get_redis_client with Azure Redis (windows.net host)."""
        mock_app_config.redis.host = "test.redis.cache.windows.net"
        mock_redis_instance = MagicMock()
        mock_redis_class.return_value = mock_redis_instance

        with patch("tools.memory.DefaultAzureCredential") as mock_cred_class:
            mock_cred = MagicMock()
            mock_token = MagicMock()
            mock_token.token = "azure_token"
            mock_cred.get_token.return_value = mock_token
            mock_cred_class.return_value = mock_cred

            result = get_redis_client(mock_app_config)

            assert result == mock_redis_instance
            assert mock_app_config.redis.password == "azure_token"
            mock_cred.get_token.assert_called_once_with(
                "https://redis.azure.com/.default"
            )

    @patch("tools.memory.Redis")
    def test_get_redis_client_cached(
        self, mock_redis_class: MagicMock, mock_app_config
    ):
        """Test subsequent calls return cached client."""
        mock_redis_instance = MagicMock()
        mock_redis_class.return_value = mock_redis_instance

        # First call
        result1 = get_redis_client(mock_app_config)
        # Second call
        result2 = get_redis_client(mock_app_config)

        assert result1 == result2 == mock_redis_instance
        # Redis should only be instantiated once
        assert mock_redis_class.call_count == 1


class TestWritePlan:
    """Test the write_plan function."""

    @patch("tools.memory.get_redis_client")
    @patch("tools.memory.get_app_config")
    def test_write_plan_dict(
        self, mock_get_config: MagicMock, mock_get_redis: MagicMock
    ):
        """Test writing a plan as dict."""
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        plan_data = {"id": 1, "goal": "test"}
        plan_id = "test-plan-id"

        result = write_plan(plan_id, plan_data)

        assert result == "ok"
        mock_redis.json().set.assert_called_once_with(plan_id, "$", plan_data)
        mock_redis.expire.assert_called_once_with(plan_id, 3600)

    @patch("tools.memory.get_redis_client")
    @patch("tools.memory.get_app_config")
    def test_write_plan_json_string(
        self, mock_get_config: MagicMock, mock_get_redis: MagicMock
    ):
        """Test writing a plan as JSON string - should work after fixing the logic."""
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        plan_data = {"id": 1, "goal": "test"}
        plan_json = json.dumps(plan_data)
        plan_id = "test-plan-id"

        # This should now work with the fixed validation logic
        result = write_plan(plan_id, plan_json)

        assert result == "ok"
        mock_redis.json().set.assert_called_once_with(plan_id, "$", plan_data)
        mock_redis.expire.assert_called_once_with(plan_id, 3600)

    @patch("tools.memory.get_redis_client")
    @patch("tools.memory.get_app_config")
    def test_write_plan_invalid_type(
        self, mock_get_config: MagicMock, mock_get_redis: MagicMock
    ):
        """Test writing a plan with invalid type."""
        plan_id = "test-plan-id"

        with pytest.raises(ValueError, match="Plan must be a JSON-serializable object"):
            write_plan(plan_id, "invalid string")


class TestUpdatePlanStatus:
    """Test the update_plan_status function."""

    @patch("tools.memory.get_redis_client")
    @patch("tools.memory.get_app_config")
    def test_update_plan_status_default(
        self, mock_get_config: MagicMock, mock_get_redis: MagicMock
    ):
        """Test updating plan status with default status."""
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        plan_id = "test-plan-id"
        step_id = 1

        result = update_plan_status(plan_id, step_id)

        assert result == "ok"
        mock_redis.json().set.assert_called_once_with(
            plan_id, ".steps.[0].status", "completed"
        )

    @patch("tools.memory.get_redis_client")
    @patch("tools.memory.get_app_config")
    def test_update_plan_status_custom(
        self, mock_get_config: MagicMock, mock_get_redis: MagicMock
    ):
        """Test updating plan status with custom status."""
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        plan_id = "test-plan-id"
        step_id = 2
        status = "failed"

        result = update_plan_status(plan_id, step_id, status)

        assert result == "ok"
        mock_redis.json().set.assert_called_once_with(
            plan_id, ".steps.[1].status", "failed"
        )


class TestWriteContextDescription:
    """Test the write_context_description function."""

    @patch("tools.memory.get_redis_client")
    @patch("tools.memory.get_app_config")
    def test_write_context_description(
        self, mock_get_config: MagicMock, mock_get_redis: MagicMock
    ):
        """Test writing context description."""
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        plan_id = "test-plan-id"
        file_path = "file:///tmp/test.txt"
        description = "Test description"

        result = write_context_description(plan_id, file_path, description)

        assert result == "ok"

        expected_b_key = f"blackboard|{plan_id}".lower()
        expected_v_key = f"context|{plan_id}|{file_path}"

        mock_redis.hset.assert_called_once_with(
            expected_b_key, expected_v_key, description
        )
        mock_redis.expire.assert_called_once_with(expected_b_key, 3600)


class TestWriteResult:
    """Test the write_result function."""

    @patch("tools.memory.get_redis_client")
    @patch("tools.memory.get_app_config")
    def test_write_result_dict(
        self, mock_get_config: MagicMock, mock_get_redis: MagicMock
    ):
        """Test writing result as dict - should work after fixing the logic."""
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        plan_id = "test-plan-id"
        agent_name = "researcher"
        step_id = 1
        description = "Test result"
        result_data = {"data": "test"}

        # This should now work with the fixed logic
        result = write_result(plan_id, agent_name, step_id, description, result_data)

        assert result == "ok"
        expected_b_key = f"blackboard|{plan_id}".lower()
        expected_v_key = f"result|{plan_id}|{step_id}|{agent_name}".lower()
        expected_data = json.dumps(result_data)

        mock_redis.hset.assert_called_once_with(
            expected_b_key, expected_v_key, description
        )
        mock_redis.set.assert_called_once_with(expected_v_key, expected_data)
        assert mock_redis.expire.call_count == 2

    @patch("tools.memory.get_redis_client")
    @patch("tools.memory.get_app_config")
    def test_write_result_json_string(
        self, mock_get_config: MagicMock, mock_get_redis: MagicMock
    ):
        """Test writing result as JSON string - should work after fixing logic."""
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        plan_id = "test-plan-id"
        agent_name = "researcher"
        step_id = 1
        description = "Test result"
        result_data = {"data": "test"}
        result_json = json.dumps(result_data)

        # This should now work with the fixed validation logic
        result = write_result(plan_id, agent_name, step_id, description, result_json)

        assert result == "ok"
        expected_b_key = f"blackboard|{plan_id}".lower()
        expected_v_key = f"result|{plan_id}|{step_id}|{agent_name}".lower()

        mock_redis.hset.assert_called_once_with(
            expected_b_key, expected_v_key, description
        )
        mock_redis.set.assert_called_once_with(expected_v_key, result_data)
        assert mock_redis.expire.call_count == 2

    @patch("tools.memory.get_redis_client")
    @patch("tools.memory.get_app_config")
    def test_write_result_invalid_type(
        self, mock_get_config: MagicMock, mock_get_redis: MagicMock
    ):
        """Test writing result with invalid type."""
        plan_id = "test-plan-id"
        agent_name = "researcher"
        step_id = 1
        description = "Test result"

        with pytest.raises(
            ValueError, match="Result must be a JSON-serializable object"
        ):
            write_result(plan_id, agent_name, step_id, description, 123)  # Invalid type

    @patch("tools.memory.get_redis_client")
    @patch("tools.memory.get_app_config")
    def test_write_result_invalid_json_string(
        self, mock_get_config: MagicMock, mock_get_redis: MagicMock
    ):
        """Test writing result with invalid JSON string."""
        plan_id = "test-plan-id"
        agent_name = "researcher"
        step_id = 1
        description = "Test result"

        with pytest.raises(
            ValueError, match="Result must be a JSON-serializable object"
        ):
            write_result(plan_id, agent_name, step_id, description, "invalid json")


class TestFetchPlan:
    """Test the fetch_plan function."""

    @patch("tools.memory.get_redis_client")
    @patch("tools.memory.get_app_config")
    def test_fetch_plan(self, mock_get_config: MagicMock, mock_get_redis: MagicMock):
        """Test fetching a plan."""
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        plan_data = {"id": 1, "goal": "test"}
        mock_redis.json().get.return_value = plan_data

        plan_id = "test-plan-id"
        result = fetch_plan(plan_id)

        assert result == plan_data
        mock_redis.json().get.assert_called_once_with(plan_id)

    @patch("tools.memory.get_redis_client")
    @patch("tools.memory.get_app_config")
    def test_fetch_plan_not_found(
        self, mock_get_config: MagicMock, mock_get_redis: MagicMock
    ):
        """Test fetching a non-existent plan."""
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        mock_redis.json().get.return_value = None

        plan_id = "nonexistent-plan-id"
        result = fetch_plan(plan_id)

        assert result is None


class TestFetchBlackboard:
    """Test the fetch_blackboard function."""

    @patch("tools.memory.get_redis_client")
    @patch("tools.memory.get_app_config")
    def test_fetch_blackboard(
        self, mock_get_config: MagicMock, mock_get_redis: MagicMock
    ):
        """Test fetching a blackboard."""
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        blackboard_data = {"key1": "value1", "key2": "value2"}
        mock_redis.hgetall.return_value = blackboard_data

        plan_id = "test-plan-id"
        result = fetch_blackboard(plan_id)

        expected_b_key = f"blackboard|{plan_id}".lower()
        expected_result = json.dumps(blackboard_data)

        assert result == expected_result
        mock_redis.hgetall.assert_called_once_with(expected_b_key)

    @patch("tools.memory.get_redis_client")
    @patch("tools.memory.get_app_config")
    def test_fetch_blackboard_empty(
        self, mock_get_config: MagicMock, mock_get_redis: MagicMock
    ):
        """Test fetching an empty blackboard."""
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        mock_redis.hgetall.return_value = {}

        plan_id = "test-plan-id"
        result = fetch_blackboard(plan_id)

        assert result == json.dumps({})


class TestFetchResult:
    """Test the fetch_result function."""

    @patch("tools.memory.get_redis_client")
    @patch("tools.memory.get_app_config")
    def test_fetch_result(self, mock_get_config: MagicMock, mock_get_redis: MagicMock):
        """Test fetching a result."""
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        result_data = {"data": "test"}
        mock_redis.get.return_value = result_data

        plan_id = "test-plan-id"
        agent_name = "researcher"
        step_id = 1

        result = fetch_result(plan_id, agent_name, step_id)

        expected_v_key = f"result|{plan_id}|{step_id}|{agent_name}".lower()
        expected_result = json.dumps(result_data)

        assert result == expected_result
        mock_redis.get.assert_called_once_with(expected_v_key)

    @patch("tools.memory.get_redis_client")
    @patch("tools.memory.get_app_config")
    def test_fetch_result_not_found(
        self, mock_get_config: MagicMock, mock_get_redis: MagicMock
    ):
        """Test fetching a non-existent result."""
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        mock_redis.get.return_value = None

        plan_id = "test-plan-id"
        agent_name = "researcher"
        step_id = 1

        result = fetch_result(plan_id, agent_name, step_id)

        assert result == json.dumps(None)


class TestMemoryModuleEdgeCases:
    """Test edge cases in memory module after fixing the bugs."""

    @patch("tools.memory.get_redis_client")
    @patch("tools.memory.get_app_config")
    def test_write_plan_invalid_json_string(
        self, mock_get_config: MagicMock, mock_get_redis: MagicMock
    ):
        """Test write_plan with invalid JSON string."""
        plan_id = "test-plan-id"

        with pytest.raises(ValueError, match="Plan must be a JSON-serializable object"):
            write_plan(plan_id, "invalid json string")

    @patch("tools.memory.get_redis_client")
    @patch("tools.memory.get_app_config")
    def test_write_plan_invalid_type(
        self, mock_get_config: MagicMock, mock_get_redis: MagicMock
    ):
        """Test write_plan with invalid type."""
        plan_id = "test-plan-id"

        with pytest.raises(ValueError, match="Plan must be a JSON-serializable object"):
            write_plan(plan_id, 123)  # type: ignore

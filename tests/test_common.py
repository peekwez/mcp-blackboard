# type: ignore
import datetime
from unittest.mock import MagicMock, patch

import pytest  # noqa F401

from common import (
    get_app_config,
    get_converter_opts,
    get_file_age,
    get_filesystem,
    get_redis_client,
    get_storage_opts,
    load_config,
    validate_key,
)


@patch("common.app_config", None)
@patch("common.Environment")
@patch("common.yaml.safe_load")
def test_load_config(mock_yaml_load, mock_env, app_config):
    """Test loading configuration from environment variables."""
    # Setup
    mock_env.return_value.get_template.return_value.render.return_value = "config_yaml"
    mock_yaml_load.return_value = app_config.model_dump()

    # Execute
    result = load_config(".env.test")

    # Assert
    assert result is not None
    assert result.cache_path == app_config.cache_path
    assert result.mcp_transport == app_config.mcp_transport


@patch("common.app_config", None)
@patch("common.load_config")
def test_get_app_config(mock_load_config, app_config):
    """Test getting application configuration."""
    # Setup
    mock_load_config.return_value = app_config

    # Execute
    result = get_app_config()

    # Assert
    assert result is not None
    assert result == app_config

    # Test caching
    with patch("common.load_config") as mock_load_config_2:
        result2 = get_app_config()
        mock_load_config_2.assert_not_called()
        assert result2 == app_config


def test_get_converter_opts(app_config):
    """Test getting converter options."""
    # Test PDF file
    result_pdf = get_converter_opts("file:///path/to/file.pdf", app_config)
    assert result_pdf is not None
    assert "docintel_endpoint" in result_pdf
    assert (
        result_pdf["docintel_endpoint"] == app_config.converter.azure_document_endpoint
    )

    # Test image file
    result_img = get_converter_opts("file:///path/to/file.png", app_config)
    assert result_img is not None
    assert "llm_model" in result_img
    assert result_img["llm_model"] == app_config.converter.openai_default_model

    # Test other file format
    result_other = get_converter_opts("file:///path/to/file.txt", app_config)
    assert result_other is not None
    assert "enable_plugins" in result_other
    assert result_other["enable_plugins"] is True


def test_get_storage_opts_file(app_config):
    """Test getting storage options for file protocol."""
    # Setup & Execute
    result = get_storage_opts("file:///path/to/file.pdf", app_config)

    # Assert
    assert result == {}


def test_get_storage_opts_s3(app_config):
    """Test getting storage options for S3 protocol."""
    # Setup & Execute
    result = get_storage_opts("s3://bucket/path/to/file.pdf", app_config)

    # Assert
    assert result is not None
    assert result == app_config.storage.s3


def test_get_storage_opts_abfs(app_config):
    """Test getting storage options for ABFS protocol."""
    # Setup & Execute
    result = get_storage_opts("abfs://container/path/to/file.pdf", app_config)

    # Assert
    assert result is not None
    assert result == app_config.storage.abfs


def test_get_storage_opts_unsupported(app_config):
    """Test getting storage options for unsupported protocol."""
    # Setup & Execute & Assert
    with pytest.raises(ValueError, match="Unsupported protocol"):
        get_storage_opts("unknown://path/to/file.pdf", app_config)


@patch("common.get_storage_opts")
@patch("common.fsspec.filesystem")
def test_get_filesystem(
    mock_filesystem_fn, mock_get_storage_opts, app_config, mock_filesystem
):
    """Test getting filesystem for a URL."""
    # Setup
    mock_get_storage_opts.return_value = {"key": "value"}
    mock_filesystem_fn.return_value = mock_filesystem

    # Execute
    result = get_filesystem("s3://bucket/path/to/file.pdf", app_config)

    # Assert
    mock_filesystem_fn.assert_called_once_with("s3", key="value")
    assert result == mock_filesystem


def test_get_file_age():
    """Test getting file age."""
    # Setup
    now = datetime.datetime.now(datetime.UTC)
    one_hour_ago = now - datetime.timedelta(hours=1)

    file_info_ctime = {"ctime": one_hour_ago.timestamp()}
    file_info_creation_time = {"creation_time": one_hour_ago}

    # Execute & Assert
    age_ctime = get_file_age(file_info_ctime)
    assert 3500 <= age_ctime <= 3700  # Around 1 hour in seconds

    age_creation_time = get_file_age(file_info_creation_time)
    assert 3500 <= age_creation_time <= 3700


@patch("common.redis_client", None)
@patch("common.Redis")
def test_get_redis_client(mock_redis_class, app_config, mock_redis):
    """Test getting Redis client."""
    # Setup
    mock_redis_class.return_value = mock_redis

    # Execute
    result = get_redis_client(app_config)

    # Assert
    assert result == mock_redis
    mock_redis_class.assert_called_once()

    # Test caching
    with patch("common.Redis") as mock_redis_class_2:
        result2 = get_redis_client(app_config)
        mock_redis_class_2.assert_not_called()
        assert result2 == mock_redis


@patch("common.redis_client", None)
@patch("common.Redis")
@patch("common.DefaultAzureCredential")
def test_get_redis_client_azure(
    mock_azure_cred, mock_redis_class, app_config, mock_redis
):
    """Test getting Redis client with Azure credentials."""
    # Setup
    mock_redis_class.return_value = mock_redis
    mock_cred = MagicMock()
    mock_azure_cred.return_value = mock_cred
    mock_cred.get_token.return_value.token = "azure-token"

    app_config_azure = app_config.model_copy(deep=True)
    app_config_azure.redis.host = "test.windows.net"

    # Execute
    result = get_redis_client(app_config_azure)

    # Assert
    assert result == mock_redis
    mock_azure_cred.assert_called_once()
    mock_cred.get_token.assert_called_once_with("https://redis.azure.com/.default")
    assert app_config_azure.redis.password == "azure-token"
    mock_redis_class.assert_called_once()


def test_validate_key():
    """Test key validation function."""
    # Test valid context key
    key_type, plan_id, file_path, step_id = validate_key(
        "context|123e4567-e89b-12d3-a456-426614174000|file.txt"
    )
    assert key_type == "context"
    assert plan_id == "123e4567-e89b-12d3-a456-426614174000"
    assert file_path == "file.txt"
    assert step_id == ""

    # Test valid plan key
    key_type, plan_id, file_path, step_id = validate_key(
        "plan|123e4567-e89b-12d3-a456-426614174000"
    )
    assert key_type == "plan"
    assert plan_id == "123e4567-e89b-12d3-a456-426614174000"
    assert file_path == ""
    assert step_id == ""

    # Test valid blackboard key
    key_type, plan_id, file_path, step_id = validate_key(
        "blackboard|123e4567-e89b-12d3-a456-426614174000"
    )
    assert key_type == "blackboard"
    assert plan_id == "123e4567-e89b-12d3-a456-426614174000"
    assert file_path == ""
    assert step_id == ""

    # Test valid result key
    key_type, plan_id, file_path, step_id = validate_key(
        "result|123e4567-e89b-12d3-a456-426614174000|agent1|step1"
    )
    assert key_type == "result"
    assert plan_id == "123e4567-e89b-12d3-a456-426614174000"
    assert file_path == "agent1"
    assert step_id == "step1"

    # Test invalid key type
    with pytest.raises(ValueError, match="Key must start with"):
        validate_key("invalid|123e4567-e89b-12d3-a456-426614174000|file.txt")

    # Test invalid plan key format
    with pytest.raises(ValueError, match="Plan or blackboard must be in the format"):
        validate_key("plan|123e4567-e89b-12d3-a456-426614174000|extra")

    # Test invalid context key format
    with pytest.raises(ValueError, match="Context key must be in the format"):
        validate_key("context|123e4567-e89b-12d3-a456-426614174000")

    # Test invalid result key format
    with pytest.raises(ValueError, match="Result key must be in the format"):
        validate_key("result|123e4567-e89b-12d3-a456-426614174000|agent1")

    # Test invalid UUID
    with pytest.raises(ValueError, match="Plan ID must be a valid UUID"):
        validate_key("context|invalid-uuid|file.txt")

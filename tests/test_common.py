# type: ignore
from unittest.mock import patch

import pytest  # noqa F401

from common import (
    get_app_config,
    get_converter_opts,
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


def test_get_storage_opts_gcs(app_config):
    """Test getting storage options for GCS protocol."""
    # Setup & Execute
    result = get_storage_opts("gcs://bucket/path/to/file.pdf", app_config)

    # Assert
    assert result is not None
    assert result == app_config.storage.gcs


def test_get_storage_opts_sftp(app_config):
    """Test getting storage options for SFTP protocol."""
    # Setup & Execute
    result = get_storage_opts("sftp://server/path/to/file.pdf", app_config)

    # Assert
    assert result is not None
    assert result == app_config.storage.sftp


def test_get_storage_opts_smb(app_config):
    """Test getting storage options for SMB protocol."""
    # Setup & Execute
    result = get_storage_opts("smb://server/path/to/file.pdf", app_config)

    # Assert
    assert result is not None
    assert result == app_config.storage.smb


def test_get_storage_opts_unsupported(app_config):
    """Test getting storage options for unsupported protocol."""
    # Setup & Execute & Assert
    with pytest.raises(ValueError, match="Unsupported protocol"):
        get_storage_opts("unknown://path/to/file.pdf", app_config)


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

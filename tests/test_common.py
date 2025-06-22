# type: ignore
from unittest.mock import patch

import pytest  # noqa F401

from nexus.common import (
    get_converter_opts,
    get_settings,
    get_storage_opts,
    load_config,
    validate_key,
)


@patch("nexus.common.settings", None)
@patch("nexus.common.Environment")
@patch("nexus.common.yaml.safe_load")
def test_load_config(mock_yaml_load, mock_env, settings):
    """Test loading configuration from environment variables."""
    # Setup
    mock_env.return_value.get_template.return_value.render.return_value = "config_yaml"
    mock_yaml_load.return_value = settings.model_dump()

    # Execute
    result = load_config(".env.test")

    # Assert
    assert result is not None
    assert result.cache_path == settings.cache_path
    assert result.mcp_transport == settings.mcp_transport


@patch("nexus.common.settings", None)
@patch("nexus.common.load_config")
def test_get_settings(mock_load_config, settings):
    """Test getting application settings."""
    # Setup
    mock_load_config.return_value = settings

    # Execute
    result = get_settings()

    # Assert
    assert result is not None
    assert result == settings

    # Test caching
    with patch("nexus.common.load_config") as mock_load_config_2:
        result2 = get_settings()
        mock_load_config_2.assert_not_called()
        assert result2 == settings


def test_get_converter_opts(settings):
    """Test getting converter options."""
    # Test PDF file
    result_pdf = get_converter_opts("file:///path/to/file.pdf", settings)
    assert result_pdf is not None
    assert "docintel_endpoint" in result_pdf
    assert result_pdf["docintel_endpoint"] == settings.converter.azure_document_endpoint

    # Test image file
    result_img = get_converter_opts("file:///path/to/file.png", settings)
    assert result_img is not None
    assert "llm_model" in result_img
    assert result_img["llm_model"] == settings.converter.openai_default_model

    # Test other file format
    result_other = get_converter_opts("file:///path/to/file.txt", settings)
    assert result_other is not None
    assert "enable_plugins" in result_other
    assert result_other["enable_plugins"] is True


def test_get_storage_opts_file(settings):
    """Test getting storage options for file protocol."""
    # Setup & Execute
    result = get_storage_opts("file:///path/to/file.pdf", settings)

    # Assert
    assert result == {}


def test_get_storage_opts_s3(settings):
    """Test getting storage options for S3 protocol."""
    # Setup & Execute
    result = get_storage_opts("s3://bucket/path/to/file.pdf", settings)

    # Assert
    assert result is not None
    assert result == settings.storage.s3


def test_get_storage_opts_abfs(settings):
    """Test getting storage options for ABFS protocol."""
    # Setup & Execute
    result = get_storage_opts("abfs://container/path/to/file.pdf", settings)

    # Assert
    assert result is not None
    assert result == settings.storage.abfs


def test_get_storage_opts_gcs(settings):
    """Test getting storage options for GCS protocol."""
    # Setup & Execute
    result = get_storage_opts("gcs://bucket/path/to/file.pdf", settings)

    # Assert
    assert result is not None
    assert result == settings.storage.gcs


def test_get_storage_opts_sftp(settings):
    """Test getting storage options for SFTP protocol."""
    # Setup & Execute
    result = get_storage_opts("sftp://server/path/to/file.pdf", settings)

    # Assert
    assert result is not None
    assert result == settings.storage.sftp


def test_get_storage_opts_smb(settings):
    """Test getting storage options for SMB protocol."""
    # Setup & Execute
    result = get_storage_opts("smb://server/path/to/file.pdf", settings)

    # Assert
    assert result is not None
    assert result == settings.storage.smb


def test_get_storage_opts_unsupported(settings):
    """Test getting storage options for unsupported protocol."""
    # Setup & Execute & Assert
    with pytest.raises(ValueError, match="Unsupported protocol"):
        get_storage_opts("unknown://path/to/file.pdf", settings)


def test_validate_key_plan():
    """Test validating a plan key."""
    # Setup
    key = "plan|123e4567-e89b-12d3-a456-426614174000"

    # Execute
    key_type, plan_id, file_path, step_id = validate_key(key)

    # Assert
    assert key_type == "plan"
    assert plan_id == "123e4567-e89b-12d3-a456-426614174000"
    assert file_path == ""
    assert step_id == ""


def test_validate_key_blackboard():
    """Test validating a blackboard key."""
    # Setup
    key = "blackboard|123e4567-e89b-12d3-a456-426614174000"

    # Execute
    key_type, plan_id, file_path, step_id = validate_key(key)

    # Assert
    assert key_type == "blackboard"
    assert plan_id == "123e4567-e89b-12d3-a456-426614174000"
    assert file_path == ""
    assert step_id == ""


def test_validate_key_context():
    """Test validating a context key."""
    # Setup
    key = "context|123e4567-e89b-12d3-a456-426614174000|file:///path/to/file.pdf"

    # Execute
    key_type, plan_id, file_path, step_id = validate_key(key)

    # Assert
    assert key_type == "context"
    assert plan_id == "123e4567-e89b-12d3-a456-426614174000"
    assert file_path == "file:///path/to/file.pdf"
    assert step_id == ""


def test_validate_key_result():
    """Test validating a result key."""
    # Setup
    key = "result|123e4567-e89b-12d3-a456-426614174000|agent_name|1"

    # Execute
    key_type, plan_id, file_path, step_id = validate_key(key)

    # Assert
    assert key_type == "result"
    assert plan_id == "123e4567-e89b-12d3-a456-426614174000"
    assert file_path == "agent_name"
    assert step_id == "1"


def test_validate_key_invalid_type():
    """Test validating a key with an invalid type."""
    # Setup
    key = "invalid|123e4567-e89b-12d3-a456-426614174000"

    # Execute & Assert
    with pytest.raises(
        ValueError,
        match="Key must start with 'result', 'context', 'plan', or 'blackboard'",
    ):
        validate_key(key)


def test_validate_key_invalid_plan_format():
    """Test validating a plan key with an invalid format."""
    # Setup
    key = "plan|123e4567-e89b-12d3-a456-426614174000|extra"

    # Execute & Assert
    with pytest.raises(
        ValueError,
        match="Plan or blackboard must be in the format 'plan|<plan_id>' "
        "or 'blackboard|<plan_id>'",
    ):
        validate_key(key)


def test_validate_key_invalid_context_format():
    """Test validating a context key with an invalid format."""
    # Setup
    key = "context|123e4567-e89b-12d3-a456-426614174000"

    # Execute & Assert
    with pytest.raises(
        ValueError,
        match=(
            "Context key must be in the format 'context|<plan_id>|<file_path_or_url>'"
        ),
    ):
        validate_key(key)


def test_validate_key_invalid_result_format():
    """Test validating a result key with an invalid format."""
    # Setup
    key = "result|123e4567-e89b-12d3-a456-426614174000|agent_name"

    # Execute & Assert
    with pytest.raises(
        ValueError,
        match=(
            "Result key must be in the format 'result|<plan_id>|<agent_name>|<step id>'"
        ),
    ):
        validate_key(key)


def test_validate_key_invalid_uuid():
    """Test validating a key with an invalid UUID."""
    # Setup
    key = "plan|invalid-uuid"

    # Execute & Assert
    with pytest.raises(ValueError):
        validate_key(key)

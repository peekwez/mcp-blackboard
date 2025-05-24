# type: ignore
import os
import uuid
from unittest.mock import MagicMock, patch

import pytest
import yaml

from common import (
    get_app_config,
    get_converter_opts,
    get_storage_opts,
    load_config,
    validate_key,
)
from models import AppConfig


class TestLoadConfig:
    """Test the load_config function."""

    def test_load_config_success(self, temp_env_file: str, mock_app_config: AppConfig):
        """Test successful config loading."""
        with (
            patch("common.load_dotenv"),
            patch("common.Path"),
            patch("common.Environment") as mock_env,
            patch("common.yaml.safe_load") as mock_yaml_load,
            patch("common.AppConfig.model_validate") as mock_validate,
        ):
            mock_template = MagicMock()
            mock_template.render.return_value = "test_yaml_content"
            mock_env_instance = MagicMock()
            mock_env_instance.get_template.return_value = mock_template
            mock_env.return_value = mock_env_instance

            mock_yaml_load.return_value = {"test": "config"}
            mock_validate.return_value = mock_app_config

            result = load_config(temp_env_file)

            assert result == mock_app_config
            mock_template.render.assert_called_once_with(env=os.environ)

    def test_load_config_file_not_found(self):
        """Test config loading with missing file."""
        with patch("common.load_dotenv") as mock_load_dotenv:
            mock_load_dotenv.side_effect = FileNotFoundError("File not found")

            with pytest.raises(FileNotFoundError):
                load_config("nonexistent.env")

    def test_load_config_invalid_yaml(self, temp_env_file: str):
        """Test config loading with invalid YAML."""
        with (
            patch("common.load_dotenv"),
            patch("common.Path"),
            patch("common.Environment") as mock_env,
            patch("common.yaml.safe_load") as mock_yaml_load,
        ):
            mock_template = MagicMock()
            mock_template.render.return_value = "invalid: yaml: content:"
            mock_env_instance = MagicMock()
            mock_env_instance.get_template.return_value = mock_template
            mock_env.return_value = mock_env_instance

            mock_yaml_load.side_effect = yaml.YAMLError("Invalid YAML")

            with pytest.raises(yaml.YAMLError):
                load_config(temp_env_file)


class TestGetAppConfig:
    """Test the get_app_config function."""

    def test_get_app_config_first_call(
        self, mock_app_config: AppConfig, temp_env_file: str
    ):
        """Test first call to get_app_config loads config."""
        with patch("common.load_config") as mock_load_config:
            mock_load_config.return_value = mock_app_config

            result = get_app_config()

            assert result == mock_app_config
            mock_load_config.assert_called_once_with(".env")

    def test_get_app_config_subsequent_calls(self, mock_app_config: AppConfig):
        """Test subsequent calls return cached config."""
        with patch("common.load_config") as mock_load_config:
            mock_load_config.return_value = mock_app_config

            # First call
            result1 = get_app_config()
            # Second call
            result2 = get_app_config()

            assert result1 == result2 == mock_app_config
            # load_config should only be called once
            assert mock_load_config.call_count == 1


class TestGetConverterOpts:
    """Test the get_converter_opts function."""

    @patch("common.ConverterParams")
    @patch("common.OpenAI")
    def test_get_converter_opts_image_url(
        self,
        mock_openai_class: MagicMock,
        mock_converter_params: MagicMock,
        mock_app_config: AppConfig,
    ):
        """Test converter options for image URLs."""
        url = "https://example.com/image.png"

        # Mock the OpenAI instance
        mock_openai_instance = MagicMock()
        mock_openai_class.return_value = mock_openai_instance

        # Mock the ConverterParams instance
        mock_params_instance = MagicMock()
        mock_params_instance.model_dump.return_value = {
            "enable_plugins": False,
            "llm_client": mock_openai_instance,
            "llm_model": "gpt-4o",
            "docintel_endpoint": None,
        }
        mock_converter_params.return_value = mock_params_instance

        result = get_converter_opts(url, mock_app_config)

        assert result["enable_plugins"] is False
        assert result["llm_client"] is mock_openai_instance
        assert result["llm_model"] == "gpt-4o"
        assert result["docintel_endpoint"] is None

        # Verify OpenAI was called with correct parameters
        mock_openai_class.assert_called_once_with(
            api_key=mock_app_config.converter.openai_api_key,
            base_url=mock_app_config.converter.openai_api_base,
        )

    def test_get_converter_opts_pdf_url(self, mock_app_config: AppConfig):
        """Test converter options for PDF URLs."""
        url = "https://example.com/document.pdf"

        result = get_converter_opts(url, mock_app_config)

        assert result["enable_plugins"] is False
        assert result["llm_client"] is None
        assert result["llm_model"] == "gpt-4o"
        assert (
            result["docintel_endpoint"]
            == mock_app_config.converter.azure_document_endpoint
        )

    def test_get_converter_opts_other_url(self, mock_app_config: AppConfig):
        """Test converter options for other file types."""
        url = "https://example.com/document.txt"

        result = get_converter_opts(url, mock_app_config)

        assert result["enable_plugins"] is True
        assert result["llm_client"] is None
        assert result["llm_model"] == "gpt-4o"
        assert result["docintel_endpoint"] is None


class TestGetStorageOpts:
    """Test the get_storage_opts function."""

    def test_get_storage_opts_s3(self, mock_app_config: AppConfig):
        """Test storage options for S3 URLs."""
        url = "s3://bucket/file.txt"

        result = get_storage_opts(url, mock_app_config)

        assert result == mock_app_config.storage.s3

    def test_get_storage_opts_abfs(self, mock_app_config: AppConfig):
        """Test storage options for Azure Blob Storage URLs."""
        url = "abfs://container/file.txt"

        result = get_storage_opts(url, mock_app_config)

        assert result == mock_app_config.storage.abfs

    def test_get_storage_opts_gcs(self, mock_app_config: AppConfig):
        """Test storage options for Google Cloud Storage URLs."""
        url = "gcs://bucket/file.txt"

        result = get_storage_opts(url, mock_app_config)

        assert result == mock_app_config.storage.gcs

    def test_get_storage_opts_sftp(self, mock_app_config: AppConfig):
        """Test storage options for SFTP URLs."""
        url = "sftp://server/file.txt"

        result = get_storage_opts(url, mock_app_config)

        assert result == mock_app_config.storage.sftp

    def test_get_storage_opts_smb(self, mock_app_config: AppConfig):
        """Test storage options for SMB URLs."""
        url = "smb://server/file.txt"

        result = get_storage_opts(url, mock_app_config)

        assert result == mock_app_config.storage.smb

    def test_get_storage_opts_file(self, mock_app_config: AppConfig):
        """Test storage options for local file URLs."""
        url = "file:///tmp/file.txt"

        result = get_storage_opts(url, mock_app_config)

        assert result == {}

    def test_get_storage_opts_https(self, mock_app_config: AppConfig):
        """Test storage options for HTTPS URLs."""
        url = "https://example.com/file.txt"

        result = get_storage_opts(url, mock_app_config)

        assert result == {}

    def test_get_storage_opts_unsupported_protocol(self, mock_app_config: AppConfig):
        """Test storage options for unsupported protocols."""
        url = "ftp://server/file.txt"

        with pytest.raises(ValueError, match="Unsupported protocol: ftp"):
            get_storage_opts(url, mock_app_config)


class TestValidateKey:
    """Test the validate_key function."""

    def test_validate_key_plan(self):
        """Test validating a plan key."""
        plan_id = str(uuid.uuid4())
        key = f"plan|{plan_id}"

        result = validate_key(key)

        assert result == ("plan", plan_id, None, None)

    def test_validate_key_blackboard(self):
        """Test validating a blackboard key."""
        plan_id = str(uuid.uuid4())
        key = f"blackboard|{plan_id}"

        result = validate_key(key)

        assert result == ("blackboard", plan_id, None, None)

    def test_validate_key_context(self):
        """Test validating a context key."""
        plan_id = str(uuid.uuid4())
        file_path = "file:///tmp/test.txt"
        key = f"context|{plan_id}|{file_path}"

        result = validate_key(key)

        assert result == ("context", plan_id, file_path, None)

    def test_validate_key_result(self):
        """Test validating a result key."""
        plan_id = str(uuid.uuid4())
        agent_name = "researcher"
        step_id = "1"
        key = f"result|{plan_id}|{step_id}|{agent_name}"

        result = validate_key(key)

        assert result == ("result", plan_id, step_id, agent_name)

    def test_validate_key_invalid_prefix(self):
        """Test validating a key with invalid prefix."""
        plan_id = str(uuid.uuid4())
        key = f"invalid|{plan_id}"

        with pytest.raises(ValueError, match="Key must start with"):
            validate_key(key)

    def test_validate_key_plan_wrong_format(self):
        """Test validating a plan key with wrong format."""
        plan_id = str(uuid.uuid4())
        key = f"plan|{plan_id}|extra"

        with pytest.raises(
            ValueError, match="Plan or blackboard must be in the format"
        ):
            validate_key(key)

    def test_validate_key_context_wrong_format(self):
        """Test validating a context key with wrong format."""
        plan_id = str(uuid.uuid4())
        key = f"context|{plan_id}"

        with pytest.raises(ValueError, match="Context key must be in the format"):
            validate_key(key)

    def test_validate_key_result_wrong_format(self):
        """Test validating a result key with wrong format."""
        plan_id = str(uuid.uuid4())
        key = f"result|{plan_id}|agent"

        with pytest.raises(ValueError, match="Result key must be in the format"):
            validate_key(key)

    def test_validate_key_invalid_uuid(self):
        """Test validating a key with invalid UUID."""
        key = "plan|invalid-uuid"

        with pytest.raises(ValueError, match="Plan ID must be a valid UUID"):
            validate_key(key)

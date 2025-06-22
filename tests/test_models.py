# type: ignore
import pytest  # noqa F401
from pydantic import ValidationError

from nexus.models import (
    ConverterParams,
    ConverterSettings,
    RedisSettings,
    Settings,
    StorageSettings,
    WebSettings,
)


def test_redis_settings_validation():
    """Test RedisSettings validation."""
    # Valid configuration
    config = RedisSettings(host="localhost", port=6379, db=0)
    assert config.host == "localhost"
    assert config.port == 6379
    assert config.db == 0
    assert config.password is None  # Default value
    assert config.decode_responses is True  # Default value

    # Invalid port
    with pytest.raises(ValidationError):
        RedisSettings(host="localhost", port="invalid")

    # Invalid db
    with pytest.raises(ValidationError):
        RedisSettings(host="localhost", port=6379, db="invalid")


def test_converter_settings_validation():
    """Test ConverterSettings validation."""
    # Valid configuration
    config = ConverterSettings(
        azure_document_endpoint="https://example.com/document",
        openai_api_key="test-key",
        openai_api_base="https://api.openai.com/v1",
        openai_default_model="gpt-4o",
    )
    assert config.azure_document_endpoint == "https://example.com/document"
    assert config.openai_api_key == "test-key"
    assert config.openai_api_base == "https://api.openai.com/v1"
    assert config.openai_default_model == "gpt-4o"


def test_storage_settings_validation():
    """Test StorageSettings validation."""
    # Valid configuration with empty options
    config = StorageSettings(
        abfs={},
        s3={},
        gcs={},
        sftp={},
        smb={},
    )
    assert isinstance(config.abfs, dict)
    assert isinstance(config.s3, dict)
    assert isinstance(config.gcs, dict)
    assert isinstance(config.sftp, dict)
    assert isinstance(config.smb, dict)

    # Valid configuration with actual options
    config = StorageSettings(
        abfs={"account_name": "test-account"},
        s3={"key": "test-key", "secret": "test-secret"},
        gcs={},
        sftp={},
        smb={},
    )
    assert config.abfs["account_name"] == "test-account"
    assert config.s3["key"] == "test-key"
    assert config.s3["secret"] == "test-secret"


def test_web_settings_validation():
    """Test WebSettings validation."""
    # Valid configuration
    config = WebSettings(
        tavily_api_key="test-key",
        tavily_api_base="https://api.tavily.com/v1",
        tavily_timeout=3000,
        tavily_max_results=10,
    )
    assert config.tavily_api_key == "test-key"
    assert config.tavily_api_base == "https://api.tavily.com/v1"
    assert config.tavily_timeout == 3000
    assert config.tavily_max_results == 10


def test_settings_validation():
    """Test Settings validation."""
    # Valid configuration
    config = Settings(
        cache_path="file:///tmp/cache",
        mcp_transport="stdio",
        redis=RedisSettings(host="localhost", port=6379, db=0),
        storage=StorageSettings(abfs={}, s3={}, gcs={}, sftp={}, smb={}),
        converter=ConverterSettings(
            azure_document_endpoint="https://example.com/document",
            openai_api_key="test-key",
            openai_api_base="https://api.openai.com/v1",
            openai_default_model="gpt-4o",
        ),
        web=WebSettings(
            tavily_api_key="test-key",
            tavily_api_base="https://api.tavily.com/v1",
        ),
    )
    assert config.cache_path == "file:///tmp/cache"
    assert config.mcp_transport == "stdio"
    assert isinstance(config.redis, RedisSettings)
    assert isinstance(config.storage, StorageSettings)
    assert isinstance(config.converter, ConverterSettings)
    assert isinstance(config.web, WebSettings)

    # Valid configuration with SSE transport
    config = Settings(
        cache_path="file:///tmp/cache",
        mcp_transport="sse",
        redis=RedisSettings(host="localhost", port=6379, db=0),
        storage=StorageSettings(abfs={}, s3={}, gcs={}, sftp={}, smb={}),
        converter=ConverterSettings(),
        web=WebSettings(),
    )
    assert config.mcp_transport == "sse"


def test_converter_params():
    """Test ConverterParams model."""
    # Test with default values
    params = ConverterParams()
    assert params.enable_plugins is False
    assert params.llm_client is None
    assert params.llm_model is None
    assert params.docintel_endpoint is None

    # Test with custom values
    from openai import OpenAI

    client = OpenAI(api_key="test-key")
    params = ConverterParams(
        enable_plugins=True,
        llm_client=client,
        llm_model="gpt-4o",
        docintel_endpoint="https://example.com/document",
    )
    assert params.enable_plugins is True
    assert params.llm_client == client
    assert params.llm_model == "gpt-4o"
    assert params.docintel_endpoint == "https://example.com/document"


def test_state_updates_enum():
    """Test the StateUpdates enum."""
    from nexus.models import StateUpdates

    # Test string conversion
    assert str(StateUpdates.write_plan) == "save-plan"
    assert str(StateUpdates.update_status) == "mark-plan-as-completed"
    assert str(StateUpdates.describe_context) == "save-context-description"
    assert str(StateUpdates.write_result) == "save-result"

    # Test string matching
    assert StateUpdates("save-plan") == StateUpdates.write_plan

    # Case sensitivity check
    with pytest.raises(ValueError):
        StateUpdates("SAVE-PLAN")

    assert StateUpdates("mark-plan-as-completed") == StateUpdates.update_status

    # Test invalid value
    with pytest.raises(ValueError):
        StateUpdates("invalid-update")

# type: ignore
import pytest  # noqa F401
from pydantic import ValidationError

from models import (
    AppConfig,
    ConverterConfig,
    ConverterParams,
    RedisConfig,
    StorageConfig,
)


def test_redis_config_validation():
    """Test RedisConfig validation."""
    # Valid configuration
    config = RedisConfig(host="localhost", port=6379, db=0)
    assert config.host == "localhost"
    assert config.port == 6379
    assert config.db == 0
    assert config.password is None  # Default value
    assert config.decode_responses is True  # Default value

    # Invalid port
    with pytest.raises(ValidationError):
        RedisConfig(host="localhost", port="invalid")

    # Invalid db
    with pytest.raises(ValidationError):
        RedisConfig(host="localhost", port=6379, db="invalid")


def test_converter_config_validation():
    """Test ConverterConfig validation."""
    # Valid configuration
    config = ConverterConfig(
        azure_document_endpoint="https://example.com/document",
        openai_api_key="test-key",
        openai_api_base="https://api.openai.com/v1",
        openai_default_model="gpt-4o",
    )
    assert config.azure_document_endpoint == "https://example.com/document"
    assert config.openai_api_key == "test-key"
    assert config.openai_api_base == "https://api.openai.com/v1"
    assert config.openai_default_model == "gpt-4o"


def test_storage_config_validation():
    """Test StorageConfig validation."""
    # Valid configuration with empty options
    config = StorageConfig(
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
    config = StorageConfig(
        abfs={"account_name": "test-account"},
        s3={"key": "test-key", "secret": "test-secret"},
        gcs={},
        sftp={},
        smb={},
    )
    assert config.abfs["account_name"] == "test-account"
    assert config.s3["key"] == "test-key"
    assert config.s3["secret"] == "test-secret"


def test_app_config_validation():
    """Test AppConfig validation."""
    # Valid configuration
    config = AppConfig(
        cache_path="file:///tmp/cache",
        mcp_transport="stdio",
        redis=RedisConfig(host="localhost", port=6379, db=0),
        storage=StorageConfig(abfs={}, s3={}, gcs={}, sftp={}, smb={}),
        converter=ConverterConfig(
            azure_document_endpoint="https://example.com/document",
            openai_api_key="test-key",
            openai_api_base="https://api.openai.com/v1",
            openai_default_model="gpt-4o",
        ),
    )
    assert config.cache_path == "file:///tmp/cache"
    assert config.mcp_transport == "stdio"
    assert isinstance(config.redis, RedisConfig)
    assert isinstance(config.storage, StorageConfig)
    assert isinstance(config.converter, ConverterConfig)

    # Valid configuration with SSE transport
    config = AppConfig(
        cache_path="file:///tmp/cache",
        mcp_transport="sse",
        redis=RedisConfig(host="localhost", port=6379, db=0),
        storage=StorageConfig(abfs={}, s3={}, gcs={}, sftp={}, smb={}),
        converter=ConverterConfig(
            azure_document_endpoint="https://example.com/document",
            openai_api_key="test-key",
            openai_api_base="https://api.openai.com/v1",
            openai_default_model="gpt-4o",
        ),
    )
    assert config.mcp_transport == "sse"

    # Invalid transport
    with pytest.raises(ValidationError):
        AppConfig(
            cache_path="file:///tmp/cache",
            mcp_transport="invalid",
            redis=RedisConfig(host="localhost", port=6379, db=0),
            storage=StorageConfig(abfs={}, s3={}, gcs={}, sftp={}, smb={}),
            converter=ConverterConfig(
                azure_document_endpoint="https://example.com/document",
                openai_api_key="test-key",
                openai_api_base="https://api.openai.com/v1",
                openai_default_model="gpt-4o",
            ),
        )


def test_converter_params():
    """Test ConverterParams model."""
    # Default params
    params = ConverterParams()
    assert params.enable_plugins is False
    assert params.llm_client is None
    assert params.llm_model is None
    assert params.docintel_endpoint is None

    # Custom params
    params = ConverterParams(
        enable_plugins=True,
        llm_model="gpt-4o",
        docintel_endpoint="https://example.com/document",
    )
    assert params.enable_plugins is True
    assert params.llm_model == "gpt-4o"
    assert params.docintel_endpoint == "https://example.com/document"

    # Model dump
    dumped = params.model_dump()
    assert isinstance(dumped, dict)
    assert dumped["enable_plugins"] is True
    assert dumped["llm_model"] == "gpt-4o"
    assert dumped["docintel_endpoint"] == "https://example.com/document"

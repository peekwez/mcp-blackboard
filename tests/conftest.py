# type: ignore
import io
from unittest.mock import MagicMock

import fsspec
import pytest
from redis import Redis

from src.models import AppConfig, ConverterConfig, RedisConfig, StorageConfig


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    mock = MagicMock(spec=Redis)
    return mock


@pytest.fixture
def mock_filesystem():
    """Mock filesystem for testing."""
    mock_fs = MagicMock(spec=fsspec.AbstractFileSystem)
    mock_fs.open.return_value.__enter__.return_value = io.BytesIO(b"test content")
    return mock_fs


@pytest.fixture
def app_config():
    """Create a test AppConfig."""
    return AppConfig(
        cache_path="file:///tmp/test_cache",
        mcp_transport="stdio",
        redis=RedisConfig(
            host="localhost",
            port=6379,
            db=0,
            username=None,
            password=None,
        ),
        storage=StorageConfig(
            abfs={},
            s3={},
            gcs={},
            sftp={},
            smb={},
        ),
        converter=ConverterConfig(
            azure_document_endpoint="https://example.com/document",
            openai_api_key="test-key",
            openai_api_base="https://api.openai.com/v1",
            openai_default_model="gpt-4o",
        ),
    )


@pytest.fixture
def mock_openai():
    """Mock OpenAI client for testing."""
    mock = MagicMock()
    return mock


@pytest.fixture
def mock_markitdown():
    """Mock MarkItDown client for testing."""
    mock = MagicMock()
    mock_instance = mock.return_value
    mock_instance.convert.return_value.markdown = "# Converted markdown"
    return mock


@pytest.fixture
def sample_plan():
    """Sample plan for testing."""
    return {
        "id": "test-plan-1",
        "name": "Test Plan",
        "steps": [
            {"id": "step-1", "name": "Step 1", "status": "pending"},
            {"id": "step-2", "name": "Step 2", "status": "pending"},
        ],
    }

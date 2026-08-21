# type: ignore
import io
from unittest.mock import MagicMock

import fsspec
import pytest
from redis import Redis

from nexus.models import (
    ConverterSettings,
    RedisSettings,
    Settings,
    StorageSettings,
    WebSettings,
)


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
def settings():
    """Create test Settings."""
    return Settings(
        cache_path="file:///tmp/test_cache",
        data_path="file:///tmp/test_data",
        mcp_transport="stdio",
        redis=RedisSettings(
            host="localhost",
            port=6379,
            db=0,
            username=None,
            password=None,
        ),
        storage=StorageSettings(
            abfs={},
            s3={},
            gcs={},
            sftp={},
            smb={},
        ),
        converter=ConverterSettings(
            azure_document_endpoint="https://example.com/document",
            openai_api_key="test-key",
            openai_api_base="https://api.openai.com/v1",
            openai_default_model="gpt-4o",
        ),
        web=WebSettings(
            tavily_api_key="test-key",
            tavily_api_base="https://api.tavily.com/v1",
            tavily_timeout=3000,
            tavily_max_results=10,
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
            {"id": 1, "agent": "researcher", "status": "pending"},
            {"id": 2, "agent": "writer", "status": "pending"},
        ],
    }

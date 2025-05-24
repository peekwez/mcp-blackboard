# type: ignore
import os
import tempfile
from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from redis import Redis

from models import AppConfig, ConverterConfig, RedisConfig, StorageConfig


@pytest.fixture
def mock_redis() -> Generator[MagicMock]:
    """Mock Redis client for testing."""
    with patch("tools.memory.Redis") as mock_redis_class:
        mock_redis_instance = MagicMock(spec=Redis)
        mock_redis_class.return_value = mock_redis_instance
        yield mock_redis_instance


@pytest.fixture
def mock_app_config() -> AppConfig:
    """Create a test configuration."""
    return AppConfig(
        cache_path="file:///tmp/test_cache",
        mcp_transport="stdio",
        redis=RedisConfig(
            host="localhost",
            port=6379,
            db=0,
            username=None,
            password=None,
            ssl=False,
            ssl_ca_path=None,
            ssl_cert_reqs="required",
            ssl_ca_certs=None,
            ssl_certfile=None,
            ssl_keyfile=None,
            socket_timeout=10,
            retry_on_timeout=True,
            max_connections=20,
            decode_responses=True,
        ),
        storage=StorageConfig(
            abfs={"account_name": "test", "account_key": "test"},
            s3={"key": "test", "secret": "test"},
            gcs={"token": "test"},
            sftp={"host": "test", "port": 22, "username": "test", "password": "test"},
            smb={
                "server_name": "test",
                "share_name": "test",
                "username": "test",
                "password": "test",
            },
        ),
        converter=ConverterConfig(
            azure_document_key="test_key",
            azure_document_endpoint="https://test.cognitiveservices.azure.com/",
            openai_api_key="test_key",
            openai_api_base="https://api.openai.com/v1",
            openai_default_model="gpt-4o",
        ),
    )


@pytest.fixture
def temp_env_file() -> Generator[str]:
    """Create a temporary .env file for testing."""
    env_content = """
CACHE_PATH=file:///tmp/test_cache
MCP_TRANSPORT=stdio
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://test.cognitiveservices.azure.com/
OPENAI_API_KEY=test_key
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_DEFAULT_MODEL=gpt-4o
AZURE_STORAGE_ACCOUNT=test
AZURE_STORAGE_KEY=test_key
AWS_ACCESS_KEY_ID=test_key
AWS_SECRET_ACCESS_KEY=test_secret
GOOGLE_APPLICATION_CREDENTIALS=test_token
SFTP_HOST=test_host
SFTP_PORT=22
SFTP_USER=test_user
SFTP_PASS=test_pass
SMB_SERVER=test_server
SMB_SHARE=test_share
SMB_USER=test_user
SMB_PASS=test_pass
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write(env_content)
        f.flush()
        yield f.name

    # Cleanup
    os.unlink(f.name)


@pytest.fixture
def sample_plan_data() -> dict[str, Any]:
    """Sample plan data for testing."""
    return {
        "id": 1,
        "goal": "Test goal",
        "steps": [
            {
                "id": 1,
                "agent": "researcher",
                "prompt": "Test prompt",
                "revision": 1,
                "status": "pending",
                "depends_on": [],
            }
        ],
    }


@pytest.fixture
def mock_filesystem():
    """Mock fsspec filesystem."""
    with patch("tools.context.fsspec.filesystem") as mock_fs:
        mock_fs_instance = MagicMock()
        mock_fs.return_value = mock_fs_instance
        yield mock_fs_instance


@pytest.fixture
def mock_markitdown():
    """Mock MarkItDown converter."""
    with patch("tools.context.markitdown.MarkItDown") as mock_md:
        mock_instance = MagicMock()
        mock_document = MagicMock()
        mock_document.markdown = "# Test Markdown Content"
        mock_instance.convert.return_value = mock_document
        mock_md.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_openai():
    """Mock OpenAI client."""
    with patch("common.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        yield mock_client


@pytest.fixture(autouse=True)
def reset_global_state():
    """Reset global state before each test."""
    # Import here to avoid circular imports
    import common as common
    import tools.memory as memory

    # Reset global variables
    common.app_config = None
    memory.redis_client = None

    yield

    # Clean up after test
    common.app_config = None
    memory.redis_client = None

# type: ignore
import os  # noqa F401
from unittest.mock import MagicMock, patch

import pytest  # noqa F401

from tools.context import (
    _load_cache_file,
    fetch_context,
    get_cache_key,
    get_file_age,
    get_filesystem,
    write_cache_file,
)


def test_get_cache_key():
    """Test generating a cache key for a URL."""
    # Setup & Execute
    key = get_cache_key("s3://bucket/path/to/file.pdf")

    # Assert
    assert isinstance(key, str)
    assert len(key) > 0

    # Test different URLs generate different keys
    key2 = get_cache_key("s3://bucket/path/to/different_file.pdf")
    assert key != key2


@patch("tools.context.get_filesystem")
def test_write_cache_file(mock_get_filesystem, app_config, mock_filesystem):
    """Test writing a file to the cache."""
    # Setup
    mock_get_filesystem.return_value = mock_filesystem
    mock_open = MagicMock()
    mock_filesystem.open.return_value.__enter__.return_value = mock_open

    # Execute
    write_cache_file("s3://bucket/path/to/file.pdf", "Test content", app_config)

    # Assert
    mock_get_filesystem.assert_called_once()
    mock_filesystem.mkdirs.assert_called_once()
    mock_filesystem.open.assert_called_once()
    mock_open.write.assert_called_once_with("Test content")


@patch("tools.context.get_filesystem")
def test_load_cache_file(mock_get_filesystem, app_config, mock_filesystem):
    """Test loading a file from the cache."""
    # Setup
    mock_get_filesystem.return_value = mock_filesystem
    file_like = MagicMock()
    file_like.read.return_value = "Test content"
    mock_filesystem.open.return_value.__enter__.return_value = file_like

    # Execute
    result = _load_cache_file("s3://bucket/path/to/file.pdf", app_config)

    # Assert
    assert result == "Test content"
    mock_get_filesystem.assert_called_once()
    mock_filesystem.open.assert_called_once()


@patch("tools.context.get_app_config")
@patch("tools.context.get_filesystem")
@patch("tools.context.get_converter_opts")
@patch("tools.context.markitdown")
@patch("tools.context.write_cache_file")
def test_fetch_context_fresh(
    mock_write_cache,
    mock_markitdown,
    mock_get_converter_opts,
    mock_get_filesystem,
    mock_get_app_config,
    app_config,
    mock_filesystem,
):
    """Test fetching context from a file, not using cache."""
    # Setup
    mock_get_app_config.return_value = app_config
    mock_get_filesystem.return_value = mock_filesystem
    mock_get_converter_opts.return_value = {"key": "value"}
    mock_filesystem.exists.return_value = False  # Cache miss

    file_like = MagicMock()
    file_like.read.return_value = b"Test content"
    mock_filesystem.open.return_value.__enter__.return_value = file_like

    mock_markitdown_instance = mock_markitdown.MarkItDown.return_value
    mock_markitdown_instance.convert.return_value.markdown = "# Converted markdown"

    # Execute
    result = fetch_context(
        "s3://bucket/path/to/file.pdf", use_cache=True
    )  # Changed to True to test cache writing

    # Assert
    assert result == "# Converted markdown"
    mock_get_app_config.assert_called_once()
    # get_filesystem is called at least twice:
    # 1. To check if cache exists
    # 2. To read the source file
    assert mock_get_filesystem.call_count >= 2
    mock_get_converter_opts.assert_called_once()
    mock_write_cache.assert_called_once()


@patch("tools.context.get_app_config")
@patch("tools.context._load_cache_file")
def test_fetch_context_cached(
    mock_load_cache,
    mock_get_app_config,
    app_config,
    mock_filesystem,
):
    """Test fetching context from cache."""
    # Setup
    mock_get_app_config.return_value = app_config
    # Setup filesystem mock to return cache hit
    mock_get_filesystem = MagicMock()
    mock_get_filesystem.return_value = mock_filesystem
    mock_filesystem.exists.return_value = True

    with patch("tools.context.get_filesystem", mock_get_filesystem):
        mock_load_cache.return_value = "# Cached markdown"

        # Execute
        result = fetch_context("s3://bucket/path/to/file.pdf", use_cache=True)

    # Assert
    assert result == "# Cached markdown"
    mock_get_app_config.assert_called_once()
    mock_load_cache.assert_called_once()


@patch("tools.context.get_app_config")
@patch("tools.context.get_storage_opts")
@patch("tools.context.fsspec.filesystem")
def test_get_filesystem(
    mock_filesystem_fn,
    mock_get_storage_opts,
    mock_get_app_config,
    app_config,
    mock_filesystem,
):
    """Test getting a filesystem for a URL."""
    # Setup
    mock_get_app_config.return_value = app_config
    mock_get_storage_opts.return_value = {"key": "value"}
    mock_filesystem_fn.return_value = mock_filesystem

    # Execute
    result = get_filesystem("s3://bucket/path/to/file.pdf", app_config)

    # Assert
    assert result == mock_filesystem
    # The get_app_config isn't called inside get_filesystem - it's passed as a parameter
    mock_get_storage_opts.assert_called_once()
    mock_filesystem_fn.assert_called_once_with("s3", key="value")


def test_get_file_age():
    """Test calculating file age."""
    # Setup
    file_info = {"ctime": 1620000000.0}  # Some timestamp

    # Execute
    age = get_file_age(file_info)

    # Assert
    assert isinstance(age, int)
    assert age > 0  # The file should be aged since the timestamp is in the past


def test_get_file_age_with_naive_datetime():
    """Test getting file age with naive datetime."""
    # Setup
    import datetime as dt

    # Create a datetime without timezone info
    naive_datetime = dt.datetime.now() - dt.timedelta(hours=1)
    file_info_naive = {"creation_time": naive_datetime}

    # Execute
    age_naive = get_file_age(file_info_naive)

    # Assert - We're just testing that it doesn't crash and returns a positive value
    # The actual value will depend on timezone differences
    assert age_naive > 0


@patch("tools.context.open")
@patch("tools.context.markitdown.MarkItDown")
def test_fetch_context_with_file_error(mock_markitdown, mock_open, app_config):
    """Test error handling when loading a file fails."""
    # Setup
    mock_open.side_effect = Exception("File error")

    # Execute & Assert
    with pytest.raises(OSError, match="Failed to load file from"):
        fetch_context("file:///path/to/file.pdf", use_cache=False)

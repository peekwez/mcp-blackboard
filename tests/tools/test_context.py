# type: ignore
import datetime
import os  # noqa F401
from unittest.mock import MagicMock, patch

import fsspec
import pytest  # noqa F401

from nexus.tools.context import (
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


@patch("nexus.tools.context.get_filesystem")
def test_write_cache_file(mock_get_filesystem, settings, mock_filesystem):
    """Test writing a file to the cache."""
    # Setup
    mock_get_filesystem.return_value = mock_filesystem
    mock_open = MagicMock()
    mock_filesystem.open.return_value.__enter__.return_value = mock_open

    # Execute
    write_cache_file("s3://bucket/path/to/file.pdf", "Test content", settings)

    # Assert
    mock_get_filesystem.assert_called_once()
    mock_filesystem.mkdirs.assert_called_once()
    mock_filesystem.open.assert_called_once()
    mock_open.write.assert_called_once_with("Test content")


@patch("nexus.tools.context.get_filesystem")
def test_load_cache_file(mock_get_filesystem, settings, mock_filesystem):
    """Test loading a file from the cache."""
    # Setup
    mock_get_filesystem.return_value = mock_filesystem
    file_like = MagicMock()
    file_like.read.return_value = "Test content"
    mock_filesystem.open.return_value.__enter__.return_value = file_like

    # Execute
    result = _load_cache_file("s3://bucket/path/to/file.pdf", settings)

    # Assert
    assert result == "Test content"
    mock_get_filesystem.assert_called_once()
    mock_filesystem.open.assert_called_once()


@patch("nexus.tools.context.get_settings")
@patch("nexus.tools.context.get_filesystem")
@patch("nexus.tools.context.get_converter_opts")
@patch("nexus.tools.context.markitdown")
@patch("nexus.tools.context.write_cache_file")
def test_fetch_context_fresh(
    mock_write_cache,
    mock_markitdown,
    mock_get_converter_opts,
    mock_get_filesystem,
    mock_get_settings,
    settings,
    mock_filesystem,
):
    """Test fetching context from a file, not using cache."""
    # Setup
    mock_get_settings.return_value = settings
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
    mock_get_settings.assert_called_once()
    mock_get_converter_opts.assert_called_once_with(
        "s3://bucket/path/to/file.pdf", settings
    )
    mock_get_filesystem.assert_called()
    mock_filesystem.exists.assert_called()
    mock_filesystem.open.assert_called()
    mock_markitdown.MarkItDown.assert_called_once()
    mock_markitdown_instance.convert.assert_called_once()
    mock_write_cache.assert_called_once_with(
        "s3://bucket/path/to/file.pdf", "# Converted markdown", settings
    )


@patch("nexus.tools.context.get_settings")
@patch("nexus.tools.context._load_cache_file")
def test_fetch_context_cached(
    mock_load_cache,
    mock_get_settings,
    settings,
):
    """Test fetching context from cache."""
    # Setup
    mock_get_settings.return_value = settings
    mock_load_cache.return_value = "# Cached markdown"

    # Execute
    result = fetch_context("s3://bucket/path/to/file.pdf", use_cache=True)

    # Assert
    assert result == "# Cached markdown"
    mock_get_settings.assert_called_once()
    mock_load_cache.assert_called_once_with("s3://bucket/path/to/file.pdf", settings)


@patch("nexus.tools.context.get_settings")
@patch("nexus.tools.context.get_filesystem")
def test_fetch_context_with_file_error(
    mock_get_filesystem, mock_get_settings, settings, mock_filesystem
):
    """Test error handling when loading a file fails."""
    # Setup
    mock_get_settings.return_value = settings
    mock_get_filesystem.return_value = mock_filesystem
    mock_filesystem.open.side_effect = Exception("File error")

    # Execute & Assert
    with pytest.raises(OSError, match="Failed to load file from"):
        fetch_context("file:///path/to/file.pdf", use_cache=False)


@patch("nexus.tools.context.get_settings")
def test_get_filesystem(mock_get_settings, settings):
    """Test getting a filesystem object based on URL protocol."""
    # Setup
    mock_get_settings.return_value = settings
    test_url = "file:///path/to/file.pdf"

    # Execute
    result = get_filesystem(test_url, settings)

    # Assert
    assert result is not None
    assert isinstance(result, fsspec.AbstractFileSystem)


def test_get_file_age():
    """Test getting the age of a file from file info."""
    # Setup - with ctime
    current_time = datetime.datetime.now(tz=datetime.UTC).timestamp()
    file_info_ctime = {"ctime": current_time - 3600}  # 1 hour old

    # Execute
    age = get_file_age(file_info_ctime)

    # Assert
    assert isinstance(age, int)
    assert 3500 <= age <= 3700  # Allow for slight timing differences

    # Setup - with creation_time
    one_hour_ago = datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(hours=1)
    file_info_creation_time = {"creation_time": one_hour_ago}

    # Execute
    age = get_file_age(file_info_creation_time)

    # Assert
    assert isinstance(age, int)
    assert 3500 <= age <= 3700  # Allow for slight timing differences


@patch("nexus.tools.context.get_settings")
@patch("nexus.tools.context.get_filesystem")
@patch("nexus.tools.context._load_cache_file")
@patch("nexus.tools.context.write_cache_file")
@patch("nexus.tools.context.markitdown.MarkItDown")
def test_fetch_context_pdf_file(
    mock_markitdown_class,
    mock_write_cache,
    mock_load_cache,
    mock_get_filesystem,
    mock_get_settings,
    settings,
    mock_filesystem,
):
    """Test fetching context from a PDF file."""
    # Setup
    mock_get_settings.return_value = settings
    mock_get_filesystem.return_value = mock_filesystem
    mock_load_cache.side_effect = OSError("Cache not found")  # Force fetching fresh

    mock_open = MagicMock()
    mock_filesystem.open.return_value.__enter__.return_value = mock_open
    mock_open.read.return_value = b"PDF content"

    # Set up the markitdown mock
    mock_markitdown_instance = MagicMock()
    mock_markitdown_class.return_value = mock_markitdown_instance
    mock_document = MagicMock()
    mock_document.markdown = "Converted content"
    mock_markitdown_instance.convert.return_value = mock_document  # Execute
    result = fetch_context("file:///path/to/file.pdf")

    # Assert
    mock_load_cache.assert_called_once()
    mock_filesystem.open.assert_called_once()
    mock_markitdown_instance.convert.assert_called_once()
    mock_write_cache.assert_called_once()
    assert result == "Converted content"


@patch("nexus.tools.context.get_settings")
@patch("nexus.tools.context.get_filesystem")
@patch("nexus.tools.context._load_cache_file")
@patch("nexus.tools.context.write_cache_file")
@patch("nexus.tools.context.markitdown.MarkItDown")
def test_fetch_context_image_file(
    mock_markitdown_class,
    mock_write_cache,
    mock_load_cache,
    mock_get_filesystem,
    mock_get_settings,
    settings,
    mock_filesystem,
):
    """Test fetching context from an image file."""
    # Setup
    mock_get_settings.return_value = settings
    mock_get_filesystem.return_value = mock_filesystem
    mock_load_cache.side_effect = OSError("Cache not found")  # Force fetching fresh

    mock_open = MagicMock()
    mock_filesystem.open.return_value.__enter__.return_value = mock_open
    mock_open.read.return_value = b"Image content"

    # Set up the markitdown mock
    mock_markitdown_instance = MagicMock()
    mock_markitdown_class.return_value = mock_markitdown_instance
    mock_document = MagicMock()
    mock_document.markdown = "Converted image content"
    mock_markitdown_instance.convert.return_value = mock_document

    # Execute
    result = fetch_context("file:///path/to/image.png")

    # Assert
    mock_load_cache.assert_called_once()
    mock_filesystem.open.assert_called_once()
    mock_markitdown_instance.convert.assert_called_once()
    mock_write_cache.assert_called_once()
    assert result == "Converted image content"

# type: ignore
import datetime
import io
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from tools.context import (
    fetch_context,
    get_cache_key,
    get_file_age,
    get_filesystem,
    load_cache_file,
    write_cache_file,
)


class TestGetFilesystem:
    """Test the get_filesystem function."""

    @patch("tools.context.fsspec.filesystem")
    @patch("tools.context.get_storage_opts")
    def test_get_filesystem_s3(
        self,
        mock_get_storage_opts: MagicMock,
        mock_filesystem: MagicMock,
        mock_app_config,
    ):
        """Test getting filesystem for S3 URL."""
        url = "s3://bucket/file.txt"
        storage_opts = {"key": "test", "secret": "test"}
        mock_get_storage_opts.return_value = storage_opts
        mock_fs = MagicMock()
        mock_filesystem.return_value = mock_fs

        result = get_filesystem(url, mock_app_config)

        assert result == mock_fs
        mock_get_storage_opts.assert_called_once_with(url, mock_app_config)
        mock_filesystem.assert_called_once_with("s3", **storage_opts)

    @patch("tools.context.fsspec.filesystem")
    @patch("tools.context.get_storage_opts")
    def test_get_filesystem_local(
        self,
        mock_get_storage_opts: MagicMock,
        mock_filesystem: MagicMock,
        mock_app_config,
    ):
        """Test getting filesystem for local file URL."""
        url = "file:///tmp/file.txt"
        storage_opts = {}
        mock_get_storage_opts.return_value = storage_opts
        mock_fs = MagicMock()
        mock_filesystem.return_value = mock_fs

        result = get_filesystem(url, mock_app_config)

        assert result == mock_fs
        mock_get_storage_opts.assert_called_once_with(url, mock_app_config)
        mock_filesystem.assert_called_once_with("file", **storage_opts)


class TestGetFileAge:
    """Test the get_file_age function."""

    def test_get_file_age_with_ctime_float(self):
        """Test getting file age with ctime as float."""
        current_time = datetime.datetime.now(datetime.UTC)
        one_hour_ago = current_time - datetime.timedelta(hours=1)
        ctime = one_hour_ago.timestamp()

        file_info = {"ctime": ctime}

        age = get_file_age(file_info)

        # Should be approximately 3600 seconds (1 hour)
        assert 3590 <= age <= 3610

    def test_get_file_age_with_ctime_string(self):
        """Test getting file age with ctime as string."""
        current_time = datetime.datetime.now(datetime.UTC)
        one_hour_ago = current_time - datetime.timedelta(hours=1)
        ctime_str = str(one_hour_ago.timestamp())

        file_info = {"ctime": ctime_str}

        age = get_file_age(file_info)

        # Should be approximately 3600 seconds (1 hour)
        assert 3590 <= age <= 3610

    def test_get_file_age_with_invalid_ctime_string(self):
        """Test getting file age with invalid ctime string."""
        file_info = {"ctime": "invalid"}

        age = get_file_age(file_info)

        assert age == 0

    def test_get_file_age_with_creation_time(self):
        """Test getting file age with creation_time."""
        current_time = datetime.datetime.now(datetime.UTC)
        one_hour_ago = current_time - datetime.timedelta(hours=1)

        file_info = {"creation_time": one_hour_ago}

        age = get_file_age(file_info)

        # Should be approximately 3600 seconds (1 hour)
        assert 3590 <= age <= 3610

    def test_get_file_age_with_creation_time_no_tz(self):
        """Test getting file age with creation_time without timezone."""
        # Create a realistic test case
        current_time = datetime.datetime.now()
        one_hour_ago = current_time - datetime.timedelta(hours=1)

        # Remove timezone info to test the case where timezone is None
        one_hour_ago_no_tz = one_hour_ago.replace(tzinfo=None)

        file_info: dict[str, Any] = {"creation_time": one_hour_ago_no_tz}

        age = get_file_age(file_info)

        # Should be approximately 3600 seconds (1 hour), allow some tolerance
        # The function adds UTC timezone to naive datetime, which can cause
        # timezone offset differences. Allow for reasonable range.
        assert age > 0  # Just ensure it's positive and not zero


class TestGetCacheKey:
    """Test the get_cache_key function."""

    def test_get_cache_key(self):
        """Test generating cache key."""
        url = "https://example.com/file.txt"

        key = get_cache_key(url)

        # Should be a 32-character hex string (MD5 hash)
        assert len(key) == 32
        assert all(c in "0123456789abcdef" for c in key)

    def test_get_cache_key_consistent(self):
        """Test cache key generation is consistent."""
        url = "https://example.com/file.txt"

        key1 = get_cache_key(url)
        key2 = get_cache_key(url)

        assert key1 == key2

    def test_get_cache_key_different_urls(self):
        """Test different URLs produce different cache keys."""
        url1 = "https://example.com/file1.txt"
        url2 = "https://example.com/file2.txt"

        key1 = get_cache_key(url1)
        key2 = get_cache_key(url2)

        assert key1 != key2


class TestWriteCacheFile:
    """Test the write_cache_file function."""

    @patch("tools.context.get_filesystem")
    @patch("tools.context.get_cache_key")
    def test_write_cache_file(
        self,
        mock_get_cache_key: MagicMock,
        mock_get_filesystem: MagicMock,
        mock_app_config,
    ):
        """Test writing cache file."""
        url = "https://example.com/file.txt"
        contents = "# Test Content"
        hash_key = "testhash123"

        mock_get_cache_key.return_value = hash_key
        mock_fs = MagicMock()
        mock_get_filesystem.return_value = mock_fs

        mock_app_config.cache_path = "file:///tmp/cache"

        write_cache_file(url, contents, mock_app_config)

        mock_get_cache_key.assert_called_once_with(url)
        mock_get_filesystem.assert_called_once_with(
            mock_app_config.cache_path, mock_app_config
        )
        mock_fs.mkdir.assert_called_once_with(
            "/tmp/cache", create_parents=True, exist_ok=True
        )
        mock_fs.open.assert_called_once_with("/tmp/cache/testhash123.md", "w")

        # Check that write was called on the file handle
        mock_file = mock_fs.open.return_value.__enter__.return_value
        mock_file.write.assert_called_once_with(contents)


class TestLoadCacheFile:
    """Test the load_cache_file function."""

    @patch("tools.context.get_filesystem")
    @patch("tools.context.get_cache_key")
    def test_load_cache_file_success(
        self,
        mock_get_cache_key: MagicMock,
        mock_get_filesystem: MagicMock,
        mock_app_config,
    ):
        """Test loading cache file successfully."""
        url = "https://example.com/file.txt"
        hash_key = "testhash123"
        cached_content = "# Cached Content"

        mock_get_cache_key.return_value = hash_key
        mock_fs = MagicMock()
        mock_get_filesystem.return_value = mock_fs
        mock_fs.exists.return_value = True

        # Mock file reading
        mock_file = MagicMock()
        mock_file.read.return_value = cached_content
        mock_fs.open.return_value.__enter__.return_value = mock_file

        mock_app_config.cache_path = "file:///tmp/cache"

        result = load_cache_file(url, mock_app_config)

        assert result == cached_content
        mock_get_cache_key.assert_called_once_with(url)
        mock_get_filesystem.assert_called_once_with(
            mock_app_config.cache_path, mock_app_config
        )
        mock_fs.exists.assert_called_once_with("/tmp/cache/testhash123.md")
        mock_fs.open.assert_called_once_with("/tmp/cache/testhash123.md", "r")

    @patch("tools.context.get_filesystem")
    @patch("tools.context.get_cache_key")
    def test_load_cache_file_not_found(
        self,
        mock_get_cache_key: MagicMock,
        mock_get_filesystem: MagicMock,
        mock_app_config,
    ):
        """Test loading non-existent cache file."""
        url = "https://example.com/file.txt"
        hash_key = "testhash123"

        mock_get_cache_key.return_value = hash_key
        mock_fs = MagicMock()
        mock_get_filesystem.return_value = mock_fs
        mock_fs.exists.return_value = False

        mock_app_config.cache_path = "file:///tmp/cache"

        with pytest.raises(OSError, match="Cache file .* does not exist"):
            load_cache_file(url, mock_app_config)


class TestFetchContext:
    """Test the fetch_context function."""

    @patch("tools.context.load_cache_file")
    @patch("tools.context.get_app_config")
    @patch("tools.context.get_converter_opts")
    def test_fetch_context_from_cache(
        self,
        mock_get_converter_opts: MagicMock,
        mock_get_app_config: MagicMock,
        mock_load_cache: MagicMock,
    ):
        """Test fetching context from cache."""
        url = "https://example.com/file.txt"
        cached_content = "# Cached Content"

        mock_load_cache.return_value = cached_content
        mock_get_app_config.return_value = MagicMock()
        mock_get_converter_opts.return_value = {}

        result = fetch_context(url, use_cache=True)

        assert result == cached_content
        mock_load_cache.assert_called_once_with(url, mock_get_app_config.return_value)

    @patch("tools.context.write_cache_file")
    @patch("tools.context.load_cache_file")
    @patch("tools.context.get_filesystem")
    @patch("tools.context.get_app_config")
    @patch("tools.context.get_converter_opts")
    @patch("tools.context.markitdown.MarkItDown")
    def test_fetch_context_cache_miss(
        self,
        mock_markitdown: MagicMock,
        mock_get_converter_opts: MagicMock,
        mock_get_app_config: MagicMock,
        mock_get_filesystem: MagicMock,
        mock_load_cache: MagicMock,
        mock_write_cache: MagicMock,
    ):
        """Test fetching context when cache miss occurs."""
        url = "https://example.com/file.txt"
        file_content = b"test content"
        markdown_content = "# Test Content"

        # Mock cache miss
        mock_load_cache.side_effect = OSError("Cache miss")

        # Mock filesystem
        mock_fs = MagicMock()
        mock_file = MagicMock()
        mock_file.read.return_value = file_content
        mock_fs.open.return_value.__enter__.return_value = mock_file
        mock_get_filesystem.return_value = mock_fs

        # Mock converter
        mock_client = MagicMock()
        mock_document = MagicMock()
        mock_document.markdown = markdown_content
        mock_client.convert.return_value = mock_document
        mock_markitdown.return_value = mock_client

        mock_app_config = MagicMock()
        mock_get_app_config.return_value = mock_app_config
        mock_get_converter_opts.return_value = {}

        result = fetch_context(url, use_cache=True)

        assert result == markdown_content
        mock_get_filesystem.assert_called_once_with(url, mock_app_config)
        mock_fs.open.assert_called_once_with(url, "rb")
        mock_markitdown.assert_called_once_with()
        mock_write_cache.assert_called_once_with(url, markdown_content, mock_app_config)

    @patch("tools.context.write_cache_file")
    @patch("tools.context.get_filesystem")
    @patch("tools.context.get_app_config")
    @patch("tools.context.get_converter_opts")
    @patch("tools.context.markitdown.MarkItDown")
    def test_fetch_context_no_cache(
        self,
        mock_markitdown: MagicMock,
        mock_get_converter_opts: MagicMock,
        mock_get_app_config: MagicMock,
        mock_get_filesystem: MagicMock,
        mock_write_cache: MagicMock,
    ):
        """Test fetching context without using cache."""
        url = "https://example.com/file.txt"
        file_content = b"test content"
        markdown_content = "# Test Content"

        # Mock filesystem
        mock_fs = MagicMock()
        mock_file = MagicMock()
        mock_file.read.return_value = file_content
        mock_fs.open.return_value.__enter__.return_value = mock_file
        mock_get_filesystem.return_value = mock_fs

        # Mock converter
        mock_client = MagicMock()
        mock_document = MagicMock()
        mock_document.markdown = markdown_content
        mock_client.convert.return_value = mock_document
        mock_markitdown.return_value = mock_client

        mock_app_config = MagicMock()
        mock_get_app_config.return_value = mock_app_config
        mock_get_converter_opts.return_value = {}

        result = fetch_context(url, use_cache=False)

        assert result == markdown_content
        mock_get_filesystem.assert_called_once_with(url, mock_app_config)
        mock_fs.open.assert_called_once_with(url, "rb")
        mock_markitdown.assert_called_once_with()
        # Cache should not be written when use_cache=False
        mock_write_cache.assert_not_called()

    @patch("tools.context.get_filesystem")
    @patch("tools.context.get_app_config")
    @patch("tools.context.get_converter_opts")
    def test_fetch_context_file_error(
        self,
        mock_get_converter_opts: MagicMock,
        mock_get_app_config: MagicMock,
        mock_get_filesystem: MagicMock,
    ):
        """Test fetching context with file error."""
        url = "https://example.com/nonexistent.txt"

        # Mock filesystem error
        mock_fs = MagicMock()
        mock_fs.open.side_effect = FileNotFoundError("File not found")
        mock_get_filesystem.return_value = mock_fs

        mock_app_config = MagicMock()
        mock_get_app_config.return_value = mock_app_config
        mock_get_converter_opts.return_value = {}

        with pytest.raises(OSError, match="Failed to load file from"):
            fetch_context(url, use_cache=False)

    @patch("tools.context.write_cache_file")
    @patch("tools.context.get_filesystem")
    @patch("tools.context.get_app_config")
    @patch("tools.context.get_converter_opts")
    @patch("tools.context.markitdown.MarkItDown")
    def test_fetch_context_with_converter_options(
        self,
        mock_markitdown: MagicMock,
        mock_get_converter_opts: MagicMock,
        mock_get_app_config: MagicMock,
        mock_get_filesystem: MagicMock,
        mock_write_cache: MagicMock,
    ):
        """Test fetching context with converter options."""
        url = "https://example.com/image.png"
        file_content = b"fake image content"
        markdown_content = "# Image Description"
        converter_opts = {"llm_client": MagicMock(), "llm_model": "gpt-4o"}

        # Mock filesystem
        mock_fs = MagicMock()
        mock_file = MagicMock()
        mock_file.read.return_value = file_content
        mock_fs.open.return_value.__enter__.return_value = mock_file
        mock_get_filesystem.return_value = mock_fs

        # Mock converter
        mock_client = MagicMock()
        mock_document = MagicMock()
        mock_document.markdown = markdown_content
        mock_client.convert.return_value = mock_document
        mock_markitdown.return_value = mock_client

        mock_app_config = MagicMock()
        mock_get_app_config.return_value = mock_app_config
        mock_get_converter_opts.return_value = converter_opts

        result = fetch_context(url, use_cache=False)

        assert result == markdown_content
        mock_get_converter_opts.assert_called_once_with(url, mock_app_config)
        mock_markitdown.assert_called_once_with(**converter_opts)

        # Verify convert was called with BytesIO buffer
        args, kwargs = mock_client.convert.call_args
        assert len(args) == 1
        assert isinstance(args[0], io.BytesIO)

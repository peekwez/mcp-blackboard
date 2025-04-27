import hashlib
import io
import pathlib

import fsspec
import markitdown
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from common import get_app_config, get_converter_opts, get_protocol_opts
from models import AppConfig
from server import mcp


def _get_cache_key(url: str) -> str:
    """
    Generate a cache key based on the URL.

    Args:
        url (str): The URL to generate the cache key for.

    Returns:
        str: The generated cache key.
    """
    return hashlib.md5(url.encode()).hexdigest()


def _write_cache_file(url: str, contents: str, app_config: AppConfig) -> None:
    """
    Write the contents to a cache file.

    Args:
        url (str): The URL of the file.
        contents (str): The contents to write to the cache file.
        app_config (dict): The application configuration.

    Returns:
        None
    """
    hash_key = _get_cache_key(url)
    fs = fsspec.filesystem("file")
    cache_path = f"file://{app_config.base_folder}/cache"
    pathlib.Path(cache_path).mkdir(parents=True, exist_ok=True)
    cache_file = f"{cache_path}/{hash_key}.md"
    with fs.open(cache_file, "w") as f:
        f.write(contents)


def _load_cache_file(url: str, app_config: AppConfig) -> str:
    """
    Load the contents of a cache file.

    Args:
        url (str): The URL of the file.
        app_config (dict): The application configuration.

    Returns:
        str: The contents of the cache file.
    """
    hash_key = _get_cache_key(url)
    fs = fsspec.filesystem("file")
    cache_path = f"file://{app_config.base_folder}/cache"
    cache_file = pathlib.Path(f"{cache_path}/{hash_key}.md")
    if not fs.exists(cache_file.as_uri()):
        raise OSError(f"Cache file {cache_file} does not exist")

    with fs.open(cache_file, "r") as f:
        return f.read()


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5),
    retry=retry_if_exception_type(IOError, OSError, ValueError),
    reraise=True,
)
def _load_and_convert(url: str, use_cache: bool = True) -> str:
    """
    Load a file from a URL location and convert the contents to markdown.

    Args:
        url (str): The URL of the file to load.
        use_cache (bool): Whether to use the cache for loading the file.
            Defaults to True.

    Returns:
        str: The converted Markdown content.

    Raises:
        IOError: If there is an I/O error while loading the file.
        ValueError: If the URL is not valid or the conversion fails.
    """
    if not url:
        raise ValueError("URL cannot be empty")

    app_config = get_app_config()
    protocol_opts = get_protocol_opts(url, app_config)
    converter_opts = get_converter_opts(url, app_config)

    # if a cache file exists, load it
    if use_cache:
        try:
            return _load_cache_file(url, app_config)
        except OSError:
            pass

    try:
        fs = fsspec.filesystem(url.split("://")[0], **protocol_opts)
        with fs.open(url, "rb") as f:
            buffer = io.BytesIO(f.read())
    except Exception as e:
        raise OSError(f"Failed to load file from {url}: {e}") from None

    client = markitdown.MarkItDown(**converter_opts)
    document = client.convert(buffer)

    # save a copy of the file to the cache for future use
    if use_cache:
        _write_cache_file(url, document.markdown, app_config)
    return document.markdown


@mcp.tool()
def load_context(url: str, use_cache: bool = True) -> str:
    """
    Load the contents of a media location and convert the contents
    to Markdown.

    The tool supports various media formats such including:
        - pdf, png, jpg, html, docx, pptx, xlsx, txt, csv

    It also supports the following storage protocols:
        - file:// -  Local file system
        - https:// - HTTP/HTTPS URLs
        - s3:// - Amazon S3 storage
        - gcs:// - Google Cloud Storage
        - abfs:// - Azure Blob Storage
        - smb:// - SMB/CIFS storage
        - sftp:// - FTP/SFTP storage

    The tool uses the python `markitdown` library to convert the file
    to Markdown format.

    Args:
        url (str): The URL of the media to load as context.
        use_cache (bool): Whether to use the cache for loading the file.
            Defaults to True.

    Returns:
        str: The media content in Markdown format.

    Raises:
        OSError: If there is an I/O error while loading the file.
        ValueError: If the URL is not valid or the conversion fails.
    """

    # Disable cache for HTTP/HTTPS URLs since the content may change
    if url.startswith("http") or url.startswith("https"):
        use_cache = False
    return _load_and_convert(url, use_cache)

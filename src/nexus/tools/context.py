# type: ignore
from __future__ import annotations

import base64
import datetime
import hashlib
import io

import fsspec
import markitdown
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from nexus.common import get_converter_opts, get_settings, get_storage_opts
from nexus.logging import get_logger
from nexus.models import Settings


def get_filesystem(url: str, settings: Settings) -> fsspec.AbstractFileSystem:
    """
    Get the filesystem object based on the URL protocol.

    Args:
        url (str): The URL to determine the filesystem for.
        app_config (AppConfig): The application configuration.

    Returns:
        fsspec.AbstractFileSystem: The filesystem object.
    """
    protocol, _ = url.split("://")
    storage_options = get_storage_opts(url, settings)
    fs = fsspec.filesystem(protocol, **storage_options)
    return fs


def get_file_age(file_info: dict[str, str | int | float]) -> int:
    """
    Get the age of a file.

    Args:
        file_info (dict): The file information dictionary.

    Returns:
        datetime.timedelta: The age of the file.
    """
    created_at = None
    if ctime := file_info.get("ctime"):
        created_at = datetime.datetime.fromtimestamp(ctime, tz=datetime.UTC)
    elif not created_at:
        created_at = file_info.get("creation_time")
        # If created_at doesn't have timezone info but is aware, add UTC
        if created_at and not getattr(created_at, "tzinfo", None):  # pragma: no cover
            created_at = created_at.replace(tzinfo=datetime.UTC)

    current_time = datetime.datetime.now(datetime.UTC)
    delta = current_time - created_at
    return int(delta.total_seconds())


def get_cache_key(url: str) -> str:
    """
    Generate a cache key based on the URL.

    Args:
        url (str): The URL to generate the cache key for.

    Returns:
        str: The generated cache key.
    """
    return hashlib.md5(url.encode()).hexdigest()


def write_cache_file(url: str, contents: str, settings: Settings) -> None:
    """
    Write the contents to a cache file.

    Args:
        url (str): The URL of the file.
        contents (str): The contents to write to the cache file.
        settings (Settings): The application settings.

    Returns:
        None
    """
    logger = get_logger(__name__)
    hash_key = get_cache_key(url)
    _, cache_path = settings.cache_path.split("://")
    fs = get_filesystem(settings.cache_path, settings)
    fs.mkdirs(cache_path, exist_ok=True)
    cache_file = f"{cache_path}/{hash_key}.md"
    with fs.open(cache_file, "w") as f:
        f.write(contents)
    logger.info(f"Cache file written: {cache_file} for URL: {url}")


def _load_cache_file(url: str, settings: Settings) -> str:
    """
    Load the contents of a cache file.

    Args:
        url (str): The URL of the file.
        settings (Settings): The application settings.

    Returns:
        str: The contents of the cache file.
    """
    logger = get_logger(__name__)
    hash_key = get_cache_key(url)
    _, cache_path = settings.cache_path.split("://")
    fs = get_filesystem(settings.cache_path, settings)
    cache_file = f"{cache_path}/{hash_key}.md"
    if not fs.exists(cache_file):
        raise OSError(f"Cache file {cache_file} does not exist")

    with fs.open(cache_file, "r") as f:
        return f.read()
    logger.info(f"Cache file loaded: {cache_file} for URL: {url}")


@retry(
    stop=stop_after_attempt(3),
    wait=wait_random_exponential(multiplier=1, max=15),
    retry=retry_if_exception_type(OSError),
    reraise=True,
)
def fetch_context(file_path_or_url: str, use_cache: bool = True) -> str:
    """
    Load a file from a URL location and convert the contents to markdown.

    Args:
        file_path_or_url (str): The file path or URL of the file to load.
        use_cache (bool): Whether to use the cache for loading the file.
            Defaults to True.

    Returns:
        str: The converted Markdown content.

    Raises:
        OSError: If there is an I/O error while loading the file.
        ValueError: If the URL is not valid or the conversion fails.
    """

    settings = get_settings()
    converter_options = get_converter_opts(file_path_or_url, settings)
    logger = get_logger(__name__)
    # if a cache file exists, load it
    if use_cache:
        try:
            return _load_cache_file(file_path_or_url, settings)
        except OSError:
            pass

    try:
        fs = get_filesystem(file_path_or_url, settings)
        with fs.open(file_path_or_url, "rb") as f:
            buffer = io.BytesIO(f.read())
    except Exception as e:
        logger.error(f"Failed to load file from {file_path_or_url}: {e}")
        raise OSError(f"Failed to load file from {file_path_or_url}: {e}") from None

    client = markitdown.MarkItDown(**converter_options)
    document = client.convert(buffer)

    # save a copy of the file to the cache for future use
    if use_cache:
        write_cache_file(file_path_or_url, document.markdown, settings)
    logger.info(f"File converted to markdown: {file_path_or_url}")
    return document.markdown


@retry(
    stop=stop_after_attempt(3),
    wait=wait_random_exponential(multiplier=1, max=15),
    retry=retry_if_exception_type(OSError),
    reraise=True,
)
def save_context(data: str, file_path: str) -> str:
    """
    Save the contents to a file and return the file path.

    Args:
        data (str): Base 64 encoded string data to save.
        file_name (str): The name of the file to save.

    Returns:
        str: The path to the saved file.
    """
    settings = get_settings()
    logger = get_logger(__name__)
    contents = base64.b64decode(data.split(",")[1])
    file_url = f"{settings.data_path}/{file_path.lstrip('/')}"
    fs = get_filesystem(file_url, settings)
    with fs.open(file_url, "wb") as f:
        f.write(contents)
    logger.info(f"File saved: {file_url}")
    return file_url

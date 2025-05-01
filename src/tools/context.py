import datetime
import hashlib
import io

import fsspec
import markitdown
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from common import (
    get_app_config,
    get_converter_opts,
    get_storage_opts,
)
from models import AppConfig


def get_filesystem(url: str, app_config: AppConfig) -> fsspec.AbstractFileSystem:
    """
    Get the filesystem object based on the URL protocol.

    Args:
        url (str): The URL to determine the filesystem for.
        app_config (AppConfig): The application configuration.

    Returns:
        fsspec.AbstractFileSystem: The filesystem object.
    """
    protocol, _ = url.split("://")
    storage_options = get_storage_opts(url, app_config)
    print(storage_options)
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
    if ctime := file_info.get("ctime"):
        created_at = datetime.datetime.fromtimestamp(ctime)
    else:
        created_at = file_info.get("creation_time")

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


def write_cache_file(url: str, contents: str, app_config: AppConfig) -> None:
    """
    Write the contents to a cache file.

    Args:
        url (str): The URL of the file.
        contents (str): The contents to write to the cache file.
        app_config (dict): The application configuration.

    Returns:
        None
    """
    hash_key = get_cache_key(url)
    _, cache_path = app_config.cache_path.split("://")
    fs = get_filesystem(app_config.cache_path, app_config)
    fs.mkdir(cache_path, create_parents=True, exist_ok=True)
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
    hash_key = get_cache_key(url)
    _, cache_path = app_config.cache_path.split("://")
    fs = get_filesystem(app_config.cache_path, app_config)
    cache_file = f"{cache_path}/{hash_key}.md"
    if not fs.exists(cache_file):
        raise OSError(f"Cache file {cache_file} does not exist")

    with fs.open(cache_file, "r") as f:
        return f.read()


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5),
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

    app_config = get_app_config()
    converter_options = get_converter_opts(file_path_or_url, app_config)

    # if a cache file exists, load it
    if use_cache:
        try:
            return _load_cache_file(file_path_or_url, app_config)
        except OSError:
            pass

    try:
        fs = get_filesystem(file_path_or_url, app_config)
        with fs.open(file_path_or_url, "rb") as f:
            buffer = io.BytesIO(f.read())
    except Exception as e:
        raise OSError(f"Failed to load file from {file_path_or_url}: {e}") from None

    client = markitdown.MarkItDown(**converter_options)
    document = client.convert(buffer)

    # save a copy of the file to the cache for future use
    if use_cache:
        write_cache_file(file_path_or_url, document.markdown, app_config)
    return document.markdown

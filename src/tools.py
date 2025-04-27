import hashlib
import io
import json

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
    get_filesystem,
    get_redis_client,
    validate_key,
)
from models import AppConfig


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
    hash_key = _get_cache_key(url)
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
def fetch_context(key: str, use_cache: bool = True) -> str:
    """
    Load a file from a URL location and convert the contents to markdown.

    Args:
        key (str): The context key to load.
        use_cache (bool): Whether to use the cache for loading the file.
            Defaults to True.

    Returns:
        str: The converted Markdown content.

    Raises:
        OSError: If there is an I/O error while loading the file.
        ValueError: If the URL is not valid or the conversion fails.
    """
    
    if not key.startswith("context|"):
        raise ValueError("Key must start with 'context|'")
    
    _, _, url, _ = validate_key(key)

    # For URLs starting with http(s), we don't use the cache
    # because may be updated frequently.
    # Since cache is cleared every 1 hour this is not a problem
    #if url.startswith(("http://", "https://")):
    #    use_cache = False

    app_config = get_app_config()
    converter_options = get_converter_opts(url, app_config)

    # if a cache file exists, load it
    if use_cache:
        try:
            return _load_cache_file(url, app_config)
        except OSError:
            pass

    try:
        fs = get_filesystem(url, app_config)
        with fs.open(url, "rb") as f:
            buffer = io.BytesIO(f.read())
    except Exception as e:
        raise OSError(f"Failed to load file from {url}: {e}") from None

    client = markitdown.MarkItDown(**converter_options)
    document = client.convert(buffer)

    # save a copy of the file to the cache for future use
    if use_cache:
        _write_cache_file(url, document.markdown, app_config)
    return document.markdown


def fetch_memory(key: str) -> str | None:
    """
    Fetch a JSON-serializable value from shared Redis.

    Args:
        key (str): The key to fetch from Redis.

    Returns:
        str | None: The value associated with the key, or None if not found.

    """
    _key = key.lower()
    validate_key(_key)
    client = get_redis_client(get_app_config())
    if "blackboard" in _key:
        return json.dumps(client.hgetall(_key))

    return client.get(_key)


def update_memory(key: str, description: str, value: str) -> str:
    """
    Write a JSON-serializable value to shared Redis.

    Args:
        key (str): The key to write to Redis.
        description (str): A description of the value being written.
        value (str): The value to write to Redis.

    Returns:
        str: A confirmation message.
    """

    _key = key.lower()
    _, plan_id, _, _ = validate_key(_key)
    client = get_redis_client(get_app_config())

    _base_key = f"blackboard|{plan_id}"
    client.hset(_base_key, _key, description)
    client.expire(_base_key, 3600)
    client.set(_key, value, ex=3600)
    return "ok"

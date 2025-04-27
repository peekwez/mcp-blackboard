import datetime
import os
from pathlib import Path
from typing import Any

import fsspec
import yaml

from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
from openai import OpenAI
from models import AppConfig, ConverterParams

TEMPLATES_DIR = Path(__file__).parent / "config"
app_config: None | AppConfig = None


def load_config(env_file: str) -> AppConfig:
    """
    Load the configuration from a YAML file and return it as a dictionary.


    Args:
        env_file (str): The path to the .env file.

    Returns:
        AppConfig: The application configuration object.
    """

    load_dotenv(env_file, override=True)

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template("template.yml.j2")

    rendered_yaml: str = template.render(env=os.environ)

    config_dict: dict[str, Any] = yaml.safe_load(rendered_yaml)

    return AppConfig.model_validate(config_dict)


def get_app_config() -> AppConfig:
    """
    Get the application configuration.

    Returns:
        AppConfig: The application configuration object.
    """
    global app_config
    if app_config is None:
        app_config = load_config(".env")

    return app_config


def get_converter_opts(url: str, app_config: AppConfig) -> dict[str, Any]:
    """
    Set options for the MarkItDown converter based on the URL.

    Args:
        url (str): The URL to determine the options for.
        app_config (AppConfig): The application configuration.

    Returns:
        dict: The options for the converter.
    """

    params = ConverterParams(enable_plugins=True)
    if url.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff")):
        params = ConverterParams(
            llm_client=OpenAI(
                api_key=app_config.converter.openai_api_key,
                base_url=app_config.converter.openai_api_base,
            ),
            llm_model="gpt-4o",
        )
    elif url.lower().endswith((".pdf", ".x-pdf")):
        params = ConverterParams(
            docintel_endpoint=app_config.converter.azure_document_endpoint,
        )

    return params.model_dump()


def get_storage_opts(url: str, app_config: AppConfig) -> dict:
    """
    Get the storage options based on the URL protocol.

    Args:
        url (str): The URL to determine the options for.
        app_config (AppConfig): The application configuration.

    Returns:
        dict: The options for the protocol.
    """
    protocol = url.split("://")[0]
    if protocol == "s3":
        return app_config.storage.s3
    elif protocol == "abfs":
        return app_config.storage.abfs
    elif protocol == "gcs":
        return app_config.storage.gcs
    elif protocol == "sftp":
        return app_config.storage.sftp
    elif protocol == "smb":
        return app_config.storage.smb
    elif protocol in ["file", "https"]:
        # No options needed for local file system or HTTP(S)
        return {}
    else:
        message = (
            f"Unsupported protocol: {protocol}, Supported: "
            f"file, s3, abfs, gcs, sftp, smb, http"
        )
        raise ValueError(message)


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
    fs = fsspec.filesystem(protocol, **storage_options)
    return fs


def get_file_age(file_info: dict[str,str|int|float]) -> int:
    """
    Get the age of a file.

    Args:
        file_info (dict): The file information dictionary.

    Returns:
        datetime.timedelta: The age of the file.
    """
    created_at = datetime.datetime.fromtimestamp(file_info["ctime"])
    current_time = datetime.datetime.now()
    delta = current_time - created_at
    return int(delta.total_seconds())


def remove_stale_files(max_age: int = 3600) -> None:
    """
    Remove all files in the cache directory that are older than 1 hour.

    Args:
        max_age (int): The maximum age of files to keep in seconds.
            Default is 3600 seconds (1 hour).

    Returns:
        None
    """

    app_config = get_app_config()
    _, cache_path = app_config.cache_path.split("://")
    fs = get_filesystem(app_config.cache_path, app_config)

    # remove all files older than 1 day
    for file_info in fs.listdir(cache_path):
        file_age = get_file_age(file_info)
        if file_age > max_age:
            fs.rm(f"{file_info['name']}")


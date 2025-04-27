import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
from openai import OpenAI

from models import AppConfig, ConverterParams

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

    TEMPLATES_DIR = Path(__file__).parent / "config"
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


def get_protocol_opts(url: str, app_config: AppConfig) -> dict:
    """
    Set options for the protocol based on the URL.

    Args:
        url (str): The URL to determine the options for.
        app_config (AppConfig): The application configuration.

    Returns:
        dict: The options for the protocol.
    """
    protocol = url.split("://")[0]
    if protocol == "s3":
        return app_config.storage.s3
    elif protocol in "abfs":
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

import os
import uuid
from pathlib import Path
from typing import Any

import yaml
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
from openai import OpenAI
from redis import Redis

from models import AppConfig, ConverterParams

TEMPLATES_DIR = Path(__file__).parent

app_config: None | AppConfig = None
redis_client: None | Redis = None


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
    template = env.get_template("config.yml.j2")

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
            llm_model=app_config.converter.openai_default_model,
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



def validate_key(key: str) -> tuple[str, str, str | None, str | None]:
    """
    Validate the format of a key.

    Args:
        key (str): The key to validate.

    Returns:
        tuple[str, str, str | None, str | None]: A tuple containing the key type,
            plan ID, file path or URL or agent name, and step ID.

    Raises:
        ValueError: If the key is not in the correct format.
    """

    parts = key.split("|")
    if parts[0] not in ("context", "plan", "blackboard", "result"):
        raise ValueError(
            "Key must start with 'result', 'context', 'plan', or 'blackboard'"
        )

    if parts[0] in ("plan", "blackboard") and len(parts) != 2:
        raise ValueError(
            "Plan or blackboard must be in the format 'plan|<plan_id>' "
            "or 'blackboard|<plan_id>'"
        )

    if parts[0] == "context" and len(parts) != 3:
        raise ValueError(
            "Context key must be in the format 'context|<plan_id>|<file_path_or_url>'"
        )

    if parts[0] == "result" and len(parts) != 4:
        raise ValueError(
            "Result key must be in the format 'result|<plan_id>|<aget_name>|<step id>'"
        )

    try:
        uuid.UUID(parts[1])
    except ValueError:
        message = (
            "Plan ID must be a valid UUID. Key must be in the format "
            "'context|<plan_id>|<file_path_or_url>'"
            " or 'plan|<plan_id>' or 'blackboard|<plan_id>'"
            " or 'result|<plan_id>|<agent_name>|<step id>'"
        )
        raise ValueError(message) from None

    return (
        parts[0],
        parts[1],
        parts[2] if len(parts) > 2 else None,
        parts[3] if len(parts) > 3 else None,
    )

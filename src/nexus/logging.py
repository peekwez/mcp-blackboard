from __future__ import annotations

from pathlib import Path

import loguru
from loguru import logger

from nexus.common import get_settings

loggers: dict[str, loguru.Logger] = {}
_configured_sinks: set[str] = set()


def get_logger(name: str, file_prefix: str = "app") -> loguru.Logger:
    """
    Get a logger instance with the specified settings.

    Args:
        settings (Settings): The settings for the logger.
        name (str): The name of the logger.

    Returns:
        logger: A logger instance configured with the provided settings.
    """
    global loggers
    if name in loggers:
        return loggers[name]

    settings = get_settings()
    file_name = f"{settings.logging.root_dir}/{file_prefix}.log"

    if file_name not in _configured_sinks:
        if not _configured_sinks:
            # Remove loguru's default stderr sink once, before the first
            # file sink is configured, instead of on every call.
            logger.remove()
        Path(settings.logging.root_dir).mkdir(parents=True, exist_ok=True)
        Path(file_name).touch(exist_ok=True)
        logger.add(
            file_name,
            mode="a",
            rotation=settings.logging.rotation,
            retention=settings.logging.retention,
            compression=settings.logging.compression,
        )
        _configured_sinks.add(file_name)

    bound_logger = logger.bind(name=name)
    loggers[name] = bound_logger
    return bound_logger

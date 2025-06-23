from __future__ import annotations

import loguru
from loguru import logger

from nexus.common import get_settings


def get_logger(name: str) -> loguru.Logger:
    """
    Get a logger instance with the specified settings.

    Args:
        settings (Settings): The settings for the logger.
        name (str): The name of the logger.

    Returns:
        logger: A logger instance configured with the provided settings.
    """
    settings = get_settings()
    logger.add(settings.logging.filename, rotation=settings.logging.rotation)
    logger.add(settings.logging.filename, retention=settings.logging.retention)
    logger.add(settings.logging.filename, compression=settings.logging.compression)
    return logger.bind(name=name)

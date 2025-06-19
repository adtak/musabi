import os
import sys
from loguru import logger


def configure_logger() -> None:
    """Configure loguru logger with unified settings for all Lambda functions."""
    # Remove default handler
    logger.remove()
    
    # Configure log level from environment variable, default to INFO
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Add structured logging handler
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        serialize=False,
        colorize=True,
    )


def get_logger(name: str):
    """Get a configured logger instance for the given module name."""
    configure_logger()
    return logger.bind(name=name)
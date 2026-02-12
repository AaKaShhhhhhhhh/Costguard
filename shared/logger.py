"""Centralized logging setup using Loguru.

This module configures the `loguru` logger with a human-friendly
console format and an optional file sink for production.
"""
import sys
from loguru import logger

from shared.config import settings

# Remove default handler to avoid duplicate logs
logger.remove()

# Add console handler with structured formatting
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.log_level,
    colorize=True,
)

if settings.environment == "production":
    # File sink for production with rotation and retention
    logger.add(
        "logs/costguard_{time}.log",
        rotation="500 MB",
        retention="10 days",
        compression="zip",
        level="INFO",
    )

__all__ = ["logger"]

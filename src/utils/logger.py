"""
Structured logging configuration for the BacklinkContent Engine.

Provides rich, structured logging with context for debugging and observability.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import structlog
from rich.console import Console
from rich.logging import RichHandler


def configure_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    json_output: bool = False
) -> None:
    """
    Configure structured logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        json_output: If True, output JSON-formatted logs (useful for production)
    """
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, level.upper()),
        handlers=[RichHandler(rich_tracebacks=True, console=Console(stderr=True))]
    )

    # Configure structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if json_output:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.extend([
            structlog.dev.ConsoleRenderer(colors=True)
        ])

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)

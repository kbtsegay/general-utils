"""
Logging configuration for gutils.

Provides consistent logging across all tools with support for:
- Machine-readable output (JSON/raw text to stdout, logs to stderr)
- Human-readable output with colors and emojis
- Configurable log levels
"""

import sys
import logging
import json
from typing import Any, Dict, Optional


class MachineReadableFormatter(logging.Formatter):
    """Formatter that outputs structured JSON for machine consumption."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class HumanReadableFormatter(logging.Formatter):
    """Formatter with colors and clear formatting for human consumption."""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(
    level: str = "INFO",
    machine_readable: bool = False,
    logger_name: Optional[str] = None
) -> logging.Logger:
    """
    Set up logging configuration for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        machine_readable: If True, output JSON to stderr; if False, use human-readable format
        logger_name: Name for the logger (defaults to root logger)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    logger.handlers = []

    # Create handler (always to stderr so stdout is clean for data output)
    handler = logging.StreamHandler(sys.stderr)

    # Set formatter based on mode
    if machine_readable:
        formatter = MachineReadableFormatter()
    else:
        formatter = HumanReadableFormatter(
            fmt="%(levelname)s: %(message)s"
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

"""Vigil Home — Structured JSON Logging

Configures structured JSON logging for production environments.
All logs are emitted as JSON objects for easy parsing by log aggregators.

Usage:
    from app.logging_config import setup_logging
    setup_logging()

Per SECURITY-HARDENING-PLAN.md Phase 3.
"""

import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """Format log records as JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        """Convert a log record to a JSON string."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        for key, value in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "pathname", "process", "processName", "relativeCreated",
                "stack_info", "exc_info", "thread", "threadName", "message"
            }:
                try:
                    json.dumps(value)  # Test if JSON-serializable
                    log_data[key] = value
                except (TypeError, ValueError):
                    log_data[key] = str(value)

        return json.dumps(log_data)


def setup_logging(
    level: str = "INFO",
    log_file: str = None,
    console: bool = True,
) -> None:
    """Configure structured JSON logging for Vigil Home.

    Args:
        level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path to write logs to
        console: Whether to log to stdout (default True)
    """
    # Root logger for vigil.* modules
    root_logger = logging.getLogger("vigil")
    root_logger.setLevel(getattr(logging, level.upper()))

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Create formatter
    formatter = JSONFormatter()

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(getattr(logging, level.upper()))
        root_logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            file_handler.setLevel(getattr(logging, level.upper()))
            root_logger.addHandler(file_handler)
        except OSError as e:
            # Fallback to basic logging if file can't be opened
            logging.basicConfig(
                level=getattr(logging, level.upper()),
                format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            )
            logging.getLogger("vigil").warning(
                f"Could not open log file {log_file}: {e}. Using console logging."
            )

    # Prevent log propagation to root Python logger
    root_logger.propagate = False

    # Configure uvicorn/loggers if running as ASGI
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.handlers.clear()
    uvicorn_handler = logging.StreamHandler(sys.stdout)
    uvicorn_handler.setFormatter(JSONFormatter())
    uvicorn_logger.addHandler(uvicorn_handler)
    uvicorn_logger.setLevel(logging.INFO)

    logging.info(f"Structured JSON logging configured (level={level})")

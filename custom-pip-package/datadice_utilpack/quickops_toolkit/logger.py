"""Logger setup for local and GCP environments.

This module provides a method to create a logging instance with a specified name and log level.
Depending on the environment, it adjusts the logging format to be compatible with GCP structured
logging or a regular console output.

Example:
    import logging
    from gaming_academy.quickops_toolkit.logger import get_logger

    logger = get_logger(__name__, level=logging.INFO)
    logger.info('This is an info message')

"""

import json
import logging
import os
from logging import Logger


class GCPJsonFormatter(logging.Formatter):
    """Custom formatter for GCP structured logging.

    This formatter produces logs in JSON format suitable for GCP's structured logging system.

    Attributes:
        SEVERITY_MAP (dict): A mapping from logging levels to their GCP severity string.
    """

    SEVERITY_MAP = {
        logging.DEBUG: "DEBUG",
        logging.INFO: "INFO",
        logging.WARNING: "WARNING",
        logging.ERROR: "ERROR",
        logging.CRITICAL: "CRITICAL",
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record for GCP structured logging.

        Args:
            record (logging.LogRecord): The log record to be formatted.

        Returns:
            str: A JSON-formatted string representing the log record.
        """
        gcp_log = {
            "message": super().format(record),
            "severity": self.SEVERITY_MAP.get(record.levelno, "DEFAULT"),
            "logging.googleapis.com/sourceLocation": {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName,
            },
        }
        return json.dumps(gcp_log)


def get_logger(name: str, level: int = logging.DEBUG) -> Logger:
    """Create and return a logger with the specified name and log level.

    Depending on the environment variable `ENVIRONMENT`, it configures the logger
    for either GCP structured logging or regular console logging. If `ENVIRONMENT`
    is not set or set to "GCP", it defaults to GCP logging.

    Args:
        name (str): The name to set for the logger.
        level (int): The log level to set for the logger. Defaults to logging.DEBUG.

    Returns:
        Logger: The newly created logger instance.
    """
    # Assume we're running in GCP environment by default
    if not hasattr(get_logger, "_library_loggers_configured"):
        _configure_library_loggers(level)
        get_logger._library_loggers_configured = True

    is_gcp = os.environ.get("ENVIRONMENT", "GCP") == "GCP"
    formatter = (
        GCPJsonFormatter()
        if is_gcp
        else logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(console_handler)

    return logger


def _configure_library_loggers(level: int = logging.INFO):
    """
    Configure loggers for common libraries used in web/API development.

    Args:
        level (int): The logging level to set for the libraries (default is logging.INFO).
    """
    libraries = [
        "requests",
        "gunicorn",
        "uwsgi",
        "celery",
        "urllib3",
        "starlette",
        "uvicorn",
    ]
    for lib in libraries:
        lib_logger = logging.getLogger(lib)
        lib_logger.setLevel(level)
        console_handler = logging.StreamHandler()
        formatter = (
            GCPJsonFormatter()
            if os.environ.get("ENVIRONMENT", "GCP") == "GCP"
            else logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
        console_handler.setFormatter(formatter)
        lib_logger.addHandler(console_handler)

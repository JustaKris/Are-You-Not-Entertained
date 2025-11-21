"""
Centralized logging configuration for both local development and
production deployments (Docker, Azure, AWS, Kubernetes).

Features:
- JSON logging for structured cloud logs
- Colorized human-readable logs for local development
- Unified formatting for app + uvicorn logs
- Suppression of noisy 3rd-party libraries
- Support for extra contextual fields (e.g., request_id)
"""

import json
import logging
import sys
from typing import Any, Dict


# ===============================================================
# JSON FORMATTER
# ===============================================================

class JsonFormatter(logging.Formatter):
    """
    Formatter that outputs logs as structured JSON.

    This is recommended for production because:
    - JSON logs can be parsed by Azure Monitor, CloudWatch, Datadog, Loki, etc.
    - They allow better querying, filtering, and alerting
    - They enforce consistency in log structure
    """

    def format(self, record: logging.LogRecord) -> str:
        """Convert log record into a JSON object."""
        log_record: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "process": record.process,
            "thread": record.thread,
        }

        # If the log includes exception info, serialize it as plain text
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        # Allow user-defined fields — e.g., request_id, correlation_id, user_id
        extra_fields = getattr(record, "extra_fields", None)
        if extra_fields:
            log_record.update(extra_fields)

        return json.dumps(log_record)


# ===============================================================
# COLORIZED FORMATTER
# ===============================================================

class ColoredFormatter(logging.Formatter):
    """
    Formatter that adds ANSI colors to log levels for readability.

    This is ideal for local development:
    - Easier to visually parse logs
    - No need for JSON noise
    """

    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Inject color codes into the level name without mutating the original record."""
        original = record.levelname
        color = self.COLORS.get(original, "")
        record.levelname = f"{color}{original}{self.RESET}"

        formatted = super().format(record)

        # Restore original level name to avoid cross-handler contamination
        record.levelname = original
        return formatted


# ===============================================================
# FILTERS
# ===============================================================

class ChromaDBTelemetryFilter(logging.Filter):
    """
    Suppresses extremely noisy messages from ChromaDB's telemetry subsystem.

    These messages are not useful and pollute logs.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        return "Failed to send telemetry event" not in record.getMessage()


# ===============================================================
# CORE CONFIGURATION FUNCTION
# ===============================================================

def configure_logging(
    level: str = "INFO",
    use_json: bool = False,
    include_uvicorn: bool = True,
) -> None:
    """
    Configure application-wide logging.

    Args:
        level: Default logging level (INFO, DEBUG, WARNING, ...)
        use_json: Enables JSON logs (recommended for production)
        include_uvicorn: Also applies formatting to uvicorn logs

    This function replaces any previous logging configuration and ensures
    the entire application uses a consistent log format.
    """
    level = level.upper()

    # Choose the correct formatter depending on environment
    if use_json:
        formatter = JsonFormatter(datefmt="%Y-%m-%d %H:%M:%S")
    else:
        fmt = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
        datefmt = "%Y-%m-%d %H:%M:%S"
        formatter = ColoredFormatter(fmt=fmt, datefmt=datefmt)

    # Configure root logger (the parent of all loggers)
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root.addHandler(handler)

    # Suppress known noisy loggers
    logging.getLogger("chromadb").setLevel(logging.ERROR)
    logging.getLogger("chromadb").addFilter(ChromaDBTelemetryFilter())

    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # Apply formatting to uvicorn loggers as well
    if include_uvicorn:
        for name in ("uvicorn.error", "uvicorn.access"):
            uv = logging.getLogger(name)
            uv.handlers.clear()
            uv.addHandler(handler)
            uv.propagate = False  # Prevent duplicate logs
            uv.setLevel(logging.INFO)

    # Confirm setup
    logging.getLogger(__name__).info(
        f"Logging configured: level={level}, format={'JSON' if use_json else 'colored'}"
    )


# ===============================================================
# LOGGER RETRIEVAL
# ===============================================================

def get_logger(name: str) -> logging.Logger:
    """
    Retrieve a logger by name.

    Preferred over calling logging.getLogger() directly because:
    - It enforces consistent usage across the project
    - Makes future enhancements (like adding context managers) easier
    """
    return logging.getLogger(name)

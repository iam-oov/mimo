"""
Structured logging module for Mimo.
Provides JSON logging for production and readable logs for development.
"""

import json
import logging
from datetime import datetime
from typing import Any

from src.infrastructure.config.settings import get_settings


class StructuredLogger:
    """
    Structured logger that formats logs as JSON in production
    and human-readable format in development.
    """

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.settings = get_settings()
        self._setup_logger()

    def _setup_logger(self):
        """Configure logger based on environment"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()

            # Set level based on environment
            level = logging.INFO if self.settings.is_production else logging.DEBUG
            self.logger.setLevel(level)
            handler.setLevel(level)

            # No formatter - we'll format manually
            self.logger.addHandler(handler)
            self.logger.propagate = False

    def _format_log(self, level: str, message: str, **context: Any) -> str:
        """Format log entry based on environment"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "logger": self.logger.name,
            "message": message,
            **context,
        }

        if self.settings.is_production:
            # JSON format for production (parseable by log aggregators)
            return json.dumps(log_entry)
        else:
            # Human-readable format for development
            context_str = ""
            if context:
                context_str = " | " + " | ".join(f"{k}={v}" for k, v in context.items())
            return f"[{level}] {message}{context_str}"

    def debug(self, message: str, **context: Any):
        """Log debug message"""
        if self.logger.isEnabledFor(logging.DEBUG):
            formatted = self._format_log("DEBUG", message, **context)
            self.logger.debug(formatted)

    def info(self, message: str, **context: Any):
        """Log info message"""
        formatted = self._format_log("INFO", message, **context)
        self.logger.info(formatted)

    def warning(self, message: str, **context: Any):
        """Log warning message"""
        formatted = self._format_log("WARNING", message, **context)
        self.logger.warning(formatted)

    def error(self, message: str, **context: Any):
        """Log error message"""
        formatted = self._format_log("ERROR", message, **context)
        self.logger.error(formatted)

    def exception(self, message: str, **context: Any):
        """Log exception with traceback"""
        formatted = self._format_log("ERROR", message, **context)
        self.logger.exception(formatted)


def get_logger(name: str) -> StructuredLogger:
    """
    Get or create a structured logger instance.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        StructuredLogger instance

    Example:
        from src.infrastructure.logging.structured_logger import get_logger

        logger = get_logger(__name__)
        logger.info("Processing request", user_id="123", request_id="abc")
    """
    return StructuredLogger(name)

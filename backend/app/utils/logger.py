"""Structured JSON logger configuration."""

import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional
import os

from app.config.settings import get_settings


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        # Base log entry
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
            }
        
        # Add extra fields
        if hasattr(record, "correlation_id"):
            log_entry["correlation_id"] = record.correlation_id
        
        # Add any extra attributes
        if hasattr(record, "extra"):
            for key, value in record.extra.items():
                log_entry[key] = value
        
        return json.dumps(log_entry, ensure_ascii=False)


class CorrelationIDFilter(logging.Filter):
    """Filter to add correlation ID to log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to record."""
        from app.utils.correlation import get_correlation_id
        record.correlation_id = get_correlation_id()
        return True


def setup_logging(settings):
    """Configure structured JSON logging."""
    # Get log level from settings
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add correlation ID filter to root logger
    root_logger.addFilter(CorrelationIDFilter())
    
    # Console handler (JSON format)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(console_handler)
    
    # File handler for local development
    if settings.app_env == "local":
        try:
            os.makedirs("logs", exist_ok=True)
            file_handler = logging.FileHandler("logs/app.log")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(JSONFormatter())
            root_logger.addHandler(file_handler)
        except Exception:
            pass  # Skip file logging if logs directory can't be created
    
    # Set third-party log levels
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with correlation ID support."""
    logger = logging.getLogger(name)
    
    # Ensure correlation ID filter is attached
    has_filter = any(isinstance(f, CorrelationIDFilter) for f in logger.filters)
    if not has_filter:
        logger.addFilter(CorrelationIDFilter())
    
    return logger


class LoggerAdapter(logging.LoggerAdapter):
    """Logger adapter for adding extra context."""
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Process the message and kwargs to add extra context."""
        extra = kwargs.pop("extra", {})
        if "correlation_id" not in extra:
            from app.utils.correlation import get_correlation_id
            extra["correlation_id"] = get_correlation_id()
        
        kwargs["extra"] = extra
        return msg, kwargs
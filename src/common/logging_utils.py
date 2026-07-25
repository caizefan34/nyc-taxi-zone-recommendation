"""Logging utilities with standardized formatting."""
from __future__ import annotations
import logging
import sys
from typing import Optional

_LOGGING_INITIALIZED = False


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    format_string: Optional[str] = None,
) -> None:
    """Initialize logging with standardized format.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR).
        log_file: Optional path to log file. If None, logs to stderr only.
        format_string: Custom format string. If None, uses default.
    
    Examples:
        >>> setup_logging(level=logging.INFO)
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing started")
        2026-07-25 10:00:00 INFO Processing started
    """
    global _LOGGING_INITIALIZED
    
    if _LOGGING_INITIALIZED:
        return
    
    if format_string is None:
        format_string = "%(asctime)s %(levelname)s %(message)s"
    
    date_format = "%Y-%m-%d %H:%M:%S"
    
    handlers: list[logging.Handler] = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(format_string, date_format))
    handlers.append(console_handler)
    
    # File handler (optional)
    if log_file is not None:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(format_string, date_format))
        handlers.append(file_handler)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    for handler in handlers:
        root_logger.addHandler(handler)
    
    _LOGGING_INITIALIZED = True


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.
    
    Args:
        name: Logger name (typically __name__).
    
    Returns:
        Configured logger instance.
    
    Examples:
        >>> logger = get_logger(__name__)
        >>> logger.info("Operation completed")
    """
    if not _LOGGING_INITIALIZED:
        setup_logging()
    
    return logging.getLogger(name)

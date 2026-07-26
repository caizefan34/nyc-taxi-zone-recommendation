"""Tests for the logging utility module."""

from __future__ import annotations

import io
import logging

from src.common.logging_utils import get_logger, setup_logging


class TestLoggingUtils:
    """Test suite for logging utilities."""

    def test_get_logger_returns_logger(self):
        """get_logger should return a Logger instance."""
        logger = get_logger("test_logger")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"

    def test_get_logger_none_name(self):
        """get_logger with None should work (root logger)."""
        logger = get_logger(None)
        assert isinstance(logger, logging.Logger)

    def test_setup_logging_creates_handler(self):
        """setup_logging should configure root logger."""
        root = logging.getLogger()
        old_handlers = list(root.handlers)
        root.handlers.clear()
        try:
            result = setup_logging(level="WARNING")
            assert result is True or result is None
        finally:
            root.handlers.clear()
            for h in old_handlers:
                root.addHandler(h)

    def test_logger_levels(self):
        """Logger should respect level settings."""
        logger = get_logger("test_levels")
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        logger.info("info message")
        logger.debug("debug message")
        output = stream.getvalue()

        assert "info message" in output
        assert "debug message" not in output

        logger.removeHandler(handler)

    def test_multiple_loggers_different_names(self):
        """Multiple loggers with different names should be independent."""
        logger_a = get_logger("logger_a")
        logger_b = get_logger("logger_b")
        assert logger_a.name == "logger_a"
        assert logger_b.name == "logger_b"
        assert logger_a is not logger_b

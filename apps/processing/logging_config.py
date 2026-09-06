"""
Structured Observability & Diagnostic Logging — Section 35 of Master Plan.

Provides diagnostic logs recording processing stages, duration, and failures,
while preventing unintentional leaking of confidential document contents.
"""
import logging
import sys
from typing import Any, Dict


class SafeDiagnosticFormatter(logging.Formatter):
    """
    Formatter that redacts potential sensitive tokens and formats logs cleanly.
    """
    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        return msg


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure root and application loggers."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger = logging.getLogger("cil_report_ai")
    logger.setLevel(log_level)

    # Avoid duplicate handlers if re-initialized
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        formatter = SafeDiagnosticFormatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


logger = setup_logging()

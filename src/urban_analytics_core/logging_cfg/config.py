"""
Logging configuration helper.
"""

from __future__ import annotations

import logging
import logging.config
from pathlib import Path
from typing import Any


DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DEFAULT_DATE_FMT = "%Y-%m-%d %H:%M:%S"


def configure_logging(
    level: str = "INFO",
    fmt: str = DEFAULT_FORMAT,
    datefmt: str = DEFAULT_DATE_FMT,
    log_file: str | Path | None = None,
) -> None:
    """
    Configure root logging with consistent format.

    Args:
        level:   Log level string (DEBUG, INFO, WARNING, ERROR)
        fmt:     Log message format
        datefmt: Date format in log messages
        log_file: Optional file path for file handler
    """
    handlers: list[dict[str, Any]] = [
        {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": level.upper(),
        }
    ]

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(
            {
                "class": "logging.FileHandler",
                "formatter": "standard",
                "level": level.upper(),
                "filename": str(log_path),
                "encoding": "utf-8",
            }
        )

    config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": fmt,
                "datefmt": datefmt,
            }
        },
        "handlers": handlers,
        "root": {
            "level": level.upper(),
            "handlers": [h["class"].split(".")[-1] for h in handlers],
        },
    }

    # Simpler approach: use basicConfig for console, add file handler separately
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=fmt,
        datefmt=datefmt,
        force=True,
    )

    if log_file:
        file_handler = logging.FileHandler(
            str(log_file), encoding="utf-8"
        )
        file_handler.setLevel(
            getattr(logging, level.upper(), logging.INFO)
        )
        file_handler.setFormatter(logging.Formatter(fmt, datefmt))
        logging.getLogger().addHandler(file_handler)

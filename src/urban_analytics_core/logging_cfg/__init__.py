"""
Centralized logging configuration.

Provides a single `configure_logging()` that all urban analytics projects
can use for consistent log format, level, and output.
"""

from __future__ import annotations

from .config import configure_logging

__all__ = ["configure_logging"]

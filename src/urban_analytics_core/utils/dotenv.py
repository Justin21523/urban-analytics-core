"""
Lightweight .env file loader (no python-dotenv dependency required).

Reads KEY=VALUE lines from a file, skipping comments and blanks.
Does NOT override already-set environment variables.
"""

from __future__ import annotations

from pathlib import Path


def load_dotenv(path: str | Path = ".env") -> None:
    """
    Load a .env file into os.environ (setdefault — won't override).
    """
    import os

    path = Path(path)
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)

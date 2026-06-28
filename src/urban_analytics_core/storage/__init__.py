"""
Storage backends for urban analytics projects.

Provides:
- SQLiteBackend:   Simple SQLite store with WAL mode
- DuckDBBackend:   DuckDB + Parquet columnar store (optional)
"""

from __future__ import annotations

__all__ = [
    "SQLiteBackend",
    "DuckDBBackend",
]

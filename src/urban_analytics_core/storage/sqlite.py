"""
SQLite storage backend.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


@dataclass
class MetaRecord:
    key: str
    value: str
    updated_at: str


class SQLiteBackend:
    """
    Lightweight SQLite store with WAL mode.

    Used for:
    - Cached reference data (bus stops, metro stations)
    - ETA observations
    - Run metadata
    """

    def __init__(self, db_path: str | Path) -> None:
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._path))
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.executescript(
            """
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS meta (
                key       TEXT PRIMARY KEY,
                value     TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        self._conn.commit()

    def set_meta(self, key: str, value: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            "INSERT OR REPLACE INTO meta (key, value, updated_at) VALUES (?, ?, ?)",
            (key, value, now),
        )
        self._conn.commit()

    def get_meta(self, key: str) -> str | None:
        row = self._conn.execute(
            "SELECT value FROM meta WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else None

    def execute(
        self, sql: str, params: tuple | None = None
    ) -> sqlite3.Cursor:
        return self._conn.execute(sql, params or ())

    def executemany(
        self, sql: str, params: Iterable[tuple]
    ) -> None:
        self._conn.executemany(sql, params)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "SQLiteBackend":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

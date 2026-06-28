"""
DuckDB storage backend (optional, requires duckdb package).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


class DuckDBBackend:
    """
    DuckDB + Parquet columnar store.

    Used for:
    - Large observation tables (traffic VD, bike availability)
    - Time-series analytics
    - Parquet-based data warehouse
    """

    def __init__(self, db_path: str | Path, parquet_dir: str | Path | None = None) -> None:
        self._path = Path(db_path)
        self._parquet_dir = Path(parquet_dir) if parquet_dir else None
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if self._parquet_dir:
            self._parquet_dir.mkdir(parents=True, exist_ok=True)

        try:
            import duckdb

            self._conn = duckdb.connect(str(self._path))
            self._duckdb = duckdb
        except ImportError as exc:
            raise ImportError(
                "duckdb is required for DuckDBBackend. "
                "Install with: pip install duckdb"
            ) from exc

    def query(self, sql: str, params: dict | None = None) -> pd.DataFrame:
        result = self._conn.execute(sql, params or {}).fetchdf()
        return result

    def write_parquet(
        self, df: pd.DataFrame, table_name: str, partition_by: str | None = None
    ) -> Path:
        if not self._parquet_dir:
            raise ValueError("No parquet_dir configured")

        import uuid

        safe_name = table_name.replace("/", "_")
        filename = f"{safe_name}_{uuid.uuid4().hex[:8]}.parquet"
        path = self._parquet_dir / filename
        df.to_parquet(str(path), index=False)
        return path

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "DuckDBBackend":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

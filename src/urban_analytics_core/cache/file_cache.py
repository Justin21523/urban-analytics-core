"""
File-based JSON cache with TTL support.

Used by TDX clients, weather clients, and scoring modules to avoid
repeated external API calls.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Optional


class CacheKey:
    """Namespace + key → SHA-256 hash for safe filesystem storage."""

    def __init__(self, namespace: str, key: str) -> None:
        self.namespace = namespace
        self.key = key

    @property
    def hashed(self) -> str:
        return hashlib.sha256(
            f"{self.namespace}:{self.key}".encode("utf-8")
        ).hexdigest()


class FileCache:
    """
    Simple on-disk JSON cache.

    - Stores values as JSON files under a directory
    - Keys are SHA-256 hashed to avoid filesystem issues
    - TTL enforced on read
    - Safe to disable entirely (reads/writes become no-ops)
    """

    def __init__(
        self,
        directory: str | Path,
        ttl_seconds: int = 3600,
        enabled: bool = True,
    ) -> None:
        self.directory = Path(directory)
        self.ttl_seconds = ttl_seconds
        self.enabled = enabled
        if self.enabled:
            self.directory.mkdir(parents=True, exist_ok=True)

    def get(self, key: CacheKey) -> Any | None:
        if not self.enabled:
            return None
        path = self._file_path(key)
        if not path.exists():
            return None
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

        # Check TTL
        if self.ttl_seconds > 0:
            created = raw.get("_created", 0)
            if time.time() - created > self.ttl_seconds:
                try:
                    path.unlink()
                except OSError:
                    pass
                return None

        return raw.get("_value")

    def set(self, key: CacheKey, value: Any) -> None:
        if not self.enabled:
            return
        path = self._file_path(key)
        envelope = {
            "_created": time.time(),
            "_ttl": self.ttl_seconds,
            "_value": value,
        }
        path.write_text(
            json.dumps(envelope, ensure_ascii=False), encoding="utf-8"
        )

    def _file_path(self, key: CacheKey) -> Path:
        safe_ns = key.namespace.replace("/", "_")
        digest = key.hashed
        subdir = self.directory / safe_ns / digest[:2]
        subdir.mkdir(parents=True, exist_ok=True)
        return subdir / f"{digest}.json"

    def clear(self) -> None:
        """Remove all cached files."""
        import shutil

        if self.enabled and self.directory.exists():
            shutil.rmtree(self.directory)
            self.directory.mkdir(parents=True, exist_ok=True)

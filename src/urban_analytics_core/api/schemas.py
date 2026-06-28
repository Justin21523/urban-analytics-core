"""
Common Pydantic schemas shared across projects.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class BoundingBox(BaseModel):
    """Bounding box for spatial queries."""

    min_lat: float
    min_lon: float
    max_lat: float
    max_lon: float


class GeoFeature(BaseModel):
    """Minimal GeoJSON-like feature."""

    lat: float
    lon: float
    name: str = ""
    properties: dict[str, Any] = {}


class TimeRange(BaseModel):
    """Start/end time range."""

    start: datetime
    end: datetime


class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper."""

    items: list[Any] = []
    total: int = 0
    page: int = 1
    page_size: int = 100
    has_more: bool = False


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    detail: str = ""
    code: str | None = None

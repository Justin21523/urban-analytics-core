"""
Time parsing and timezone normalization helpers.
"""

from __future__ import annotations

from datetime import datetime, time, timezone, timedelta
from zoneinfo import ZoneInfo

# Default timezone for Taiwan projects
DEFAULT_TIMEZONE = "Asia/Taipei"


def ensure_tz(dt: datetime, tz: str = DEFAULT_TIMEZONE) -> datetime:
    """
    Ensure `dt` is timezone-aware. If naive, attach `tz`.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=ZoneInfo(tz))
    return dt


def to_utc(dt: datetime) -> datetime:
    """Convert a datetime to UTC."""
    dt = ensure_tz(dt)
    return dt.astimezone(timezone.utc)


def parse_iso_datetime(
    value: str, *, default_tz: str = DEFAULT_TIMEZONE
) -> datetime:
    """
    Parse an ISO datetime string.

    - If no timezone, interpret as `default_tz`.
    - Always return an aware datetime.
    """
    dt = datetime.fromisoformat(value)
    return ensure_tz(dt, default_tz)


def parse_hhmm(value: str) -> time:
    """Parse 'HH:MM' string into a time object."""
    parts = value.strip().split(":")
    return time(int(parts[0]), int(parts[1]))

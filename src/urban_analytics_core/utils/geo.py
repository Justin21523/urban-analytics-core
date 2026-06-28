"""
Geospatial helpers — lightweight, no GIS dependency required.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class GeoPoint:
    """A latitude/longitude pair in decimal degrees (WGS84)."""

    lat: float
    lon: float


def haversine_meters(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """
    Great-circle distance in meters between two WGS84 coordinates.
    """
    R = 6371000.0  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def distance_between(p1: GeoPoint, p2: GeoPoint) -> float:
    """Distance in meters between two GeoPoints."""
    return haversine_meters(p1.lat, p1.lon, p2.lat, p2.lon)

"""
urban_analytics_core — Shared infrastructure for Taiwan urban analytics projects.

This package extracts common functionality from:
- traffic-pulse (road congestion analytics)
- mrt-ubike-analysis (metro/YouBike mobility)
- tripscore (destination scoring & recommendation)
- commute-reliability-analysis (commute ETA reliability)
- library-reach-analysis (library accessibility)

Modules:
- tdx:         TDX API client (OAuth2 auth, rate limiting, HTTP client)
- settings:    Base configuration loader (YAML + env + Pydantic)
- logging_cfg: Centralized logging setup
- cache:       File-based JSON cache with TTL
- utils:       Shared helpers (geo, time, dotenv)
- api:         FastAPI app factory, middleware, schemas
- storage:     Storage backends (SQLite, DuckDB)
"""

__all__ = [
    "__version__",
]

__version__ = "0.1.0"

# urban-analytics-core

Shared infrastructure package for Taiwan urban analytics projects.

## Source Projects

Extracted from these 5 projects in `../`:

| Project | Domain |
|---------|--------|
| `traffic-pulse` | Road congestion analytics |
| `mrt-ubike-analysis` | Metro/YouBike mobility |
| `tripscore` | Destination scoring & recommendation |
| `commute-reliability-analysis` | Commute ETA reliability |
| `library-reach-analysis` | Library accessibility |

## Shared Modules

| Module | What it provides | Replaces |
|--------|-----------------|----------|
| `tdx` | TDX OAuth auth + HTTP client with rate limit/retry | 5 separate TDX clients |
| `settings` | Pydantic base settings + YAML loader + TdxSettings | 5 separate config systems |
| `logging_cfg` | Unified logging setup | 5 separate logging configs |
| `cache` | File-based JSON cache with TTL | 3 separate cache implementations |
| `utils` | Geo (haversine), time parsing, .env loader | 3 separate geo + 3 time utils |
| `api` | FastAPI factory + CORS + cache + rate limit middleware | 5 separate app factories |
| `storage` | SQLite + DuckDB backends | 2 separate storage layers |

## Quick Start

```bash
# Install in editable mode (development)
cd /home/justin/web-projects/urban-analytics-core
pip install -e ".[full]"

# Use in any project
# Add to requirements.txt or pyproject.toml:
#   -e ../urban-analytics-core
```

## Example Usage

```python
from urban_analytics_core.tdx import TdxClient
from urban_analytics_core.settings import BaseAppSettings, TdxSettings
from urban_analytics_core.logging_cfg import configure_logging
from urban_analytics_core.cache import FileCache, CacheKey
from urban_analytics_core.api import create_app
from urban_analytics_core.storage import SQLiteBackend
from urban_analytics_core.utils.geo import haversine_meters, GeoPoint
from urban_analytics_core.utils.time import parse_iso_datetime

# Shared TDX client
with TdxClient(client_id="...", client_secret="...") as tdx:
    data = tdx.get("Road/Traffic/Live/VD/City/Taipei", top=100)

# Shared settings
settings = BaseAppSettings(app_name="my-project")
settings.ensure_dirs()

# Shared logging
configure_logging(level="INFO")

# Shared cache
cache = FileCache("data/cache", ttl_seconds=3600)
cache.set(CacheKey("tdx", "taipei_vd"), data)
```

## License

Personal project — no formal license.

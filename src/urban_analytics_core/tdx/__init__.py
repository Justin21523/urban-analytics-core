"""
TDX (Transport Data eXchange) client module.

Provides:
- OAuth 2.0 client-credentials authentication with token caching
- Configurable HTTP client with rate limiting & retry
- Unified exceptions for auth vs request errors
"""

from __future__ import annotations

from .auth import TdxAuthError, TdxAuthClient
from .client import TdxClient, TdxRequestError

__all__ = [
    "TdxAuthError",
    "TdxAuthClient",
    "TdxClient",
    "TdxRequestError",
]

"""
TDX OAuth 2.0 client-credentials authentication.

Handles:
- Token exchange (client_id + client_secret → access token)
- In-memory token caching with automatic refresh
- Token expiry detection (with safety margin)
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Default TDX token endpoint
DEFAULT_TOKEN_URL = (
    "https://tdx.transportdata.tw/auth/realms/"
    "TDXConnect/protocol/openid-connect/token"
)


class TdxAuthError(RuntimeError):
    """Raised when TDX OAuth authentication fails."""


@dataclass(frozen=True)
class _AccessToken:
    token: str
    expires_at: float  # epoch seconds


class TdxAuthClient:
    """
    Manages TDX OAuth 2.0 client-credentials token lifecycle.

    Usage:
        auth = TdxAuthClient(client_id="...", client_secret="...")
        token = auth.get_token()
        auth.close()
    """

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        token_url: str = DEFAULT_TOKEN_URL,
        env_id: str = "TDX_CLIENT_ID",
        env_secret: str = "TDX_CLIENT_SECRET",
        safety_margin_seconds: float = 60.0,
        timeout: float = 30.0,
    ):
        # Resolve credentials from args or environment
        self._client_id = (client_id or os.getenv(env_id, "")).strip()
        self._client_secret = (
            client_secret or os.getenv(env_secret, "")
        ).strip()
        if not self._client_id or not self._client_secret:
            raise TdxAuthError(
                f"Missing TDX credentials. Set {env_id} and {env_secret} "
                "or pass client_id/client_secret."
            )

        self._token_url = token_url
        self._safety_margin = safety_margin_seconds
        self._token: _AccessToken | None = None
        self._http = httpx.Client(timeout=timeout)

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._http.close()

    def get_token(self) -> str:
        """
        Return a valid access token, refreshing if necessary.
        """
        if self._token and self._is_valid(self._token):
            return self._token.token
        self._token = self._fetch_token()
        return self._token.token

    def _is_valid(self, token: _AccessToken) -> bool:
        return time.time() < (token.expires_at - self._safety_margin)

    def _fetch_token(self) -> _AccessToken:
        try:
            resp = self._http.post(
                self._token_url,
                data={
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "grant_type": "client_credentials",
                },
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise TdxAuthError(f"TDX token request failed: {exc}") from exc

        body: dict[str, Any] = resp.json()
        access_token = body.get("access_token")
        expires_in: float = body.get("expires_in", 3600)

        if not access_token:
            raise TdxAuthError(
                "TDX token response missing 'access_token'. "
                f"Response keys: {list(body.keys())}"
            )

        expires_at = time.time() + expires_in
        logger.info(
            "TDX token obtained, expires in %.0fs (at %.0f)",
            expires_in,
            expires_at,
        )
        return _AccessToken(token=access_token, expires_at=expires_at)

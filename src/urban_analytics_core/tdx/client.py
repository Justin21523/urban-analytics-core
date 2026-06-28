"""
TDX HTTP client with rate limiting, retry, and request error handling.
"""

from __future__ import annotations

import logging
import random
import time
from typing import Any

import httpx

from .auth import TdxAuthClient, TdxAuthError

logger = logging.getLogger(__name__)

# Default TDX API base URLs
DEFAULT_BASE_URL_V2 = "https://tdx.transportdata.tw/api/basic/v2"
DEFAULT_BASE_URL_V1 = "https://tdx.transportdata.tw/api/basic/v1"
DEFAULT_HISTORICAL_URL = "https://tdx.transportdata.tw/api/historical"


class TdxRequestError(RuntimeError):
    """Raised when a TDX business API request fails (non-auth)."""


class TdxClient:
    """
    Unified TDX API client.

    Usage:
        client = TdxClient(client_id="...", client_secret="...")
        data = client.get("Road/Traffic/Live/VD/City/Taipei", top=1000)
        client.close()
    """

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        base_url: str = DEFAULT_BASE_URL_V2,
        token_url: str = "https://tdx.transportdata.tw/auth/realms/"
        "TDXConnect/protocol/openid-connect/token",
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_backoff: float = 1.0,
        backoff_multiplier: float = 2.0,
        max_backoff: float = 60.0,
        jitter: float = 0.25,
        respect_retry_after: bool = True,
        min_interval: float = 0.0,
    ):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries
        self._backoff = retry_backoff
        self._backoff_multiplier = backoff_multiplier
        self._max_backoff = max_backoff
        self._jitter = jitter
        self._respect_retry_after = respect_retry_after
        self._min_interval = min_interval
        self._last_request_time: float = 0.0

        self._auth = TdxAuthClient(
            client_id=client_id,
            client_secret=client_secret,
            token_url=token_url,
            timeout=timeout,
        )
        self._http = httpx.Client(timeout=timeout)

    def close(self) -> None:
        self._http.close()
        self._auth.close()

    # --- Context manager ---
    def __enter__(self) -> "TdxClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    # --- Core request ---
    def get(
        self,
        path: str,
        *,
        top: int | None = None,
        skip: int | None = None,
        retry: bool = True,
    ) -> list[dict[str, Any]] | dict[str, Any]:
        """
        GET a TDX endpoint and return parsed JSON.

        Args:
            path:   API path (e.g. "Road/Traffic/Live/VD/City/Taipei")
            top:    $top query param
            skip:   $skip query param
            retry:  whether to retry on transient errors
        """
        url = f"{self._base_url}/{path.lstrip('/')}"
        params: dict[str, Any] = {}
        if top is not None:
            params["$top"] = top
        if skip is not None:
            params["$skip"] = skip

        attempt = 0
        while True:
            self._enforce_min_interval()
            token = self._auth.get_token()
            try:
                resp = self._http.get(
                    url,
                    params=params,
                    headers={"Authorization": f"Bearer {token}"},
                )
            except httpx.NetworkError as exc:
                if not retry or attempt >= self._max_retries:
                    raise TdxRequestError(
                        f"Network error after {attempt + 1} attempts: {exc}"
                    ) from exc
                attempt += 1
                self._sleep_before_retry(attempt, resp=None)
                continue

            # Handle 401 — token may be expired, force refresh
            if resp.status_code == 401:
                self._auth._token = None  # force refresh
                if attempt >= self._max_retries:
                    raise TdxRequestError("401 Unauthorized after retries")
                attempt += 1
                self._sleep_before_retry(attempt, resp=None)
                continue

            # Handle 429 — rate limited
            if resp.status_code == 429:
                retry_after = self._parse_retry_after(resp)
                if not retry or attempt >= self._max_retries:
                    raise TdxRequestError(
                        f"Rate limited (429) after {attempt + 1} attempts"
                    )
                attempt += 1
                self._sleep_before_retry(attempt, resp, retry_after)
                continue

            resp.raise_for_status()
            return resp.json()  # type: ignore[return-value]

    # --- Rate limiting helpers ---
    def _enforce_min_interval(self) -> None:
        if self._min_interval <= 0:
            return
        elapsed = time.time() - self._last_request_time
        wait = self._min_interval - elapsed
        if wait > 0:
            time.sleep(wait)
        self._last_request_time = time.time()

    def _sleep_before_retry(
        self,
        attempt: int,
        resp: httpx.Response | None,
        retry_after: float | None = None,
    ) -> None:
        if retry_after and retry_after > 0:
            delay = retry_after
        else:
            delay = min(
                self._backoff * (self._backoff_multiplier ** (attempt - 1)),
                self._max_backoff,
            )
            if self._jitter > 0:
                delay += random.uniform(0, self._jitter)

        logger.warning(
            "TDX request failed, retrying in %.1fs (attempt %d)",
            delay,
            attempt,
        )
        time.sleep(delay)

    def _parse_retry_after(self, resp: httpx.Response) -> float | None:
        if not self._respect_retry_after:
            return None
        val = resp.headers.get("Retry-After")
        if val:
            try:
                return float(val)
            except ValueError:
                pass
        return None

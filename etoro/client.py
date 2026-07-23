from __future__ import annotations

import random
import time
import uuid
from typing import Any

import requests

from .auth import get_random_private_key


class EToroRateLimitError(Exception):
    """Raised when the eToro API returns HTTP 429."""


class EToroAPIError(Exception):
    """Raised for non-recoverable eToro API errors."""


_BASE_URL = "https://public-api.etoro.com/api/v1"
_SEARCH_URL = f"{_BASE_URL}/user-info/people/search"
_PROFILES_URL = f"{_BASE_URL}/user-info/people"
_INSTRUMENTS_URL = "https://www.etoro.com/sapi/instrumentsmetadata/V1.1/instruments"


class EToroClient:
    """Centralised HTTP client for the public eToro API."""

    def __init__(
        self,
        api_key: str,
        *,
        timeout: int = 30,
        max_retries: int = 5,
        retry_delays: list[int] | None = None,
        rate_limit_delay: float = 1.1,
        long_pause_every: int = 250,
        long_pause_seconds: int = 60,
    ) -> None:
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delays = retry_delays or [5, 10, 20, 40, 60]
        self.rate_limit_delay = rate_limit_delay
        self.long_pause_every = long_pause_every
        self.long_pause_seconds = long_pause_seconds
        self._call_count = 0
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (compatible; alphasentra-etoro-client)",
                "Accept": "application/json",
                "x-api-key": api_key,
            }
        )

    def _headers(self) -> dict[str, str]:
        return {
            "x-user-key": get_random_private_key(),
            "x-request-id": str(uuid.uuid4()),
        }

    def _note_call(self, count: int = 1) -> None:
        self._call_count += count
        if self._call_count % self.long_pause_every == 0:
            print(
                f"  [throttle] Reached {self._call_count} API calls "
                f"— pausing {self.long_pause_seconds}s..."
            )
            self._sleep_with_progress(self.long_pause_seconds, label="Throttle pause")

    def _sleep_with_progress(self, seconds: float, label: str = "Waiting") -> None:
        for _ in range(int(seconds * 10)):
            time.sleep(0.1)

    def request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        """Send a single request with retry/back-off and return the raw Response.

        Retries on HTTP 429 / 404 and network-level failures.  The caller is
        responsible for parsing the response body.
        """
        for attempt in range(self.max_retries + 1):
            try:
                resp = self.session.request(
                    method,
                    url,
                    headers=self._headers(),
                    timeout=self.timeout,
                    **kwargs,
                )
                self._note_call()
                resp.raise_for_status()
                return resp
            except requests.HTTPError as exc:
                status = exc.response.status_code if exc.response else None
                if status in (429, 404) and attempt < self.max_retries:
                    time.sleep(self.retry_delays[attempt])
                    continue
                raise EToroAPIError(
                    f"HTTP {status} for {method} {url}"
                ) from exc
            except requests.RequestException as exc:
                if attempt < self.max_retries:
                    time.sleep(self.retry_delays[attempt])
                    continue
                raise EToroAPIError(
                    f"Network error for {method} {url}: {exc}"
                ) from exc
        raise EToroAPIError(f"Retries exhausted for {method} {url}")

    def get_json(self, method: str, url: str, **kwargs: Any) -> Any:
        """Like ``request`` but parses the response body as JSON."""
        resp = self.request(method, url, **kwargs)
        return resp.json()

    def search_page(self, *, period: str, sort: str, page: int, page_size: int) -> Any:
        """Fetch one page of the Pro Investor search endpoint."""
        return self.get_json(
            "GET",
            _SEARCH_URL,
            params={
                "period": period,
                "sort": sort,
                "isPopularInvestor": "true",
                "page": page,
                "pageSize": page_size,
            },
        )

    def get_profiles(self, usernames: list[str]) -> Any:
        """Fetch full profiles for a list of usernames (max 20)."""
        url = f"{_PROFILES_URL}?usernames={','.join(usernames)}"
        return self.get_json("GET", url)

    def get_instruments(self) -> Any:
        """Fetch instrument metadata from the sapi endpoint."""
        return self.get_json("GET", _INSTRUMENTS_URL)

    @property
    def call_count(self) -> int:
        return self._call_count

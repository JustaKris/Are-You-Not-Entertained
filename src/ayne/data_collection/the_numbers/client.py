"""Async, rate-limited client for scraping box office data from The Numbers.

The Numbers (the-numbers.com) has no public API, so this client fetches the
same public movie pages a browser would and parses the financial summary
table with BeautifulSoup. Design goals, in priority order:

1. Be a good citizen. The site's robots.txt allows generic crawling (it only
   restricts Amazonbot and rate-limits PetalBot), but this client still
    defaults to a deliberately conservative rate (`numbers_requests_per_second`, 1
    request/sec by default), a single concurrent request, a small per-run cap
   (`numbers_max_movies`), and a real browser-like User-Agent. It never
   touches the site's internal, token-gated search-suggestion endpoint
   (`/api/search-suggest.php`) - only public movie pages.
2. Be resilient to the site's URL quirks. The Numbers moves a leading
   "The"/"A"/"An" to the end of the title (e.g. "The Godfather" ->
   "Godfather-The"), frequently omits the year entirely for unambiguous
   titles, and its own internal release year can differ from TMDB's by a
   year (confirmed live: "Avengers: Infinity War" is filed under (2017) on
   The Numbers despite its 2018 theatrical release). A small, bounded set of
   URL candidates is tried per movie before giving up.
"""

import re
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import certifi
import httpx
from bs4 import BeautifulSoup

from ayne.core.config import settings
from ayne.core.logging import get_logger
from ayne.data_collection.rate_limiter import AsyncRateLimiter, retry_with_backoff
from ayne.data_collection.the_numbers.slug import candidate_urls

logger = get_logger(__name__)

# Label -> normalized field name, matched against the left-hand <td> of each
# row in the financial summary tables (case-insensitive, trailing ':' stripped).
# The site renders these across at least two separate tables per page (one
# with a stable `id="movie_finances"`, one without), so we scan all tables.
_FIELD_LABELS: dict[str, str] = {
    "domestic box office": "domestic_box_office",
    "international box office": "international_box_office",
    "worldwide box office": "worldwide_box_office",
    "production budget": "production_budget",
    "opening weekend": "opening_weekend_box_office",
}

_USER_AGENT = "Mozilla/5.0 (compatible; AYNE-data-collector/1.0)"


def parse_money(text: str) -> int | None:
    """Extract a dollar amount like '$1,071,177,215' from a text blob."""
    match = re.search(r"\$([\d,]+)", text)
    if not match:
        return None
    return int(match.group(1).replace(",", ""))


def extract_financial_data(soup: BeautifulSoup) -> dict[str, int]:
    """Extract known financial fields from a The Numbers movie page.

    Scans every `<table>` row for a label matching `_FIELD_LABELS` (e.g.
    "Domestic Box Office", "Production Budget") in the first cell and a
    dollar amount in the second cell.
    """
    financial_data: dict[str, int] = {}

    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 2:
                continue

            # The site sometimes uses non-breaking spaces (\xa0) inside labels
            # (e.g. "Production\xa0Budget:") - normalize before matching.
            label = cells[0].get_text(strip=True).replace("\xa0", " ").rstrip(":").strip().lower()
            field = _FIELD_LABELS.get(label)
            if not field or field in financial_data:
                continue

            amount = parse_money(cells[1].get_text(strip=True))
            if amount is not None:
                financial_data[field] = amount

    return financial_data


class TheNumbersClient:
    """Async, rate-limited scraper client for The Numbers box office data."""

    def __init__(
        self,
        requests_per_second: float | None = None,
        timeout: float | None = None,
    ):
        """Initialize the client.

        Args:
            requests_per_second: Rate limit (defaults to settings.numbers_requests_per_second)
            timeout: Per-request timeout in seconds (defaults to settings.api_timeout)
        """
        self.requests_per_second = requests_per_second or settings.numbers_requests_per_second  # type: ignore
        self.timeout = timeout or settings.api_timeout  # type: ignore

        # A single concurrent request at a time - this is HTML scraping of a
        # third-party site with no official API, not something to parallelize.
        self._rate_limiter = AsyncRateLimiter(
            requests_per_second=self.requests_per_second, max_concurrent=1
        )
        self._client: httpx.AsyncClient | None = None

        logger.debug(f"TheNumbers client initialized (rate: {self.requests_per_second} req/s)")

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                verify=certifi.where(),
                headers={"User-Agent": _USER_AGENT},
                follow_redirects=True,
            )
        return self._client

    async def _fetch(self, url: str) -> httpx.Response:
        client = await self._get_client()

        async def make_request() -> httpx.Response:
            async with self._rate_limiter:
                response = await client.get(url)
                # Only treat server errors as retryable; a 404 just means this
                # particular candidate slug/year guess was wrong.
                if response.status_code >= 500:
                    response.raise_for_status()
                return response

        return await retry_with_backoff(make_request, retry_count=2)

    async def get_financial_data(
        self, title: str, release_year: int | None = None
    ) -> tuple[dict[str, int], str] | None:
        """Look up box office/budget data for a single movie.

        Tries a small, bounded set of candidate URLs (see
        `the_numbers.slug.candidate_urls`). Returns None if no candidate page
        is found or none has usable financial data.
        """
        for url in candidate_urls(title, release_year):
            try:
                response = await self._fetch(url)
            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                logger.debug(f"TheNumbers request failed for {url}: {e}")
                continue

            if response.status_code != 200:
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            data = extract_financial_data(soup)
            if data:
                logger.debug(f"TheNumbers data found for '{title}' at {url}")
                return data, url

        logger.debug(f"No TheNumbers data found for '{title}' ({release_year})")
        return None

    async def get_batch_financial_data(
        self,
        movies: list[dict[str, Any]],
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch financial data for multiple movies sequentially (politeness over speed).

        Args:
            movies: List of dicts with at least "movie_id" and "title", and
                optionally "release_year"
            progress_callback: Optional callback(current, total) for progress updates

        Returns:
            List of dicts ready to upsert into `numbers_movies`: movie_id,
            release_year, source_url, last_updated_utc, plus whichever of
            domestic_box_office / international_box_office /
            worldwide_box_office / production_budget /
            opening_weekend_box_office were found.
        """
        total = len(movies)
        results: list[dict[str, Any]] = []
        for completed, movie in enumerate(movies, start=1):
            try:
                result = await self.get_financial_data(movie["title"], movie.get("release_year"))
            except KeyboardInterrupt:
                logger.info(
                    f"Cancelled - keeping {len(results)}/{len(movies)} movies scraped so far"
                )
                break

            if progress_callback:
                progress_callback(completed, total)
            elif completed % 10 == 0 or completed == total:
                logger.debug(f"Progress: {completed}/{total} movies scraped")

            if result is None:
                continue

            data, url = result
            results.append(
                {
                    "movie_id": movie["movie_id"],
                    "release_year": movie.get("release_year"),
                    "source_url": url,
                    "last_updated_utc": datetime.now(UTC).isoformat(),
                    **data,
                }
            )

        logger.debug(f"TheNumbers: found financial data for {len(results)}/{len(movies)} movies")
        return results

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

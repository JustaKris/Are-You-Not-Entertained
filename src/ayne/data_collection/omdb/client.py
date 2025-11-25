"""Async OMDB API client with rate limiting and retry logic.

Features:
- Async/await using httpx.AsyncClient
- Rate limiting via shared AsyncRateLimiter
- Semaphore for concurrent request control
- Exponential backoff retry logic via retry_with_backoff
"""

import asyncio
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import httpx

from ayne.core.config import settings
from ayne.core.exceptions import APIRateLimitExceeded
from ayne.core.logging import get_logger
from ayne.data_collection.omdb.normalizers import normalize_movie_response
from ayne.data_collection.rate_limiter import AsyncRateLimiter, retry_with_backoff

logger = get_logger(__name__)


class OMDBClient:
    """Async OMDB API client optimized for batch data collection with rate limiting."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        requests_per_second: float = 2.0,
        max_concurrent: int = 5,
        output_dir: Optional[Path] = None,
    ):
        """Initialize async OMDB client.

        Args:
            api_key: OMDB API key (defaults to settings)
            requests_per_second: Rate limit (requests per second)
            max_concurrent: Maximum concurrent requests
            output_dir: Directory for saving parquet files
        """
        self.api_key = (
            api_key
            or getattr(settings, "omdb_api_key", None)
            or getattr(settings, "OMDB_API_KEY", None)
        )
        if not self.api_key:
            raise ValueError("OMDB API key is required")

        # Support multiple possible setting names and provide a sensible default
        self.base_url = getattr(
            settings,
            "omdb_api_base_url",
            getattr(settings, "OMDB_API_BASE_URL", "http://www.omdbapi.com/"),
        )
        self.output_dir = output_dir or (settings.data_raw_dir / "omdb")  # type: ignore
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Shared rate limiter
        self._rate_limiter = AsyncRateLimiter(
            requests_per_second=requests_per_second, max_concurrent=max_concurrent
        )

        # Quota exceeded flag (set when 401 detected)
        self._quota_exceeded = asyncio.Event()

        logger.info(
            f"OMDB client initialized (rate: {requests_per_second} req/s, "
            f"concurrent: {max_concurrent}, output: {self.output_dir})"
        )

    async def _request(self, params: Dict, retry_count: int = 3) -> Dict:
        """Make async API request with rate limiting and retry logic.

        Args:
            params: Query parameters
            retry_count: Number of retries on failure

        Returns:
            JSON response as dict

        Raises:
            httpx.HTTPStatusError: If quota exceeded (401) detected
        """
        params["apikey"] = self.api_key

        async def make_request():
            # Acquire rate limiter slot
            async with self._rate_limiter:
                # Check quota flag AFTER acquiring slot, right before HTTP request
                if self._quota_exceeded.is_set():
                    # Create a fake 401 response without logging warnings
                    # Use a custom message so we can detect and suppress logs
                    raise httpx.HTTPStatusError(
                        "[Quota Check] Daily limit exceeded",
                        request=httpx.Request("GET", self.base_url),
                        response=httpx.Response(401),
                    )

                timeout_value = getattr(settings, "api_timeout", 10.0)
                async with httpx.AsyncClient(timeout=timeout_value) as client:
                    response = await client.get(self.base_url, params=params)
                    response.raise_for_status()
                    return response.json()

        try:
            return await retry_with_backoff(make_request, retry_count=retry_count)
        except httpx.HTTPStatusError as e:
            # Set flag if 401 detected from actual API call
            if e.response.status_code == 401 and "[Quota Check]" not in str(e):
                self._quota_exceeded.set()
            raise

    async def get_movie_by_imdb_id(self, imdb_id: str) -> Optional[Dict[str, Any]]:
        """Fetch movie by IMDb ID.

        Args:
            imdb_id: IMDb ID (e.g., 'tt0111161')

        Returns:
            Normalized movie data or None on error
        """
        if not imdb_id:
            return None

        params = {"i": imdb_id}

        try:
            data = await self._request(params)
            return normalize_movie_response(data)
        except Exception as e:
            logger.error(f"Failed to fetch OMDB data for {imdb_id}: {e}")
            return None

    async def get_batch_movies(
        self, imdb_ids: List[str], progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Dict[str, Any]]:
        """Fetch multiple movies by IMDb ID concurrently.

        Args:
            imdb_ids: List of IMDb IDs
            progress_callback: Optional callback(current, total) for progress updates

        Returns:
            List of normalized movie data

        Raises:
            APIRateLimitExceeded: If OMDB daily quota is reached (401 errors)
        """
        # Reset quota flag at the start of each batch
        self._quota_exceeded.clear()

        # Filter out None/empty IDs
        valid_ids = [id for id in imdb_ids if id]
        total = len(valid_ids)

        if total == 0:
            logger.warning("No valid IMDb IDs provided")
            return []

        logger.info(f"Fetching OMDB data for {total} movies")

        completed = 0
        successful_fetches = 0
        movies: List[Dict[str, Any]] = []

        # Create tasks for all movies
        async def fetch_with_progress(imdb_id: str) -> Optional[Dict[str, Any]]:
            nonlocal completed, successful_fetches

            try:
                result = await self.get_movie_by_imdb_id(imdb_id)
                completed += 1

                if result:
                    successful_fetches += 1

                if progress_callback:
                    progress_callback(completed, total)
                elif completed % 10 == 0 or completed == total:
                    logger.info(f"Progress: {completed}/{total} movies fetched")

                return result
            except httpx.HTTPStatusError as e:
                completed += 1

                # Check for 401 (daily quota exceeded)
                if e.response.status_code == 401:
                    # Only log warning for the FIRST 401 (actual API error)
                    # Subsequent 401s are from our flag check, silently skip them
                    if "[Quota Check]" not in str(e):
                        if not self._quota_exceeded.is_set():
                            self._quota_exceeded.set()
                            logger.warning(
                                f"OMDB daily quota exceeded after {successful_fetches} successful requests"
                            )
                    return None

                # Other HTTP errors
                logger.error(f"HTTP error fetching {imdb_id}: {e}")
                return None
            except Exception as e:
                # Don't log errors for our artificial quota check exceptions
                if "[Quota Check]" not in str(e):
                    logger.error(f"Error fetching {imdb_id}: {e}")
                completed += 1
                return None

        # Create tasks for all movies
        tasks = [fetch_with_progress(imdb_id) for imdb_id in valid_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out None and exceptions
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Task failed: {result}")
            elif isinstance(result, dict):
                movies.append(result)

        # If quota was exceeded, raise custom exception with progress info
        if self._quota_exceeded.is_set():
            raise APIRateLimitExceeded(
                api_name="OMDB",
                items_processed=successful_fetches,
                total_requested=total,
            )

        logger.info(f"Successfully fetched {len(movies)}/{total} movies")
        return movies

    async def close(self):
        """Cleanup method (placeholder for future resource cleanup)."""
        pass

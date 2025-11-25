"""TMDB API client with async/await, rate limiting, and concurrent request management.

Features:
- Async/await using httpx.AsyncClient
- Shared rate limiter with token bucket algorithm
- Retry logic with exponential backoff
- Concurrent request control
"""

import asyncio
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import httpx

from ayne.core.config import settings
from ayne.core.logging import get_logger
from ayne.data_collection.rate_limiter import AsyncRateLimiter, retry_with_backoff
from ayne.data_collection.tmdb.normalizers import (
    normalize_discover_results,
    normalize_movie_details,
)

logger = get_logger(__name__)


class TMDBClient:
    """TMDB API client optimized for batch data collection with rate limiting."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        requests_per_second: float = 4.0,
        max_concurrent: int = 10,
        output_dir: Optional[Path] = None,
    ):
        """Initialize TMDB client.

        Args:
            api_key: TMDB API key (defaults to settings)
            requests_per_second: Rate limit (requests per second)
            max_concurrent: Maximum concurrent requests
            output_dir: Directory for saving parquet files
        """
        # Prefer explicit api_key, fallback to settings attribute if present
        self.api_key = api_key or getattr(settings, "tmdb_api_key", None)
        if not self.api_key:
            raise ValueError("TMDB API key is required")

        # Base URL from settings (use getattr to avoid attribute errors in static checks)
        self.base_url = getattr(settings, "tmdb_api_base_url", "https://api.themoviedb.org/3")
        self.output_dir = output_dir or (settings.data_raw_dir / "tmdb")  # type: ignore
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Rate limiting
        self._rate_limiter = AsyncRateLimiter(
            requests_per_second=requests_per_second, max_concurrent=max_concurrent
        )

        logger.info(
            f"TMDB client initialized (rate: {requests_per_second} req/s, "
            f"concurrent: {max_concurrent}, output: {self.output_dir})"
        )

    async def _request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make async API request with rate limiting and retry logic.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            JSON response as dict
        """
        params = params or {}
        params["api_key"] = self.api_key
        url = f"{self.base_url}/{endpoint}"

        async def make_request():
            async with self._rate_limiter:
                timeout = getattr(settings, "api_timeout", 10)
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    return response.json()

        return await retry_with_backoff(make_request, retry_count=3)

    async def discover_movies_page(
        self,
        page: int,
        min_popularity: float = 10.0,
        min_vote_count: int = 50,
        min_release_year: int = 1950,
        max_release_year: Optional[int] = None,
        allowed_statuses: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch a single page of discovered movies with advanced filters.

        Args:
            page: Page number
            min_popularity: Minimum popularity score
            min_vote_count: Minimum vote count filter
            min_release_year: Minimum release year
            max_release_year: Maximum release year (None = no upper limit)
            allowed_statuses: Allowed release statuses (if None, not filtered)

        Returns:
            List of normalized movie dictionaries
        """
        endpoint = "discover/movie"
        params = {
            "popularity.gte": min_popularity,
            "vote_count.gte": min_vote_count,
            "primary_release_date.gte": f"{min_release_year}-01-01",
            "sort_by": "popularity.desc",
            "include_adult": "false",
            "include_video": "false",
            "page": page,
        }

        if max_release_year:
            params["primary_release_date.lte"] = f"{max_release_year}-12-31"

        response = await self._request(endpoint, params)
        movies = response.get("results", [])

        # Note: TMDB discover API doesn't support filtering by status directly
        # Status filtering will be done when fetching full details
        return normalize_discover_results(movies)

    async def _discover_movies_for_year_range(
        self,
        min_release_year: int,
        max_release_year: Optional[int],
        min_popularity: float,
        min_vote_count: int,
        allowed_statuses: Optional[List[str]],
        max_pages: Optional[int],
    ) -> List[Dict[str, Any]]:
        """Discover movies for a specific year range, with automatic splitting if needed.

        This method recursively splits year ranges when the TMDB 500-page limit is hit,
        ensuring complete data coverage without manual intervention.

        Args:
            min_release_year: Minimum release year
            max_release_year: Maximum release year (None = current year)
            min_popularity: Minimum popularity score
            min_vote_count: Minimum vote count filter
            allowed_statuses: Allowed release statuses
            max_pages: Maximum pages to fetch (user-specified limit)

        Returns:
            List of normalized movie dictionaries
        """
        from datetime import datetime

        TMDB_MAX_PAGES = 500

        # Default max_release_year to current year if not specified
        if max_release_year is None:
            max_release_year = datetime.now().year

        # Check if this is a single year (can't split further)
        if min_release_year >= max_release_year:
            # Single year - fetch what we can
            year_str = f"{min_release_year}"
            logger.info(f"Fetching movies for year: {year_str}")

            endpoint = "discover/movie"
            params = {
                "popularity.gte": min_popularity,
                "vote_count.gte": min_vote_count,
                "primary_release_date.gte": f"{min_release_year}-01-01",
                "primary_release_date.lte": f"{max_release_year}-12-31",
                "sort_by": "popularity.desc",
                "include_adult": "false",
                "include_video": "false",
                "page": 1,
            }

            response = await self._request(endpoint, params)
            total_pages = response.get("total_pages", 1)

            if total_pages > TMDB_MAX_PAGES:
                logger.warning(
                    f"Year {year_str} has {total_pages} pages (>{TMDB_MAX_PAGES}). "
                    f"Only first {TMDB_MAX_PAGES} pages will be fetched. "
                    f"Consider using stricter filters (--min-popularity, --min-votes)."
                )

            pages_to_fetch = min(total_pages, max_pages or TMDB_MAX_PAGES, TMDB_MAX_PAGES)
        else:
            # Multi-year range - check if we need to split
            endpoint = "discover/movie"
            params = {
                "popularity.gte": min_popularity,
                "vote_count.gte": min_vote_count,
                "primary_release_date.gte": f"{min_release_year}-01-01",
                "primary_release_date.lte": f"{max_release_year}-12-31",
                "sort_by": "popularity.desc",
                "include_adult": "false",
                "include_video": "false",
                "page": 1,
            }

            response = await self._request(endpoint, params)
            total_pages = response.get("total_pages", 1)

            # If we exceed the limit and can split, do so recursively
            if total_pages > TMDB_MAX_PAGES and min_release_year < max_release_year:
                mid_year = (min_release_year + max_release_year) // 2

                logger.info(
                    f"Year range {min_release_year}-{max_release_year} has {total_pages} pages "
                    f"(>{TMDB_MAX_PAGES}). Splitting into two ranges: "
                    f"{min_release_year}-{mid_year} and {mid_year + 1}-{max_release_year}"
                )

                # Recursively fetch both halves
                first_half = await self._discover_movies_for_year_range(
                    min_release_year=min_release_year,
                    max_release_year=mid_year,
                    min_popularity=min_popularity,
                    min_vote_count=min_vote_count,
                    allowed_statuses=allowed_statuses,
                    max_pages=max_pages,
                )

                second_half = await self._discover_movies_for_year_range(
                    min_release_year=mid_year + 1,
                    max_release_year=max_release_year,
                    min_popularity=min_popularity,
                    min_vote_count=min_vote_count,
                    allowed_statuses=allowed_statuses,
                    max_pages=max_pages,
                )

                # Combine results
                all_movies = first_half + second_half

                # Deduplicate by tmdb_id (in case of boundary overlaps)
                seen_ids = set()
                unique_movies = []
                for movie in all_movies:
                    tmdb_id = movie.get("tmdb_id")
                    if tmdb_id not in seen_ids:
                        seen_ids.add(tmdb_id)
                        unique_movies.append(movie)

                if len(all_movies) != len(unique_movies):
                    logger.debug(
                        f"Removed {len(all_movies) - len(unique_movies)} duplicate movies "
                        f"from year range split"
                    )

                return unique_movies

            # No split needed
            pages_to_fetch = min(total_pages, max_pages or TMDB_MAX_PAGES, TMDB_MAX_PAGES)

        # Fetch all pages for this range
        all_movies = []

        tasks = [
            self.discover_movies_page(
                page=page,
                min_popularity=min_popularity,
                min_vote_count=min_vote_count,
                min_release_year=min_release_year,
                max_release_year=max_release_year,
                allowed_statuses=allowed_statuses,
            )
            for page in range(1, pages_to_fetch + 1)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Failed to fetch page: {result}")
            elif isinstance(result, list):
                all_movies.extend(result)

        return all_movies

    async def discover_movies(
        self,
        max_movies: Optional[int] = None,
        min_popularity: float = 10.0,
        min_vote_count: int = 50,
        min_release_year: int = 1950,
        max_release_year: Optional[int] = None,
        allowed_statuses: Optional[List[str]] = None,
        max_pages: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Discover movies with advanced filtering using TMDB discover endpoint.

        This method automatically handles the TMDB 500-page limit by recursively
        splitting year ranges when needed, ensuring complete data coverage.

        Args:
            max_movies: Maximum number of movies to fetch (None = unlimited)
            min_popularity: Minimum popularity score
            min_vote_count: Minimum vote count filter
            min_release_year: Minimum release year
            max_release_year: Maximum release year (None = current year)
            allowed_statuses: Allowed release statuses (filtering happens at detail fetch)
            max_pages: Maximum pages to fetch per year range (overrides max_movies if set)

        Returns:
            List of normalized movie dictionaries
        """
        year_filter = f"year>={min_release_year}"
        if max_release_year:
            year_filter += f"-{max_release_year}"
        else:
            year_filter += "-present"

        logger.info(
            f"Discovering TMDB movies with filters: "
            f"popularity>={min_popularity}, votes>={min_vote_count}, "
            f"{year_filter}, max_movies={max_movies or 'unlimited'}"
        )

        # Use the new recursive method to handle year range splitting
        all_movies = await self._discover_movies_for_year_range(
            min_release_year=min_release_year,
            max_release_year=max_release_year,
            min_popularity=min_popularity,
            min_vote_count=min_vote_count,
            allowed_statuses=allowed_statuses,
            max_pages=max_pages,
        )

        # Trim to max_movies if specified
        if max_movies and len(all_movies) > max_movies:
            all_movies = all_movies[:max_movies]
            logger.info(f"Trimmed results to {max_movies} movies")

        logger.info(f"Total movies discovered: {len(all_movies)}")
        return all_movies

    async def get_movie_details(self, tmdb_id: int) -> Optional[Dict[str, Any]]:
        """Fetch full movie details by TMDB ID.

        Args:
            tmdb_id: TMDB movie ID

        Returns:
            Normalized movie details or None on error
        """
        endpoint = f"movie/{tmdb_id}"
        try:
            response = await self._request(endpoint)
            return normalize_movie_details(response)
        except Exception as e:
            logger.error(f"Failed to fetch details for TMDB ID {tmdb_id}: {e}")
            return None

    async def get_batch_movie_details(
        self,
        tmdb_ids: List[int],
        progress_callback: Optional[Callable[[int, int], None]] = None,
        allowed_statuses: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch details for multiple movies concurrently with optional status filtering.

        Args:
            tmdb_ids: List of TMDB movie IDs
            progress_callback: Optional callback(current, total) for progress updates
            allowed_statuses: Optional list of allowed release statuses to filter by

        Returns:
            List of normalized movie details
        """
        total = len(tmdb_ids)
        logger.info(f"Fetching details for {total} movies")

        completed = 0

        # Create tasks for all movies
        async def fetch_with_progress(tmdb_id: int) -> Optional[Dict[str, Any]]:
            nonlocal completed
            result = await self.get_movie_details(tmdb_id)
            completed += 1

            if progress_callback:
                progress_callback(completed, total)
            elif completed % 10 == 0 or completed == total:
                logger.info(f"Progress: {completed}/{total} movies fetched")

            return result

        tasks = [fetch_with_progress(tmdb_id) for tmdb_id in tmdb_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out None and exceptions, and apply status filtering if specified
        movies: list[dict[str, Any]] = []
        filtered_count = 0
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Task failed: {result}")
            elif isinstance(result, dict):
                # Apply status filtering if specified
                if allowed_statuses:
                    movie_status = result.get("status", "")
                    if movie_status in allowed_statuses:
                        movies.append(result)
                    else:
                        filtered_count += 1
                else:
                    movies.append(result)

        if filtered_count > 0:
            logger.info(
                f"Filtered out {filtered_count} movies due to release status not in {allowed_statuses}"
            )

        logger.info(f"Successfully fetched {len(movies)}/{total} movies")
        return movies

    async def close(self):
        """Cleanup method (placeholder for future resource cleanup)."""
        pass

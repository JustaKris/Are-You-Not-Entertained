"""
TMDB API client with async/await, rate limiting, and concurrent request management.

Features:
- Async/await using httpx.AsyncClient
- Shared rate limiter with token bucket algorithm
- Retry logic with exponential backoff
- Concurrent request control
"""

from typing import List, Dict, Optional, Any, Callable
from pathlib import Path
import asyncio
import httpx

from src.core.logging import get_logger
from src.core.config import settings
from src.data_collection.rate_limiter import AsyncRateLimiter, retry_with_backoff
from src.data_collection.tmdb.normalizers import normalize_discover_results, normalize_movie_details

logger = get_logger(__name__)


class TMDBClient:
    """TMDB API client optimized for batch data collection with rate limiting."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        requests_per_second: float = 4.0,
        max_concurrent: int = 10,
        output_dir: Optional[Path] = None
    ):
        """
        Initialize TMDB client.
        
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
            requests_per_second=requests_per_second,
            max_concurrent=max_concurrent
        )
        
        logger.info(
            f"TMDB client initialized (rate: {requests_per_second} req/s, "
            f"concurrent: {max_concurrent}, output: {self.output_dir})"
        )
    
    async def _request(
        self,
        endpoint: str,
        params: Optional[Dict] = None
    ) -> Dict:
        """
        Make async API request with rate limiting and retry logic.
        
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
        year: int,
        page: int,
        min_vote_count: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Fetch a single page of discovered movies.
        
        Args:
            year: Release year
            page: Page number
            min_vote_count: Minimum vote count filter
            
        Returns:
            List of normalized movie dictionaries
        """
        endpoint = "discover/movie"
        params = {
            "primary_release_date.gte": f"{year}-01-01",
            "primary_release_date.lte": f"{year}-12-31",
            "vote_count.gte": min_vote_count,
            "sort_by": "primary_release_date.desc",
            "include_adult": "false",
            "include_video": "false",
            "page": page
        }
        
        response = await self._request(endpoint, params)
        movies = response.get("results", [])
        return normalize_discover_results(movies)
    
    async def discover_movies(
        self,
        start_year: int,
        end_year: Optional[int] = None,
        min_vote_count: int = 200,
        max_pages: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Discover movies by year range with concurrent page fetching.
        
        Args:
            start_year: Starting year
            end_year: Ending year (defaults to start_year)
            min_vote_count: Minimum vote count filter
            max_pages: Maximum pages to fetch per year
            
        Returns:
            List of normalized movie dictionaries
        """
        end_year = end_year or start_year
        all_movies = []
        
        for year in range(start_year, end_year + 1):
            logger.info(f"Discovering TMDB movies for year {year}...")
            
            # Get first page to determine total pages
            first_page = await self.discover_movies_page(year, 1, min_vote_count)
            
            # Fetch first page to get total
            endpoint = "discover/movie"
            params = {
                "primary_release_date.gte": f"{year}-01-01",
                "primary_release_date.lte": f"{year}-12-31",
                "vote_count.gte": min_vote_count,
                "sort_by": "primary_release_date.desc",
                "include_adult": "false",
                "include_video": "false",
                "page": 1
            }
            response = await self._request(endpoint, params)
            total_pages = response.get("total_pages", 1)
            
            if max_pages:
                total_pages = min(total_pages, max_pages)
            
            logger.info(f"Fetching {total_pages} pages for year {year}")
            
            # Fetch remaining pages concurrently
            if total_pages > 1:
                tasks = [
                    self.discover_movies_page(year, page, min_vote_count)
                    for page in range(2, total_pages + 1)
                ]
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Collect results
                year_movies = first_page.copy()
                for result in results:
                    if isinstance(result, Exception):
                        logger.error(f"Failed to fetch page: {result}")
                    elif isinstance(result, list):
                        year_movies.extend(result)
                    else:
                        logger.error(f"Unexpected result type {type(result)} while fetching pages: {result}")
            else:
                year_movies = first_page
            
            logger.info(f"Discovered {len(year_movies)} movies for year {year}")
            all_movies.extend(year_movies)
        
        logger.info(f"Total movies discovered: {len(all_movies)}")
        return all_movies
    
    async def get_movie_details(self, tmdb_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch full movie details by TMDB ID.
        
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
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch details for multiple movies concurrently.
        
        Args:
            tmdb_ids: List of TMDB movie IDs
            progress_callback: Optional callback(current, total) for progress updates
            
        Returns:
            List of normalized movie details
        """
        total = len(tmdb_ids)
        logger.info(f"Fetching details for {total} movies")
        
        movies = []
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
        
        # Filter out None and exceptions
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Task failed: {result}")
            elif result is not None:
                movies.append(result)
        
        logger.info(f"Successfully fetched {len(movies)}/{total} movies")
        return movies
    
    async def close(self):
        """Cleanup method (placeholder for future resource cleanup)."""
        pass

"""Modern TMDB API client for DuckDB integration."""

import time
import httpx
from typing import List, Dict, Optional, Any
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq

from src.core.logging import get_logger
from src.core.config import settings
from .normalizers import normalize_discover_results, normalize_movie_details

logger = get_logger(__name__)


class TMDBClient:
    """TMDB API client optimized for batch data collection."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        delay: float = 0.1,
        output_dir: Optional[Path] = None
    ):
        """
        Initialize TMDB client.
        
        Args:
            api_key: TMDB API key (defaults to settings)
            delay: Rate limit delay between requests (seconds)
            output_dir: Directory for saving parquet files (defaults to settings.data_raw_dir/tmdb)
        """
        self.api_key = api_key or settings.tmdb_api_key
        if not self.api_key:
            raise ValueError("TMDB API key is required")
        
        self.base_url = settings.tmdb_api_base_url
        self.delay = delay
        self.output_dir = output_dir or (settings.data_raw_dir / "tmdb")  # type: ignore
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"TMDB client initialized (output: {self.output_dir})")
    
    def _request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make API request with error handling and rate limiting."""
        params = params or {}
        params["api_key"] = self.api_key
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            with httpx.Client(timeout=settings.api_timeout) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                time.sleep(self.delay)
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching {endpoint}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching {endpoint}: {e}")
            raise
    
    # ================================================================
    # Discover Movies (Basic Info)
    # ================================================================
    
    def discover_movies(
        self,
        start_year: int,
        end_year: Optional[int] = None,
        min_vote_count: int = 200,
        max_pages: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Discover movies by year and vote count.
        
        Args:
            start_year: Starting year
            end_year: Ending year (defaults to start_year)
            min_vote_count: Minimum vote count filter
            max_pages: Maximum pages to fetch per year
        
        Returns:
            List of movie dictionaries with basic info
        """
        end_year = end_year or start_year
        all_movies = []
        
        for year in range(start_year, end_year + 1):
            logger.info(f"Discovering TMDB movies for year {year}...")
            
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
            
            # Get first page to determine total pages
            response = self._request(endpoint, params)
            total_pages = response.get("total_pages", 1)
            
            if max_pages:
                total_pages = min(total_pages, max_pages)
            
            logger.info(f"Fetching {total_pages} pages for year {year}")
            
            # Fetch all pages
            year_movies = []
            for page in range(1, total_pages + 1):
                params["page"] = page
                response = self._request(endpoint, params)
                movies = response.get("results", [])
                year_movies.extend(movies)
                logger.debug(f"Fetched page {page}/{total_pages}")
            
            logger.info(f"Discovered {len(year_movies)} movies for year {year}")
            all_movies.extend(normalize_discover_results(year_movies))
        
        logger.info(f"Total movies discovered: {len(all_movies)}")
        return all_movies
    
    # ================================================================
    # Get Movie Details (Full Features)
    # ================================================================
    
    def get_movie_details(self, tmdb_id: int) -> Optional[Dict[str, Any]]:
        """Fetch full movie details by TMDB ID."""
        endpoint = f"movie/{tmdb_id}"
        try:
            response = self._request(endpoint)
            return normalize_movie_details(response)
        except Exception as e:
            logger.error(f"Failed to fetch details for TMDB ID {tmdb_id}: {e}")
            return None
    
    def get_batch_movie_details(self, tmdb_ids: List[int]) -> List[Dict[str, Any]]:
        """Fetch details for multiple movies."""
        movies = []
        total = len(tmdb_ids)
        
        for idx, tmdb_id in enumerate(tmdb_ids, 1):
            logger.info(f"Fetching movie {idx}/{total}: TMDB ID {tmdb_id}")
            movie = self.get_movie_details(tmdb_id)
            if movie:
                movies.append(movie)
        
        logger.info(f"Successfully fetched {len(movies)}/{total} movies")
        return movies
    
    # ================================================================
    # Storage
    # ================================================================
    
    def save_to_parquet(self, movies: List[Dict[str, Any]], filename: str = "tmdb_movies.parquet"):
        """Save movie data to parquet file."""
        if not movies:
            logger.warning("No data to save")
            return
        
        table = pa.Table.from_pylist(movies)
        output_path = self.output_dir / filename
        pq.write_table(table, output_path)
        logger.info(f"Saved {len(movies)} rows → {output_path}")

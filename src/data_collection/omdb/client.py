"""Modern OMDB API client for DuckDB integration."""

import time
import httpx
from typing import Optional, List, Dict, Any
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path

from src.core.logging import get_logger
from src.core.config import settings
from .normalizers import normalize_movie_response

logger = get_logger(__name__)


class OMDBClient:
    """OMDB API client optimized for batch data collection."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        delay: float = 0.1,
        output_dir: Optional[Path] = None
    ):
        """
        Initialize OMDB client.
        
        Args:
            api_key: OMDB API key (defaults to settings)
            delay: Rate limit delay between requests (seconds)
            output_dir: Directory for saving parquet files (defaults to settings.data_raw_dir/omdb)
        """
        self.api_key = api_key or settings.omdb_api_key
        if not self.api_key:
            raise ValueError("OMDB API key is required")
        
        self.base_url = settings.omdb_api_base_url
        self.delay = delay
        self.output_dir = output_dir or (settings.data_raw_dir / "omdb")  # type: ignore
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"OMDB client initialized (output: {self.output_dir})")
    
    # -------------------------------------------------------------
    # API calls
    # -------------------------------------------------------------

    def get_movie_by_imdb_id(self, imdb_id: str) -> Optional[Dict[str, Any]]:
        """Fetch movie by IMDb ID."""
        params = {"apikey": self.api_key, "i": imdb_id}
        
        try:
            with httpx.Client(timeout=settings.api_timeout) as client:
                resp = client.get(self.base_url, params=params)
                resp.raise_for_status()
                time.sleep(self.delay)
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching {imdb_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching {imdb_id}: {e}")
            return None

        data = resp.json()
        return normalize_movie_response(data)

    # -------------------------------------------------------------
    # Batch mode
    # -------------------------------------------------------------

    def get_batch_movies(self, imdb_ids: List[str]) -> List[Dict[str, Any]]:
        """Fetch multiple movies by IMDb ID."""
        results = []
        total = len(imdb_ids)
        
        for i, imdb_id in enumerate(imdb_ids, start=1):
            logger.info(f"Fetching movie {i}/{total}: {imdb_id}")
            row = self.get_movie_by_imdb_id(imdb_id)
            if row:
                results.append(row)
        
        logger.info(f"Successfully fetched {len(results)}/{total} movies")
        return results

    # -------------------------------------------------------------
    # Storage
    # -------------------------------------------------------------

    def save_to_parquet(self, movies: List[Dict[str, Any]], filename: str = "omdb_movies.parquet"):
        """Save movie data to parquet file."""
        if not movies:
            logger.warning("No data to save")
            return
        
        table = pa.Table.from_pylist(movies)
        output_path = self.output_dir / filename
        pq.write_table(table, output_path)
        logger.info(f"Saved {len(movies)} rows → {output_path}")


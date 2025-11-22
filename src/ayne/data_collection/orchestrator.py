"""Data collection orchestrator with intelligent refresh logic.

Coordinates:
- Refresh strategy decisions
- Async API calls to TMDB/OMDB
- Batch database updates
- Timestamp management
"""

from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

import pandas as pd

from ayne.core.logging import get_logger
from ayne.data_collection.omdb import OMDBClient
from ayne.data_collection.refresh_strategy import (
    calculate_refresh_plan,
    get_movies_due_for_refresh_query,
    should_freeze_movie,
)
from ayne.data_collection.tmdb import TMDBClient
from ayne.database.duckdb_client import DuckDBClient

logger = get_logger(__name__)


class DataCollectionOrchestrator:
    """Orchestrates intelligent data collection with refresh strategies.

    Features:
    - Age-based refresh intervals
    - Concurrent API calls with rate limiting
    - Batch database updates
    - Automatic data freezing for stable movies
    """

    def __init__(
        self,
        db: DuckDBClient,
        tmdb_client: Optional[TMDBClient] = None,
        omdb_client: Optional[OMDBClient] = None,
    ):
        """Initialize orchestrator.

        Args:
            db: DuckDB client instance
            tmdb_client: TMDB client (creates new if None)
            omdb_client: OMDB client (creates new if None)
        """
        self.db = db
        self.tmdb_client = tmdb_client or TMDBClient()
        self.omdb_client = omdb_client or OMDBClient()

        logger.info("Data collection orchestrator initialized")

    async def discover_and_store_movies(
        self,
        start_year: int,
        end_year: Optional[int] = None,
        min_vote_count: int = 200,
        max_pages: Optional[int] = None,
    ) -> int:
        """Discover new movies from TMDB and store in database.

        Args:
            start_year: Starting year
            end_year: Ending year (defaults to start_year)
            min_vote_count: Minimum vote count filter
            max_pages: Maximum pages to fetch per year

        Returns:
            Number of movies discovered
        """
        logger.info(f"Discovering movies from TMDB ({start_year}-{end_year or start_year})...")

        movies = await self.tmdb_client.discover_movies(
            start_year=start_year,
            end_year=end_year,
            min_vote_count=min_vote_count,
            max_pages=max_pages,
        )

        if not movies:
            logger.warning("No movies discovered")
            return 0

        # Store in database
        df_movies = pd.DataFrame(movies)
        movies_for_db = df_movies[["tmdb_id", "title", "release_date"]].copy()

        self.db.upsert_dataframe("movies", movies_for_db, key_columns=["tmdb_id"])
        logger.info(f"✅ Stored {len(movies)} movies")

        return len(movies)

    def get_movies_for_refresh(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Get movies that need data refresh based on age and last update.

        Args:
            limit: Maximum number of movies to return

        Returns:
            DataFrame of movies due for refresh
        """
        query = get_movies_due_for_refresh_query(limit=limit, include_frozen=False)
        movies_df = self.db.query(query)

        logger.info(f"Found {len(movies_df)} movies due for refresh")
        return movies_df

    async def refresh_movie_data(
        self,
        movies_df: pd.DataFrame,
        fetch_tmdb: bool = True,
        fetch_omdb: bool = True,
        batch_size: int = 50,
    ) -> Tuple[int, int, int]:
        """Refresh data for multiple movies based on their refresh needs.

        Args:
            movies_df: DataFrame of movies to refresh
            fetch_tmdb: Whether to fetch TMDB data
            fetch_omdb: Whether to fetch OMDB data
            batch_size: Batch size for database updates

        Returns:
            Tuple of (tmdb_updated, omdb_updated, movies_frozen)
        """
        if movies_df.empty:
            logger.info("No movies to refresh")
            return 0, 0, 0

        total = len(movies_df)
        logger.info(f"Starting refresh for {total} movies...")

        tmdb_updated = 0
        omdb_updated = 0
        movies_frozen = 0

        # Calculate refresh plans for all movies
        movies_df["refresh_plan"] = movies_df.apply(
            lambda row: calculate_refresh_plan(row.to_dict()), axis=1
        )

        # Separate movies by what needs updating
        needs_tmdb = (
            movies_df[movies_df["refresh_plan"].apply(lambda x: x["needs_tmdb"])]
            if fetch_tmdb
            else pd.DataFrame()
        )

        needs_omdb = (
            movies_df[movies_df["refresh_plan"].apply(lambda x: x["needs_omdb"])]
            if fetch_omdb
            else pd.DataFrame()
        )

        # Fetch TMDB data
        if not needs_tmdb.empty:
            logger.info(f"Fetching TMDB data for {len(needs_tmdb)} movies...")
            tmdb_ids = needs_tmdb["tmdb_id"].dropna().astype(int).tolist()

            if tmdb_ids:
                tmdb_data = await self.tmdb_client.get_batch_movie_details(tmdb_ids)

                if tmdb_data:
                    df_tmdb = pd.DataFrame(tmdb_data)
                    self.db.upsert_dataframe("tmdb_movies", df_tmdb, key_columns=["tmdb_id"])

                    # Update timestamps in movies table
                    now = datetime.now(timezone.utc).isoformat()
                    for tmdb_id in df_tmdb["tmdb_id"]:
                        self.db.execute(
                            "UPDATE movies SET last_tmdb_update = ? WHERE tmdb_id = ?",
                            [now, tmdb_id],
                        )

                    tmdb_updated = len(tmdb_data)
                    logger.info(f"✅ Updated TMDB data for {tmdb_updated} movies")

        # Fetch OMDB data
        if not needs_omdb.empty:
            logger.info(f"Fetching OMDB data for {len(needs_omdb)} movies...")

            # Get IMDb IDs from tmdb_movies table for these movies
            tmdb_ids_str = ",".join(str(int(id)) for id in needs_omdb["tmdb_id"].dropna())

            if tmdb_ids_str:
                imdb_query = f"""
                    SELECT DISTINCT t.imdb_id
                    FROM tmdb_movies t
                    WHERE t.tmdb_id IN ({tmdb_ids_str})
                      AND t.imdb_id IS NOT NULL
                      AND t.imdb_id != ''
                """
                imdb_df = self.db.query(imdb_query)
                imdb_ids = imdb_df["imdb_id"].tolist()

                if imdb_ids:
                    omdb_data = await self.omdb_client.get_batch_movies(imdb_ids)

                    if omdb_data:
                        df_omdb = pd.DataFrame(omdb_data)
                        self.db.upsert_dataframe("omdb_movies", df_omdb, key_columns=["imdb_id"])

                        # Update timestamps in movies table
                        now = datetime.now(timezone.utc).isoformat()
                        for imdb_id in df_omdb["imdb_id"]:
                            self.db.execute(
                                "UPDATE movies SET last_omdb_update = ? WHERE imdb_id = ?",
                                [now, imdb_id],
                            )

                        omdb_updated = len(omdb_data)
                        logger.info(f"✅ Updated OMDB data for {omdb_updated} movies")

        # Update last_full_refresh for movies that got both updates
        if tmdb_updated > 0 and omdb_updated > 0:
            now = datetime.now(timezone.utc).isoformat()
            self.db.execute(
                """
                UPDATE movies
                SET last_full_refresh = ?
                WHERE last_tmdb_update IS NOT NULL
                  AND last_omdb_update IS NOT NULL
                  AND last_full_refresh IS NULL
                """,
                [now],
            )

        # Check for movies that should be frozen
        for _, movie in movies_df.iterrows():
            release_date = pd.to_datetime(movie["release_date"])
            # Ensure timezone awareness
            if release_date.tzinfo is None:
                release_date = release_date.replace(tzinfo=timezone.utc)

            last_tmdb = (
                pd.to_datetime(movie["last_tmdb_update"])
                if pd.notna(movie["last_tmdb_update"])
                else None
            )
            if last_tmdb and last_tmdb.tzinfo is None:
                last_tmdb = last_tmdb.replace(tzinfo=timezone.utc)

            last_omdb = (
                pd.to_datetime(movie["last_omdb_update"])
                if pd.notna(movie["last_omdb_update"])
                else None
            )
            if last_omdb and last_omdb.tzinfo is None:
                last_omdb = last_omdb.replace(tzinfo=timezone.utc)

            if should_freeze_movie(
                release_date, last_tmdb, last_omdb, consecutive_unchanged_cycles=3
            ):
                self.db.execute(
                    "UPDATE movies SET data_frozen = TRUE WHERE movie_id = ?", [movie["movie_id"]]
                )
                movies_frozen += 1

        if movies_frozen > 0:
            logger.info(f"🔒 Froze {movies_frozen} stable movies")

        return tmdb_updated, omdb_updated, movies_frozen

    async def run_full_collection(
        self,
        discover_start_year: Optional[int] = None,
        discover_end_year: Optional[int] = None,
        max_discover_pages: Optional[int] = None,
        refresh_limit: Optional[int] = 100,
        discover_min_vote_count: int = 200,
    ) -> Dict[str, int]:
        """Run complete collection workflow: discover + refresh.

        Args:
            discover_start_year: Year to start discovery (None to skip discovery)
            discover_end_year: Year to end discovery
            max_discover_pages: Max pages per year for discovery
            refresh_limit: Max movies to refresh
            discover_min_vote_count: Minimum vote count for discovery

        Returns:
            Dict with collection statistics
        """
        stats = {"discovered": 0, "tmdb_updated": 0, "omdb_updated": 0, "frozen": 0}

        # Step 1: Discover new movies (if requested)
        if discover_start_year:
            stats["discovered"] = await self.discover_and_store_movies(
                start_year=discover_start_year,
                end_year=discover_end_year,
                min_vote_count=discover_min_vote_count,
                max_pages=max_discover_pages,
            )

        # Step 2: Refresh existing movies
        movies_to_refresh = self.get_movies_for_refresh(limit=refresh_limit)

        if not movies_to_refresh.empty:
            tmdb_updated, omdb_updated, frozen = await self.refresh_movie_data(
                movies_to_refresh, fetch_tmdb=True, fetch_omdb=True
            )
            stats["tmdb_updated"] = tmdb_updated
            stats["omdb_updated"] = omdb_updated
            stats["frozen"] = frozen

        return stats

    async def close(self):
        """Cleanup resources."""
        await self.tmdb_client.close()
        await self.omdb_client.close()
        logger.info("Orchestrator closed")

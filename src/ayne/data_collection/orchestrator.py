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
        max_movies: Optional[int] = None,
        min_popularity: Optional[float] = None,
        min_vote_count: Optional[int] = None,
        min_release_year: Optional[int] = None,
        max_release_year: Optional[int] = None,
        allowed_statuses: Optional[list[str]] = None,
        max_pages: Optional[int] = None,
    ) -> int:
        """Discover new movies from TMDB and store in database.

        Args:
            max_movies: Maximum number of movies to fetch (None = unlimited)
            min_popularity: Minimum popularity score (defaults to settings)
            min_vote_count: Minimum vote count filter (defaults to settings)
            min_release_year: Minimum release year (defaults to settings)
            max_release_year: Maximum release year (None = no upper limit)
            allowed_statuses: Allowed release statuses (defaults to settings)
            max_pages: Maximum pages to fetch (overrides max_movies)

        Returns:
            Number of movies discovered
        """
        from ayne.core.config import settings

        # Use settings defaults if not provided
        min_popularity = min_popularity or settings.tmdb_min_popularity
        min_vote_count = min_vote_count or settings.tmdb_min_vote_count
        min_release_year = min_release_year or settings.tmdb_min_release_year
        allowed_statuses = allowed_statuses or settings.tmdb_allowed_release_statuses
        max_movies = max_movies or settings.tmdb_max_movies

        logger.info("Discovering movies from TMDB with filters...")

        movies = await self.tmdb_client.discover_movies(
            max_movies=max_movies,
            min_popularity=min_popularity,
            min_vote_count=min_vote_count,
            min_release_year=min_release_year,
            max_release_year=max_release_year,
            allowed_statuses=allowed_statuses,
            max_pages=max_pages,
        )

        if not movies:
            logger.warning("No movies discovered")
            return 0

        # Store in database
        df_movies = pd.DataFrame(movies)
        movies_for_db = df_movies[["tmdb_id", "title", "release_date"]].copy()

        # Set last_tmdb_update to track discovery
        now = datetime.now(timezone.utc).isoformat()
        movies_for_db["last_tmdb_update"] = now

        self.db.upsert_dataframe("movies", movies_for_db, key_columns=["tmdb_id"])
        logger.info(f"✅ Stored {len(movies)} movies")

        return len(movies)

    def get_movies_for_refresh(
        self,
        limit: Optional[int] = None,
        min_release_year: Optional[int] = None,
        max_release_year: Optional[int] = None,
    ) -> pd.DataFrame:
        """Get movies that need data refresh based on age and last update.

        Args:
            limit: Maximum number of movies to return
            min_release_year: Filter movies by minimum release year
            max_release_year: Filter movies by maximum release year

        Returns:
            DataFrame of movies due for refresh
        """
        query = get_movies_due_for_refresh_query(limit=None, include_frozen=False)

        # Add year filtering to the base query (before ORDER BY and LIMIT)
        if min_release_year or max_release_year:
            # Insert WHERE conditions before ORDER BY
            order_by_pos = query.upper().find("ORDER BY")

            year_conditions = []
            if min_release_year:
                year_conditions.append(f"m.release_date >= '{min_release_year}-01-01'")
            if max_release_year:
                year_conditions.append(f"m.release_date <= '{max_release_year}-12-31'")

            year_filter = " AND " + " AND ".join(year_conditions)

            if order_by_pos > 0:
                query = query[:order_by_pos] + year_filter + " " + query[order_by_pos:]
            else:
                query += year_filter

        # Add limit at the end
        if limit:
            query += f" LIMIT {limit}"

        movies_df = self.db.query(query)

        logger.info(f"Found {len(movies_df)} movies due for refresh")
        return movies_df

    async def refresh_movie_data(
        self,
        movies_df: pd.DataFrame,
        fetch_tmdb: bool = True,
        fetch_omdb: bool = True,
        batch_size: int = 50,
        omdb_max_movies: Optional[int] = None,
        allowed_statuses: Optional[list[str]] = None,
    ) -> Tuple[int, int, int]:
        """Refresh data for multiple movies based on their refresh needs.

        Args:
            movies_df: DataFrame of movies to refresh
            fetch_tmdb: Whether to fetch TMDB data
            fetch_omdb: Whether to fetch OMDB data
            batch_size: Batch size for database updates
            omdb_max_movies: Maximum movies to fetch from OMDB (respects API limits)
            allowed_statuses: Allowed release statuses for TMDB filtering

        Returns:
            Tuple of (tmdb_updated, omdb_updated, movies_frozen)
        """
        from ayne.core.config import settings

        if movies_df.empty:
            logger.info("No movies to refresh")
            return 0, 0, 0

        total = len(movies_df)
        logger.info(f"Starting refresh for {total} movies...")

        tmdb_updated = 0
        omdb_updated = 0
        movies_frozen = 0

        # Use settings default if not provided
        allowed_statuses = allowed_statuses or settings.tmdb_allowed_release_statuses
        omdb_max_movies = omdb_max_movies or settings.omdb_max_movies

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
                tmdb_data = await self.tmdb_client.get_batch_movie_details(
                    tmdb_ids, allowed_statuses=allowed_statuses
                )

                if tmdb_data:
                    df_tmdb = pd.DataFrame(tmdb_data)
                    self.db.upsert_dataframe("tmdb_movies", df_tmdb, key_columns=["tmdb_id"])

                    # Update timestamps and IMDb IDs in movies table
                    now = datetime.now(timezone.utc).isoformat()
                    for _, row in df_tmdb.iterrows():
                        tmdb_id = row["tmdb_id"]
                        imdb_id = row.get("imdb_id")

                        if imdb_id:
                            self.db.execute(
                                "UPDATE movies SET last_tmdb_update = ?, imdb_id = ? WHERE tmdb_id = ?",
                                [now, imdb_id, tmdb_id],
                            )
                        else:
                            self.db.execute(
                                "UPDATE movies SET last_tmdb_update = ? WHERE tmdb_id = ?",
                                [now, tmdb_id],
                            )

                    tmdb_updated = len(tmdb_data)
                    logger.info(f"✅ Updated TMDB data for {tmdb_updated} movies")

        # Fetch OMDB data
        if not needs_omdb.empty:
            # Limit OMDB requests based on configuration
            omdb_batch_size = min(len(needs_omdb), omdb_max_movies)
            if omdb_batch_size < len(needs_omdb):
                logger.warning(
                    f"Limiting OMDB fetch to {omdb_batch_size} movies (max: {omdb_max_movies})"
                )
                needs_omdb = needs_omdb.head(omdb_batch_size)

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

        # Update last_full_refresh for movies that got both TMDB and OMDB updates in this batch
        if tmdb_updated > 0 or omdb_updated > 0:
            now = datetime.now(timezone.utc).isoformat()

            # Get tmdb_ids that were updated in this batch
            updated_tmdb_ids = set()
            if tmdb_updated > 0 and not needs_tmdb.empty:
                updated_tmdb_ids = set(needs_tmdb["tmdb_id"].dropna().astype(int).tolist())

            # Get imdb_ids that were updated and map to tmdb_ids
            updated_via_omdb_tmdb_ids = set()
            if omdb_updated > 0 and not needs_omdb.empty:
                updated_via_omdb_tmdb_ids = set(needs_omdb["tmdb_id"].dropna().astype(int).tolist())

            # Find movies that got both updates in this batch
            both_updated_ids = updated_tmdb_ids.intersection(updated_via_omdb_tmdb_ids)

            if both_updated_ids:
                ids_str = ",".join(str(id) for id in both_updated_ids)
                self.db.execute(
                    f"""
                    UPDATE movies
                    SET last_full_refresh = ?
                    WHERE tmdb_id IN ({ids_str})
                      AND last_tmdb_update IS NOT NULL
                      AND last_omdb_update IS NOT NULL
                    """,
                    [now],
                )
                logger.info(f"📅 Updated last_full_refresh for {len(both_updated_ids)} movies")

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
        discover_movies: bool = False,
        max_discover_movies: Optional[int] = None,
        max_discover_pages: Optional[int] = None,
        refresh_limit: Optional[int] = 100,
        min_popularity: Optional[float] = None,
        min_vote_count: Optional[int] = None,
        min_release_year: Optional[int] = None,
        allowed_statuses: Optional[list[str]] = None,
        omdb_max_movies: Optional[int] = None,
    ) -> Dict[str, int]:
        """Run complete collection workflow: discover + refresh.

        Args:
            discover_movies: Whether to run discovery (False to skip)
            max_discover_movies: Max movies to discover (None = unlimited)
            max_discover_pages: Max pages for discovery
            refresh_limit: Max movies to refresh
            min_popularity: Minimum popularity for discovery (defaults to settings)
            min_vote_count: Minimum vote count for discovery (defaults to settings)
            min_release_year: Minimum release year for discovery (defaults to settings)
            allowed_statuses: Allowed release statuses (defaults to settings)
            omdb_max_movies: Max OMDB movies to fetch (defaults to settings)

        Returns:
            Dict with collection statistics
        """
        stats = {"discovered": 0, "tmdb_updated": 0, "omdb_updated": 0, "frozen": 0}

        # Step 1: Discover new movies (if requested)
        if discover_movies:
            stats["discovered"] = await self.discover_and_store_movies(
                max_movies=max_discover_movies,
                min_popularity=min_popularity,
                min_vote_count=min_vote_count,
                min_release_year=min_release_year,
                allowed_statuses=allowed_statuses,
                max_pages=max_discover_pages,
            )

        # Step 2: Refresh existing movies
        movies_to_refresh = self.get_movies_for_refresh(limit=refresh_limit)

        if not movies_to_refresh.empty:
            tmdb_updated, omdb_updated, frozen = await self.refresh_movie_data(
                movies_to_refresh,
                fetch_tmdb=True,
                fetch_omdb=True,
                omdb_max_movies=omdb_max_movies,
                allowed_statuses=allowed_statuses,
            )
            stats["tmdb_updated"] = tmdb_updated
            stats["omdb_updated"] = omdb_updated
            stats["frozen"] = frozen

        return stats

    async def enrich_tmdb_details(
        self,
        limit: Optional[int] = None,
        min_release_year: Optional[int] = None,
        max_release_year: Optional[int] = None,
        allowed_statuses: Optional[list[str]] = None,
    ) -> int:
        """Fetch detailed TMDB data for movies that only have basic discovery info.

        Args:
            limit: Maximum number of movies to enrich
            min_release_year: Filter movies by minimum release year
            max_release_year: Filter movies by maximum release year
            allowed_statuses: Allowed release statuses (defaults to settings)

        Returns:
            Number of movies enriched with TMDB details
        """
        from ayne.core.config import settings

        allowed_statuses = allowed_statuses or settings.tmdb_allowed_release_statuses

        # Query movies that have tmdb_id but not detailed data yet
        query = """
            SELECT m.*
            FROM movies m
            LEFT JOIN tmdb_movies t ON m.tmdb_id = t.tmdb_id
            WHERE m.tmdb_id IS NOT NULL
              AND t.tmdb_id IS NULL
        """

        # Add year filtering
        if min_release_year:
            query += f" AND m.release_date >= '{min_release_year}-01-01'"
        if max_release_year:
            query += f" AND m.release_date <= '{max_release_year}-12-31'"

        query += " ORDER BY m.last_tmdb_update DESC"

        if limit:
            query += f" LIMIT {limit}"

        movies_to_enrich = self.db.query(query)

        if movies_to_enrich.empty:
            logger.info("No movies need TMDB enrichment")
            return 0

        logger.info(f"Enriching {len(movies_to_enrich)} movies with TMDB details...")

        tmdb_ids = movies_to_enrich["tmdb_id"].dropna().astype(int).tolist()

        if not tmdb_ids:
            return 0

        # Fetch detailed data
        tmdb_data = await self.tmdb_client.get_batch_movie_details(
            tmdb_ids, allowed_statuses=allowed_statuses
        )

        if not tmdb_data:
            logger.warning("No TMDB data fetched")
            return 0

        # Store in database
        df_tmdb = pd.DataFrame(tmdb_data)
        self.db.upsert_dataframe("tmdb_movies", df_tmdb, key_columns=["tmdb_id"])

        # Update timestamps and IMDb IDs in movies table
        now = datetime.now(timezone.utc).isoformat()
        for _, row in df_tmdb.iterrows():
            tmdb_id = row["tmdb_id"]
            imdb_id = row.get("imdb_id")

            if imdb_id:
                self.db.execute(
                    "UPDATE movies SET last_tmdb_update = ?, imdb_id = ? WHERE tmdb_id = ?",
                    [now, imdb_id, tmdb_id],
                )
            else:
                self.db.execute(
                    "UPDATE movies SET last_tmdb_update = ? WHERE tmdb_id = ?",
                    [now, tmdb_id],
                )

        logger.info(f"✅ Enriched {len(tmdb_data)} movies with TMDB details")
        return len(tmdb_data)

    async def enrich_omdb_data(
        self,
        limit: Optional[int] = None,
        min_release_year: Optional[int] = None,
        max_release_year: Optional[int] = None,
    ) -> int:
        """Fetch OMDB data for movies that have IMDb IDs but no OMDB data yet.

        Args:
            limit: Maximum number of movies to enrich
            min_release_year: Filter movies by minimum release year
            max_release_year: Filter movies by maximum release year

        Returns:
            Number of movies enriched with OMDB data
        """
        # Query movies that have imdb_id but no OMDB data yet
        query = """
            SELECT m.*
            FROM movies m
            LEFT JOIN omdb_movies o ON m.imdb_id = o.imdb_id
            WHERE m.imdb_id IS NOT NULL
              AND m.imdb_id != ''
              AND o.imdb_id IS NULL
        """

        # Add year filtering
        if min_release_year:
            query += f" AND m.release_date >= '{min_release_year}-01-01'"
        if max_release_year:
            query += f" AND m.release_date <= '{max_release_year}-12-31'"

        query += " ORDER BY m.release_date DESC"

        if limit:
            query += f" LIMIT {limit}"

        movies_to_enrich = self.db.query(query)

        if movies_to_enrich.empty:
            logger.info("No movies need OMDB enrichment")
            return 0

        logger.info(f"Enriching {len(movies_to_enrich)} movies with OMDB data...")

        imdb_ids = movies_to_enrich["imdb_id"].dropna().tolist()

        if not imdb_ids:
            return 0

        # Fetch OMDB data
        omdb_data = await self.omdb_client.get_batch_movies(imdb_ids)

        if not omdb_data:
            logger.warning("No OMDB data fetched")
            return 0

        # Store in database
        df_omdb = pd.DataFrame(omdb_data)
        self.db.upsert_dataframe("omdb_movies", df_omdb, key_columns=["imdb_id"])

        # Update timestamps in movies table
        now = datetime.now(timezone.utc).isoformat()
        for imdb_id in df_omdb["imdb_id"]:
            self.db.execute(
                "UPDATE movies SET last_omdb_update = ? WHERE imdb_id = ?",
                [now, imdb_id],
            )

        logger.info(f"✅ Enriched {len(omdb_data)} movies with OMDB data")
        return len(omdb_data)

    async def close(self):
        """Cleanup resources."""
        await self.tmdb_client.close()
        await self.omdb_client.close()
        logger.info("Orchestrator closed")

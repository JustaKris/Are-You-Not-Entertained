"""Data collection orchestrator with intelligent refresh logic.

Coordinates:
- Refresh strategy decisions
- Async API calls to TMDB/OMDB
- Batch database updates
- Timestamp management
"""

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import pandas as pd

from ayne.core.exceptions import APIRateLimitError, UserCancelledError
from ayne.core.logging import get_logger
from ayne.data_collection.api_usage import get_remaining_quota, record_api_usage
from ayne.data_collection.omdb import OMDBClient
from ayne.data_collection.refresh_strategy import (
    OMDB_VOLATILE_FIELDS,
    TMDB_VOLATILE_FIELDS,
    calculate_refresh_plan,
    get_movies_due_for_refresh_query,
    has_meaningful_change,
    should_freeze_movie,
)
from ayne.data_collection.the_numbers import TheNumbersClient
from ayne.data_collection.tmdb import TMDBClient
from ayne.database.duckdb_client import DuckDBClient

logger = get_logger(__name__)

CollectionProgressCallback = Callable[[str, int | None, int | None], None]


def _to_utc_datetime(value: Any) -> datetime | None:
    """Convert a pandas/py timestamp-like value to a tz-aware UTC datetime, or None."""
    if value is None or pd.isna(value):
        return None
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize(UTC)
    return ts.to_pydatetime()


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
        tmdb_client: TMDBClient | None = None,
        omdb_client: OMDBClient | None = None,
        numbers_client: TheNumbersClient | None = None,
    ):
        """Initialize orchestrator.

        Args:
            db: DuckDB client instance
            tmdb_client: TMDB client (creates new if None)
            omdb_client: OMDB client (creates new if None)
            numbers_client: The Numbers client (creates new if None)
        """
        self.db = db
        self.tmdb_client = tmdb_client or TMDBClient()
        self.omdb_client = omdb_client or OMDBClient()
        self.numbers_client = numbers_client or TheNumbersClient()

        logger.debug("Data collection orchestrator initialized")

    async def discover_and_store_movies(
        self,
        max_movies: int | None = None,
        min_popularity: float | None = None,
        min_vote_count: int | None = None,
        min_release_year: int | None = None,
        max_release_year: int | None = None,
        allowed_statuses: list[str] | None = None,
        max_pages: int | None = None,
        progress_callback: CollectionProgressCallback | None = None,
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
            progress_callback: Optional callback(stage, completed, total)

        Returns:
            Number of movies discovered
        """
        from typing import cast

        from ayne.core.config import Settings
        from ayne.core.config import settings as _settings

        settings = cast(Settings, _settings)
        min_popularity = cast(float, min_popularity or settings.tmdb_min_popularity)
        min_vote_count = cast(int, min_vote_count or settings.tmdb_min_vote_count)
        min_release_year = cast(int, min_release_year or settings.tmdb_min_release_year)
        allowed_statuses = allowed_statuses or settings.tmdb_allowed_release_statuses
        max_movies = max_movies or settings.tmdb_max_movies

        logger.debug("Discovering movies from TMDB with filters...")

        movies = await self.tmdb_client.discover_movies(
            max_movies=max_movies,
            min_popularity=min_popularity,
            min_vote_count=min_vote_count,
            min_release_year=min_release_year,
            max_release_year=max_release_year,
            allowed_statuses=allowed_statuses,
            max_pages=max_pages,
            progress_callback=progress_callback,
        )

        if not movies:
            logger.warning("No movies discovered")
            return 0

        # Store in database
        df_movies = pd.DataFrame(movies)
        movies_for_db = df_movies[["tmdb_id", "title", "release_date"]].copy()

        # Set last_tmdb_update to track discovery
        now = datetime.now(UTC).isoformat()
        movies_for_db["last_tmdb_update"] = now

        self.db.upsert_dataframe("movies", movies_for_db, key_columns=["tmdb_id"])
        logger.info(f"✅ Stored {len(movies)} movies")

        return len(movies)

    def get_movies_for_refresh(
        self,
        limit: int | None = None,
        min_release_year: int | None = None,
        max_release_year: int | None = None,
        include_frozen: bool = False,
        data_source: str | None = None,
    ) -> pd.DataFrame:
        """Get movies that need data refresh based on age and last update.

        Args:
            limit: Maximum number of movies to return
            min_release_year: Filter movies by minimum release year
            max_release_year: Filter movies by maximum release year
            include_frozen: Include frozen movies in results (force refresh)
            data_source: Filter by specific data source ('tmdb', 'omdb', or None for both)

        Returns:
            DataFrame of movies due for refresh
        """
        query = get_movies_due_for_refresh_query(
            limit=None, include_frozen=include_frozen, data_source=data_source
        )

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

        logger.debug(f"Found {len(movies_df)} movies due for refresh")
        return movies_df

    async def refresh_movie_data(
        self,
        movies_df: pd.DataFrame,
        fetch_tmdb: bool = True,
        fetch_omdb: bool = True,
        batch_size: int = 50,
        omdb_max_movies: int | None = None,
        allowed_statuses: list[str] | None = None,
        progress_callback: CollectionProgressCallback | None = None,
    ) -> tuple[int, int, int]:
        """Refresh data for multiple movies based on their refresh needs.

        Args:
            movies_df: DataFrame of movies to refresh
            fetch_tmdb: Whether to fetch TMDB data
            fetch_omdb: Whether to fetch OMDB data
            batch_size: Batch size for database updates
            omdb_max_movies: Maximum movies to fetch from OMDB (respects API limits)
            allowed_statuses: Allowed release statuses for TMDB filtering
            progress_callback: Optional callback(stage, completed, total)

        Returns:
            Tuple of (tmdb_updated, omdb_updated, movies_frozen)
        """
        from typing import cast

        from ayne.core.config import Settings
        from ayne.core.config import settings as _settings

        settings = cast(Settings, _settings)

        if movies_df.empty:
            logger.info("No movies to refresh")
            return 0, 0, 0

        total = len(movies_df)
        logger.debug(f"Starting refresh for {total} movies...")

        if progress_callback:
            progress_callback("Planning refresh", 0, total)

        tmdb_updated = 0
        omdb_updated = 0
        movies_frozen = 0

        # Use settings default if not provided
        allowed_statuses = allowed_statuses or settings.tmdb_allowed_release_statuses
        omdb_max_movies = omdb_max_movies or settings.omdb_max_movies

        # Never try to fetch more than what's actually left of today's OMDB
        # daily quota - avoids burning a request just to discover it's already gone.
        omdb_remaining_quota = get_remaining_quota(
            self.db, "omdb", settings.omdb_daily_request_limit
        )
        omdb_max_movies = min(omdb_max_movies, omdb_remaining_quota)
        if omdb_remaining_quota <= 0:
            logger.warning(
                "OMDB daily quota already exhausted for today - skipping OMDB fetch this run"
            )

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

        # Track which movies were actually fetched this cycle (per source) and
        # whether their data turned out to have meaningfully changed, so the
        # bookkeeping below reflects real per-movie facts instead of a single
        # batch-wide "something changed somewhere" flag.
        tmdb_fetched_ids: set[int] = set()
        tmdb_changed_ids: set[int] = set()
        omdb_fetched_ids: set[str] = set()
        omdb_changed_ids: set[str] = set()

        # Fetch TMDB data
        if not needs_tmdb.empty:
            logger.debug(f"Fetching TMDB data for {len(needs_tmdb)} movies...")
            tmdb_ids = needs_tmdb["tmdb_id"].dropna().astype(int).tolist()

            if tmdb_ids:
                if progress_callback:
                    progress_callback("Refreshing TMDB", None, None)

                # Snapshot existing volatile fields BEFORE overwriting, so we can
                # tell afterwards whether anything actually changed.
                before_df = self.db.query(
                    f"""
                    SELECT tmdb_id, budget, revenue, runtime, vote_count, vote_average, status
                    FROM tmdb_movies
                    WHERE tmdb_id IN ({",".join("?" * len(tmdb_ids))})
                    """,
                    tmdb_ids,
                )
                before_by_id = {
                    int(row["tmdb_id"]): row.to_dict() for _, row in before_df.iterrows()
                }

                tmdb_data = await self.tmdb_client.get_batch_movie_details(
                    tmdb_ids,
                    allowed_statuses=allowed_statuses,
                    progress_callback=(
                        lambda completed, batch_total: progress_callback(
                            "Refreshing TMDB", completed, batch_total
                        )
                    )
                    if progress_callback
                    else None,
                )
                record_api_usage(self.db, "tmdb", len(tmdb_ids))
                tmdb_fetched_ids.update(tmdb_ids)

                if tmdb_data:
                    df_tmdb = pd.DataFrame(tmdb_data)
                    self.db.upsert_dataframe("tmdb_movies", df_tmdb, key_columns=["tmdb_id"])

                    for _, new_row in df_tmdb.iterrows():
                        new_tmdb_id = int(new_row["tmdb_id"])
                        if has_meaningful_change(
                            cast(dict[str, Any], before_by_id.get(new_tmdb_id)),
                            cast(dict[str, Any], new_row.to_dict()),
                            TMDB_VOLATILE_FIELDS,
                        ):
                            tmdb_changed_ids.add(new_tmdb_id)

                    # Update timestamps and IMDb IDs in movies table
                    now = datetime.now(UTC).isoformat()
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

                    # Check if any movies now have both TMDB and OMDB data, set last_full_refresh
                    tmdb_id_list = [int(id) for id in df_tmdb["tmdb_id"]]
                    self.db.execute(
                        f"""
                        UPDATE movies
                        SET last_full_refresh = ?
                        WHERE tmdb_id IN ({",".join("?" * len(tmdb_id_list))})
                          AND last_tmdb_update IS NOT NULL
                          AND last_omdb_update IS NOT NULL
                          AND last_full_refresh IS NULL
                        """,
                        [now, *tmdb_id_list],
                    )
                    logger.debug("Updated last_full_refresh for movies with both updates")

                if progress_callback:
                    progress_callback("TMDB refresh complete", len(tmdb_ids), len(tmdb_ids))

        # Fetch OMDB data
        if not needs_omdb.empty and omdb_max_movies > 0:
            # Limit OMDB requests based on configuration and remaining daily quota
            omdb_batch_size = min(len(needs_omdb), omdb_max_movies)
            if omdb_batch_size < len(needs_omdb):
                logger.warning(
                    f"Limiting OMDB fetch to {omdb_batch_size} movies (max: {omdb_max_movies})"
                )
                needs_omdb = needs_omdb.head(omdb_batch_size)

            logger.debug(f"Fetching OMDB data for {len(needs_omdb)} movies...")

            # Get IMDb IDs from tmdb_movies table for these movies
            tmdb_id_list = [int(id) for id in needs_omdb["tmdb_id"].dropna()]

            if tmdb_id_list:
                imdb_query = f"""
                    SELECT DISTINCT t.imdb_id
                    FROM tmdb_movies t
                    WHERE t.tmdb_id IN ({",".join("?" * len(tmdb_id_list))})
                      AND t.imdb_id IS NOT NULL
                      AND t.imdb_id != ''
                """
                imdb_df = self.db.query(imdb_query, tmdb_id_list)
                imdb_ids = imdb_df["imdb_id"].tolist()

                if imdb_ids:
                    if progress_callback:
                        progress_callback("Refreshing OMDB", None, None)

                    before_df = self.db.query(
                        f"""
                        SELECT imdb_id, imdb_rating, imdb_votes, metascore, box_office
                        FROM omdb_movies
                        WHERE imdb_id IN ({",".join("?" * len(imdb_ids))})
                        """,
                        imdb_ids,
                    )
                    before_by_id = {
                        row["imdb_id"]: row.to_dict() for _, row in before_df.iterrows()
                    }

                    omdb_data = await self.omdb_client.get_batch_movies(
                        imdb_ids,
                        progress_callback=(
                            lambda completed, batch_total: progress_callback(
                                "Refreshing OMDB", completed, batch_total
                            )
                        )
                        if progress_callback
                        else None,
                    )
                    record_api_usage(self.db, "omdb", len(imdb_ids))
                    omdb_fetched_ids.update(imdb_ids)

                    if omdb_data:
                        df_omdb = pd.DataFrame(omdb_data)
                        self.db.upsert_dataframe("omdb_movies", df_omdb, key_columns=["imdb_id"])

                        for _, new_row in df_omdb.iterrows():
                            new_imdb_id = new_row["imdb_id"]
                            if has_meaningful_change(
                                cast(dict[str, Any], before_by_id.get(new_imdb_id)),
                                cast(dict[str, Any], new_row.to_dict()),
                                OMDB_VOLATILE_FIELDS,
                            ):
                                omdb_changed_ids.add(new_imdb_id)

                        # Update timestamps in movies table
                        now = datetime.now(UTC).isoformat()
                        for imdb_id in df_omdb["imdb_id"]:
                            self.db.execute(
                                "UPDATE movies SET last_omdb_update = ? WHERE imdb_id = ?",
                                [now, imdb_id],
                            )

                        omdb_updated = len(omdb_data)
                        logger.info(f"✅ Updated OMDB data for {omdb_updated} movies")

                        # Check if any movies now have both TMDB and OMDB data, set last_full_refresh
                        imdb_id_list = list(df_omdb["imdb_id"])
                        self.db.execute(
                            f"""
                            UPDATE movies
                            SET last_full_refresh = ?
                            WHERE imdb_id IN ({",".join("?" * len(imdb_id_list))})
                              AND last_tmdb_update IS NOT NULL
                              AND last_omdb_update IS NOT NULL
                              AND last_full_refresh IS NULL
                            """,
                            [now, *imdb_id_list],
                        )
                        logger.debug("Updated last_full_refresh for movies with both updates")

                    if progress_callback:
                        progress_callback("OMDB refresh complete", len(imdb_ids), len(imdb_ids))

        # Update per-movie "consecutive unchanged" counters and freeze stable
        # movies - but only for movies actually fetched this cycle, and based on
        # a real before/after field comparison (has_meaningful_change) rather
        # than a single batch-wide flag. Reads current counters in one query and
        # writes the result in one set-based UPDATE, instead of 2N round trips.
        fetched_movies = movies_df[
            movies_df["tmdb_id"].isin(tmdb_fetched_ids)
            | movies_df["imdb_id"].isin(omdb_fetched_ids)
        ]

        if not fetched_movies.empty:
            movie_ids = [int(m) for m in fetched_movies["movie_id"]]
            current_state = self.db.query(
                f"""
                SELECT movie_id, release_date, last_tmdb_update, last_omdb_update,
                       consecutive_unchanged_refreshes
                FROM movies
                WHERE movie_id IN ({",".join("?" * len(movie_ids))})
                """,
                movie_ids,
            )
            current_by_id = {int(row["movie_id"]): row for _, row in current_state.iterrows()}

            bookkeeping_rows = []
            for _, movie in fetched_movies.iterrows():
                movie_id = int(movie["movie_id"])
                current = current_by_id.get(movie_id)
                if current is None:
                    continue

                tmdb_id = movie["tmdb_id"]
                imdb_id = movie["imdb_id"]
                changed_by_tmdb = pd.notna(tmdb_id) and int(tmdb_id) in tmdb_changed_ids
                changed_by_omdb = pd.notna(imdb_id) and imdb_id in omdb_changed_ids
                data_changed = changed_by_tmdb or changed_by_omdb

                new_consecutive = (
                    0 if data_changed else int(current["consecutive_unchanged_refreshes"]) + 1
                )

                release_date = _to_utc_datetime(current["release_date"])
                last_tmdb = _to_utc_datetime(current["last_tmdb_update"])
                last_omdb = _to_utc_datetime(current["last_omdb_update"])

                should_freeze = (
                    should_freeze_movie(release_date, last_tmdb, last_omdb, new_consecutive)
                    if release_date is not None
                    else False
                )

                bookkeeping_rows.append(
                    {
                        "movie_id": movie_id,
                        "consecutive_unchanged_refreshes": new_consecutive,
                        "newly_frozen": should_freeze,
                    }
                )

            if bookkeeping_rows:
                bookkeeping_df = pd.DataFrame(bookkeeping_rows)
                self.db._conn.register("__refresh_bookkeeping", bookkeeping_df)
                try:
                    self.db.execute(
                        """
                        UPDATE movies
                        SET consecutive_unchanged_refreshes = b.consecutive_unchanged_refreshes,
                            data_frozen = movies.data_frozen OR b.newly_frozen
                        FROM __refresh_bookkeeping b
                        WHERE movies.movie_id = b.movie_id
                        """
                    )
                finally:
                    from contextlib import suppress

                    with suppress(Exception):
                        self.db._conn.unregister("__refresh_bookkeeping")

                movies_frozen = int(bookkeeping_df["newly_frozen"].sum())
                if movies_frozen > 0:
                    logger.info(f"🔒 Froze {movies_frozen} stable movies")

        return tmdb_updated, omdb_updated, movies_frozen

    async def run_full_collection(
        self,
        discover_movies: bool = False,
        max_discover_movies: int | None = None,
        max_discover_pages: int | None = None,
        refresh_limit: int | None = 100,
        min_popularity: float | None = None,
        min_vote_count: int | None = None,
        min_release_year: int | None = None,
        allowed_statuses: list[str] | None = None,
        omdb_max_movies: int | None = None,
        include_frozen: bool = False,
        progress_callback: CollectionProgressCallback | None = None,
    ) -> dict[str, int]:
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
            include_frozen: Include frozen movies in refresh (force refresh)
            progress_callback: Optional callback(stage, completed, total)

        Returns:
            Dict with collection statistics
        """
        stats = {"discovered": 0, "tmdb_updated": 0, "omdb_updated": 0, "frozen": 0}

        # Step 1: Discover new movies (if requested)
        if discover_movies:
            if progress_callback:
                progress_callback("Discovering new movies", None, None)
            stats["discovered"] = await self.discover_and_store_movies(
                max_movies=max_discover_movies,
                min_popularity=min_popularity,
                min_vote_count=min_vote_count,
                min_release_year=min_release_year,
                allowed_statuses=allowed_statuses,
                max_pages=max_discover_pages,
                progress_callback=progress_callback,
            )

        # Step 2: Refresh existing movies
        if progress_callback:
            progress_callback("Finding movies due for refresh", None, None)
        movies_to_refresh = self.get_movies_for_refresh(
            limit=refresh_limit, include_frozen=include_frozen
        )

        if not movies_to_refresh.empty:
            tmdb_updated, omdb_updated, frozen = await self.refresh_movie_data(
                movies_to_refresh,
                fetch_tmdb=True,
                fetch_omdb=True,
                omdb_max_movies=omdb_max_movies,
                allowed_statuses=allowed_statuses,
                progress_callback=progress_callback,
            )
            stats["tmdb_updated"] = tmdb_updated
            stats["omdb_updated"] = omdb_updated
            stats["frozen"] = frozen

        return stats

    async def enrich_tmdb_details(
        self,
        limit: int | None = None,
        min_release_year: int | None = None,
        max_release_year: int | None = None,
        allowed_statuses: list[str] | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> int:
        """Fetch detailed TMDB data for movies that only have basic discovery info.

        Args:
            limit: Maximum number of movies to enrich
            min_release_year: Filter movies by minimum release year
            max_release_year: Filter movies by maximum release year
            allowed_statuses: Allowed release statuses (defaults to settings)
            progress_callback: Optional callback(completed: int, total: int) for progress updates

        Returns:
            Number of movies enriched with TMDB details
        """
        from typing import cast

        from ayne.core.config import Settings
        from ayne.core.config import settings as _settings

        settings = cast(Settings, _settings)

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

        logger.debug(f"Enriching {len(movies_to_enrich)} movies with TMDB details...")

        tmdb_ids = movies_to_enrich["tmdb_id"].dropna().astype(int).tolist()

        if not tmdb_ids:
            return 0

        # Fetch detailed data
        tmdb_data = await self.tmdb_client.get_batch_movie_details(
            tmdb_ids, allowed_statuses=allowed_statuses, progress_callback=progress_callback
        )
        record_api_usage(self.db, "tmdb", len(tmdb_ids))

        if not tmdb_data:
            logger.warning("No TMDB data fetched")
            return 0

        # Store in database
        df_tmdb = pd.DataFrame(tmdb_data)
        self.db.upsert_dataframe("tmdb_movies", df_tmdb, key_columns=["tmdb_id"])

        # Update timestamps and IMDb IDs in movies table
        now = datetime.now(UTC).isoformat()
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

        # Check if any movies now have both TMDB and OMDB data, set last_full_refresh
        tmdb_ids_str = ",".join(str(int(id)) for id in df_tmdb["tmdb_id"])
        self.db.execute(
            f"""
            UPDATE movies
            SET last_full_refresh = ?
            WHERE tmdb_id IN ({tmdb_ids_str})
              AND last_tmdb_update IS NOT NULL
              AND last_omdb_update IS NOT NULL
              AND last_full_refresh IS NULL
            """,
            [now],
        )

        logger.info(f"✅ Enriched {len(tmdb_data)} movies with TMDB details")
        return len(tmdb_data)

    async def enrich_omdb_data(
        self,
        limit: int | None = None,
        min_release_year: int | None = None,
        max_release_year: int | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> int:
        """Fetch OMDB data for movies that have IMDb IDs but no OMDB data yet.

        Args:
            limit: Maximum number of movies to enrich
            min_release_year: Filter movies by minimum release year
            max_release_year: Filter movies by maximum release year
            progress_callback: Optional callback(current, total) for progress updates

        Returns:
            Number of movies enriched with OMDB data
        """
        from typing import cast

        from ayne.core.config import Settings
        from ayne.core.config import settings as _settings

        settings = cast(Settings, _settings)

        # Never try to fetch more than what's actually left of today's OMDB
        # daily quota - avoids burning a request just to discover it's already gone.
        omdb_remaining_quota = get_remaining_quota(
            self.db, "omdb", settings.omdb_daily_request_limit
        )
        if omdb_remaining_quota <= 0:
            logger.warning(
                "OMDB daily quota already exhausted for today - skipping OMDB enrichment"
            )
            return 0
        if limit is None or limit > omdb_remaining_quota:
            limit = omdb_remaining_quota

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

        logger.debug(f"Enriching {len(movies_to_enrich)} movies with OMDB data...")

        imdb_ids = movies_to_enrich["imdb_id"].dropna().tolist()

        if not imdb_ids:
            return 0

        try:
            # Fetch OMDB data
            omdb_data = await self.omdb_client.get_batch_movies(
                imdb_ids, progress_callback=progress_callback
            )
            record_api_usage(self.db, "omdb", len(imdb_ids))

            if not omdb_data:
                logger.warning("No OMDB data fetched")
                return 0

            # Store in database
            df_omdb = pd.DataFrame(omdb_data)
            self.db.upsert_dataframe("omdb_movies", df_omdb, key_columns=["imdb_id"])

            # Update timestamps in movies table
            now = datetime.now(UTC).isoformat()
            for imdb_id in df_omdb["imdb_id"]:
                self.db.execute(
                    "UPDATE movies SET last_omdb_update = ? WHERE imdb_id = ?",
                    [now, imdb_id],
                )

            # Check if any movies now have both TMDB and OMDB data, set last_full_refresh
            imdb_ids_str = ",".join(f"'{id}'" for id in df_omdb["imdb_id"])
            self.db.execute(
                f"""
                UPDATE movies
                SET last_full_refresh = ?
                WHERE imdb_id IN ({imdb_ids_str})
                  AND last_tmdb_update IS NOT NULL
                  AND last_omdb_update IS NOT NULL
                  AND last_full_refresh IS NULL
                """,
                [now],
            )

            logger.info(f"✅ Enriched {len(omdb_data)} movies with OMDB data")
            return len(omdb_data)

        except UserCancelledError as e:
            # User cancelled operation - save partial data
            if e.items_processed > 0 and e.partial_data:
                logger.info(
                    f"💾 Saving {len(e.partial_data)} movies fetched before cancellation..."
                )

                # Save the partial results
                df_omdb = pd.DataFrame(e.partial_data)
                self.db.upsert_dataframe("omdb_movies", df_omdb, key_columns=["imdb_id"])

                # Update timestamps in movies table
                now = datetime.now(UTC).isoformat()
                for imdb_id in df_omdb["imdb_id"]:
                    self.db.execute(
                        "UPDATE movies SET last_omdb_update = ? WHERE imdb_id = ?",
                        [now, imdb_id],
                    )

                # Check if any movies now have both TMDB and OMDB data, set last_full_refresh
                imdb_ids_str = ",".join(f"'{id}'" for id in df_omdb["imdb_id"])
                self.db.execute(
                    f"""
                    UPDATE movies
                    SET last_full_refresh = ?
                    WHERE imdb_id IN ({imdb_ids_str})
                      AND last_tmdb_update IS NOT NULL
                      AND last_omdb_update IS NOT NULL
                      AND last_full_refresh IS NULL
                    """,
                    [now],
                )
                logger.debug("Updated last_full_refresh for movies with both updates")
            raise
        except asyncio.CancelledError:
            # Task was cancelled (Ctrl+C) - save partial data if available
            # Note: partial_data comes from UserCancelledError in the client
            logger.info("Operation cancelled by user")
            raise
        except APIRateLimitError as e:
            # OMDB daily quota exceeded - save what we got and re-raise
            if e.items_processed > 0 and e.partial_data:
                logger.info(f"💾 Saving {len(e.partial_data)} movies fetched before quota limit...")

                # Save the partial results
                df_omdb = pd.DataFrame(e.partial_data)
                self.db.upsert_dataframe("omdb_movies", df_omdb, key_columns=["imdb_id"])

                # Update timestamps in movies table
                now = datetime.now(UTC).isoformat()
                for imdb_id in df_omdb["imdb_id"]:
                    self.db.execute(
                        "UPDATE movies SET last_omdb_update = ? WHERE imdb_id = ?",
                        [now, imdb_id],
                    )

                # Check if any movies now have both TMDB and OMDB data, set last_full_refresh
                imdb_ids_str = ",".join(f"'{id}'" for id in df_omdb["imdb_id"])
                self.db.execute(
                    f"""
                    UPDATE movies
                    SET last_full_refresh = ?
                    WHERE imdb_id IN ({imdb_ids_str})
                      AND last_tmdb_update IS NOT NULL
                      AND last_omdb_update IS NOT NULL
                      AND last_full_refresh IS NULL
                    """,
                    [now],
                )

                logger.info(f"✅ Saved {len(e.partial_data)} movies before quota limit")

            raise  # Re-raise to be caught by CLI

    async def enrich_numbers_data(
        self,
        limit: int | None = None,
        min_release_year: int | None = None,
        max_release_year: int | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> int:
        """Fetch The Numbers box office/budget data for movies that don't have it yet.

        Args:
            limit: Maximum number of movies to enrich (defaults to settings.numbers_max_movies)
            min_release_year: Filter movies by minimum release year
            max_release_year: Filter movies by maximum release year
            progress_callback: Optional callback(current, total) for progress updates

        Returns:
            Number of movies enriched with The Numbers data
        """
        from typing import cast

        from ayne.core.config import Settings
        from ayne.core.config import settings as _settings

        settings = cast(Settings, _settings)

        limit = limit or settings.numbers_max_movies

        # Query movies that don't have a numbers_movies row yet. A real release
        # date is required since it's used both for filtering and as the
        # release-year hint passed to TheNumbersClient.
        query = """
            SELECT m.movie_id, m.title, m.release_date
            FROM movies m
            LEFT JOIN numbers_movies n ON m.movie_id = n.movie_id
            WHERE n.movie_id IS NULL
              AND m.release_date IS NOT NULL
        """

        if min_release_year:
            query += f" AND m.release_date >= '{min_release_year}-01-01'"
        if max_release_year:
            query += f" AND m.release_date <= '{max_release_year}-12-31'"

        query += " ORDER BY m.release_date DESC"

        if limit:
            query += f" LIMIT {int(limit)}"

        movies_to_enrich = self.db.query(query)

        if movies_to_enrich.empty:
            logger.info("No movies need The Numbers enrichment")
            return 0

        logger.debug(f"Enriching {len(movies_to_enrich)} movies with The Numbers data...")

        movie_inputs = [
            {
                "movie_id": int(row["movie_id"]),
                "title": row["title"],
                "release_year": pd.to_datetime(row["release_date"]).year,
            }
            for _, row in movies_to_enrich.iterrows()
        ]

        numbers_data = await self.numbers_client.get_batch_financial_data(
            movie_inputs, progress_callback=progress_callback
        )
        record_api_usage(self.db, "numbers", len(movie_inputs) * 4)
        if not numbers_data:
            logger.warning("No The Numbers data found for any of these movies")
            return 0

        df_numbers = pd.DataFrame(numbers_data)
        self.db.upsert_dataframe("numbers_movies", df_numbers, key_columns=["movie_id"])

        now = datetime.now(UTC).isoformat()
        movie_ids = [int(id) for id in df_numbers["movie_id"]]
        self.db.execute(
            f"""
            UPDATE movies SET last_numbers_update = ?
            WHERE movie_id IN ({",".join("?" * len(movie_ids))})
            """,
            [now, *movie_ids],
        )

        logger.info(f"✅ Enriched {len(numbers_data)} movies with The Numbers data")
        return len(numbers_data)

    async def close(self):
        """Cleanup resources."""
        await self.tmdb_client.close()
        await self.omdb_client.close()
        await self.numbers_client.close()
        logger.debug("Orchestrator closed")

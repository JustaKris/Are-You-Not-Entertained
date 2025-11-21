"""Refresh strategy module for intelligent data collection.

Determines when to refresh movie data based on:
- Movie age (days since release)
- Last update timestamps
- Data frozen status
"""

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, Optional

from src.core.logging import get_logger

logger = get_logger(__name__)


class MovieAge(Enum):
    """Movie age categories for refresh strategies."""

    RECENT = "recent"  # 0-60 days
    ESTABLISHED = "established"  # 60-180 days
    MATURE = "mature"  # 180-365 days
    ARCHIVED = "archived"  # > 365 days


class RefreshThresholds:
    """Refresh interval thresholds based on movie age."""

    # TMDB refresh intervals (days)
    TMDB_RECENT = 5  # 0-60 days: refresh every 5 days
    TMDB_ESTABLISHED = 15  # 60-180 days: refresh every 15 days
    TMDB_MATURE = 30  # 180-365 days: refresh every 30 days
    TMDB_ARCHIVED = 90  # > 365 days: refresh every 90 days

    # OMDB refresh intervals (days)
    OMDB_RECENT = 5  # 0-60 days: refresh every 5 days
    OMDB_ESTABLISHED = 30  # 60-180 days: refresh every 30 days
    OMDB_MATURE = 90  # 180-365 days: refresh every 90 days
    OMDB_ARCHIVED = 180  # > 365 days: refresh every 180 days

    # Box office (The Numbers) refresh intervals (days)
    NUMBERS_RECENT = 5  # 0-60 days: refresh every 5 days
    NUMBERS_ESTABLISHED = 30  # 60-180 days: refresh every 30 days
    NUMBERS_MATURE = 90  # 180-365 days: refresh every 90 days
    NUMBERS_ARCHIVED = 180  # > 365 days: refresh every 180 days

    # Movie age boundaries (days)
    AGE_RECENT = 60
    AGE_ESTABLISHED = 180
    AGE_MATURE = 365

    # Freeze criteria
    FREEZE_MIN_AGE_DAYS = 365  # Must be at least 1 year old
    FREEZE_STABLE_CYCLES = 3  # No changes for 3 refresh cycles


def get_movie_age(release_date: datetime) -> MovieAge:
    """Determine movie age category based on release date.

    Args:
        release_date: Movie release date

    Returns:
        MovieAge enum
    """
    days_since_release = (datetime.now(timezone.utc) - release_date).days

    if days_since_release <= RefreshThresholds.AGE_RECENT:
        return MovieAge.RECENT
    elif days_since_release <= RefreshThresholds.AGE_ESTABLISHED:
        return MovieAge.ESTABLISHED
    elif days_since_release <= RefreshThresholds.AGE_MATURE:
        return MovieAge.MATURE
    else:
        return MovieAge.ARCHIVED


def get_tmdb_refresh_interval(release_date: datetime) -> int:
    """Get TMDB refresh interval in days based on movie age.

    Args:
        release_date: Movie release date

    Returns:
        Number of days before next refresh
    """
    age = get_movie_age(release_date)

    intervals = {
        MovieAge.RECENT: RefreshThresholds.TMDB_RECENT,
        MovieAge.ESTABLISHED: RefreshThresholds.TMDB_ESTABLISHED,
        MovieAge.MATURE: RefreshThresholds.TMDB_MATURE,
        MovieAge.ARCHIVED: RefreshThresholds.TMDB_ARCHIVED,
    }

    return intervals[age]


def get_omdb_refresh_interval(release_date: datetime) -> int:
    """Get OMDB refresh interval in days based on movie age.

    Args:
        release_date: Movie release date

    Returns:
        Number of days before next refresh
    """
    age = get_movie_age(release_date)

    intervals = {
        MovieAge.RECENT: RefreshThresholds.OMDB_RECENT,
        MovieAge.ESTABLISHED: RefreshThresholds.OMDB_ESTABLISHED,
        MovieAge.MATURE: RefreshThresholds.OMDB_MATURE,
        MovieAge.ARCHIVED: RefreshThresholds.OMDB_ARCHIVED,
    }

    return intervals[age]


def get_numbers_refresh_interval(release_date: datetime) -> int:
    """Get box office (The Numbers) refresh interval in days based on movie age.

    Args:
        release_date: Movie release date

    Returns:
        Number of days before next refresh
    """
    age = get_movie_age(release_date)

    intervals = {
        MovieAge.RECENT: RefreshThresholds.NUMBERS_RECENT,
        MovieAge.ESTABLISHED: RefreshThresholds.NUMBERS_ESTABLISHED,
        MovieAge.MATURE: RefreshThresholds.NUMBERS_MATURE,
        MovieAge.ARCHIVED: RefreshThresholds.NUMBERS_ARCHIVED,
    }

    return intervals[age]


def needs_tmdb_refresh(release_date: datetime, last_tmdb_update: Optional[datetime]) -> bool:
    """Check if TMDB data needs refresh.

    Args:
        release_date: Movie release date
        last_tmdb_update: Last TMDB update timestamp (None if never updated)

    Returns:
        True if refresh needed
    """
    if last_tmdb_update is None:
        return True

    # Ensure timezone awareness
    if last_tmdb_update.tzinfo is None:
        last_tmdb_update = last_tmdb_update.replace(tzinfo=timezone.utc)

    interval_days = get_tmdb_refresh_interval(release_date)
    threshold = datetime.now(timezone.utc) - timedelta(days=interval_days)

    return last_tmdb_update < threshold


def needs_omdb_refresh(release_date: datetime, last_omdb_update: Optional[datetime]) -> bool:
    """Check if OMDB data needs refresh.

    Args:
        release_date: Movie release date
        last_omdb_update: Last OMDB update timestamp (None if never updated)

    Returns:
        True if refresh needed
    """
    if last_omdb_update is None:
        return True

    # Ensure timezone awareness
    if last_omdb_update.tzinfo is None:
        last_omdb_update = last_omdb_update.replace(tzinfo=timezone.utc)

    interval_days = get_omdb_refresh_interval(release_date)
    threshold = datetime.now(timezone.utc) - timedelta(days=interval_days)

    return last_omdb_update < threshold


def needs_numbers_refresh(release_date: datetime, last_numbers_update: Optional[datetime]) -> bool:
    """Check if box office data needs refresh.

    Args:
        release_date: Movie release date
        last_numbers_update: Last box office update timestamp (None if never updated)

    Returns:
        True if refresh needed
    """
    if last_numbers_update is None:
        return True

    interval_days = get_numbers_refresh_interval(release_date)
    threshold = datetime.now(timezone.utc) - timedelta(days=interval_days)

    return last_numbers_update < threshold


def should_freeze_movie(
    release_date: datetime,
    last_tmdb_update: Optional[datetime],
    last_omdb_update: Optional[datetime],
    consecutive_unchanged_cycles: int = 0,
) -> bool:
    """Determine if a movie should be frozen (no more automatic refreshes).

    Criteria:
    - Must be at least FREEZE_MIN_AGE_DAYS old
    - Must have stable data (no changes for FREEZE_STABLE_CYCLES)

    Args:
        release_date: Movie release date
        last_tmdb_update: Last TMDB update timestamp
        last_omdb_update: Last OMDB update timestamp
        consecutive_unchanged_cycles: Number of refresh cycles without data changes

    Returns:
        True if movie should be frozen
    """
    days_since_release = (datetime.now(timezone.utc) - release_date).days

    # Must be old enough
    if days_since_release < RefreshThresholds.FREEZE_MIN_AGE_DAYS:
        return False

    # Must have been updated at least once
    if last_tmdb_update is None and last_omdb_update is None:
        return False

    # Must be stable
    if consecutive_unchanged_cycles >= RefreshThresholds.FREEZE_STABLE_CYCLES:
        logger.info(f"Movie is stable and mature, freezing (age: {days_since_release} days)")
        return True

    return False


def get_movies_due_for_refresh_query(
    limit: Optional[int] = None, include_frozen: bool = False
) -> str:
    """Generate SQL query to fetch movies due for refresh.

    Args:
        limit: Maximum number of movies to return
        include_frozen: Include frozen movies (default: False)

    Returns:
        SQL query string
    """
    frozen_filter = "" if include_frozen else "AND m.data_frozen = FALSE"
    limit_clause = f"LIMIT {limit}" if limit else ""

    query = f"""
    SELECT
        m.movie_id,
        m.tmdb_id,
        m.imdb_id,
        m.title,
        m.release_date,
        m.last_full_refresh,
        m.last_tmdb_update,
        m.last_omdb_update,
        m.last_numbers_update,
        m.data_frozen,
        DATEDIFF('day', m.release_date, CURRENT_DATE) as days_since_release
    FROM movies m
    WHERE 1=1
        {frozen_filter}
        AND (
            -- Never refreshed
            m.last_full_refresh IS NULL

            -- Recent movies (0-60 days): refresh every 5 days
            OR (
                DATEDIFF('day', m.release_date, CURRENT_DATE) <= 60
                AND (
                    m.last_tmdb_update IS NULL
                    OR DATEDIFF('day', m.last_tmdb_update, CURRENT_TIMESTAMP) >= 5
                    OR m.last_omdb_update IS NULL
                    OR DATEDIFF('day', m.last_omdb_update, CURRENT_TIMESTAMP) >= 5
                )
            )

            -- Established movies (60-180 days): refresh every 15-30 days
            OR (
                DATEDIFF('day', m.release_date, CURRENT_DATE) > 60
                AND DATEDIFF('day', m.release_date, CURRENT_DATE) <= 180
                AND (
                    m.last_tmdb_update IS NULL
                    OR DATEDIFF('day', m.last_tmdb_update, CURRENT_TIMESTAMP) >= 15
                    OR m.last_omdb_update IS NULL
                    OR DATEDIFF('day', m.last_omdb_update, CURRENT_TIMESTAMP) >= 30
                )
            )

            -- Mature movies (180-365 days): refresh every 30-90 days
            OR (
                DATEDIFF('day', m.release_date, CURRENT_DATE) > 180
                AND DATEDIFF('day', m.release_date, CURRENT_DATE) <= 365
                AND (
                    m.last_tmdb_update IS NULL
                    OR DATEDIFF('day', m.last_tmdb_update, CURRENT_TIMESTAMP) >= 30
                    OR m.last_omdb_update IS NULL
                    OR DATEDIFF('day', m.last_omdb_update, CURRENT_TIMESTAMP) >= 90
                )
            )

            -- Archived movies (>365 days): refresh every 90-180 days
            OR (
                DATEDIFF('day', m.release_date, CURRENT_DATE) > 365
                AND (
                    m.last_tmdb_update IS NULL
                    OR DATEDIFF('day', m.last_tmdb_update, CURRENT_TIMESTAMP) >= 90
                    OR m.last_omdb_update IS NULL
                    OR DATEDIFF('day', m.last_omdb_update, CURRENT_TIMESTAMP) >= 180
                )
            )
        )
    ORDER BY
        -- Prioritize never-refreshed movies
        CASE WHEN m.last_full_refresh IS NULL THEN 0 ELSE 1 END,
        -- Then by release date (newest first)
        m.release_date DESC
    {limit_clause}
    """

    return query


def calculate_refresh_plan(movie: Dict[str, Any]) -> Dict[str, bool]:
    """Calculate what data sources need refreshing for a movie.

    Args:
        movie: Movie record with release_date and last_*_update fields

    Returns:
        Dict with keys: needs_tmdb, needs_omdb, needs_numbers
    """
    release_date = movie.get("release_date")
    if not release_date:
        return {"needs_tmdb": False, "needs_omdb": False, "needs_numbers": False}

    if isinstance(release_date, str):
        release_date = datetime.fromisoformat(release_date.replace("Z", "+00:00"))

    # Ensure timezone awareness
    if release_date and release_date.tzinfo is None:
        release_date = release_date.replace(tzinfo=timezone.utc)

    last_tmdb = movie.get("last_tmdb_update")
    last_omdb = movie.get("last_omdb_update")
    last_numbers = movie.get("last_numbers_update")

    # Handle pandas NaT and NaN
    import pandas as pd

    if pd.isna(last_tmdb):
        last_tmdb = None
    elif isinstance(last_tmdb, str):
        last_tmdb = datetime.fromisoformat(last_tmdb.replace("Z", "+00:00"))
    elif last_tmdb and last_tmdb.tzinfo is None:
        last_tmdb = last_tmdb.replace(tzinfo=timezone.utc)

    if pd.isna(last_omdb):
        last_omdb = None
    elif isinstance(last_omdb, str):
        last_omdb = datetime.fromisoformat(last_omdb.replace("Z", "+00:00"))
    elif last_omdb and last_omdb.tzinfo is None:
        last_omdb = last_omdb.replace(tzinfo=timezone.utc)

    if pd.isna(last_numbers):
        last_numbers = None
    elif isinstance(last_numbers, str):
        last_numbers = datetime.fromisoformat(last_numbers.replace("Z", "+00:00"))
    elif last_numbers and last_numbers.tzinfo is None:
        last_numbers = last_numbers.replace(tzinfo=timezone.utc)

    return {
        "needs_tmdb": needs_tmdb_refresh(release_date, last_tmdb),
        "needs_omdb": needs_omdb_refresh(release_date, last_omdb),
        "needs_numbers": needs_numbers_refresh(release_date, last_numbers),
    }

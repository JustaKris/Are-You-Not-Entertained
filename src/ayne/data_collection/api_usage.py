"""Persistent, cross-run daily API usage tracking.

Both TMDB and (especially) OMDB enforce daily/rate quotas. Previously the only
"quota awareness" in this codebase was an in-memory flag scoped to a single
process run, so running the CLI more than once a day had no idea how much
quota was already spent. This module adds a tiny durable ledger table so
usage survives across runs and can be queried before starting a new batch.
"""

from datetime import date

import pandas as pd

from ayne.core.exceptions import DatabaseError
from ayne.core.logging import get_logger
from ayne.database.duckdb_client import DuckDBClient

logger = get_logger(__name__)

_USAGE_TABLE = "api_usage_daily"


def ensure_usage_table(db: DuckDBClient) -> None:
    """Verify the migrated API usage ledger is available."""
    if not db.table_exists(_USAGE_TABLE):
        raise DatabaseError("Database schema is not initialized; run `uv run ayne db init` first")


def record_api_usage(db: DuckDBClient, provider: str, count: int, on: date | None = None) -> None:
    """Record `count` additional requests made against `provider` for a given day.

    Args:
        db: DuckDB client
        provider: Provider name, e.g. "omdb" or "tmdb"
        count: Number of requests to add (no-op if <= 0)
        on: Date the usage occurred on (defaults to today, UTC-naive local date)
    """
    if count <= 0:
        return

    ensure_usage_table(db)
    usage_date = on or date.today()

    db.execute(
        f"""
        INSERT INTO {_USAGE_TABLE} (provider, usage_date, requests_used)
        VALUES (?, ?, ?)
        ON CONFLICT (provider, usage_date)
        DO UPDATE SET requests_used = {_USAGE_TABLE}.requests_used + excluded.requests_used
        """,
        [provider, usage_date, count],
    )
    logger.debug(f"Recorded {count} {provider} request(s) for {usage_date}")


def get_usage_today(db: DuckDBClient, provider: str) -> int:
    """Return how many requests have been recorded for `provider` today."""
    ensure_usage_table(db)
    result = db.query(
        f"SELECT requests_used FROM {_USAGE_TABLE} WHERE provider = ? AND usage_date = ?",
        [provider, date.today()],
    )
    if result.empty:
        return 0
    return int(result["requests_used"].iloc[0])


def get_remaining_quota(db: DuckDBClient, provider: str, daily_limit: int) -> int:
    """Return how many requests are left today for `provider` given `daily_limit`."""
    used = get_usage_today(db, provider)
    return max(daily_limit - used, 0)


def get_usage_history(
    db: DuckDBClient, provider: str | None = None, days: int = 14
) -> pd.DataFrame:
    """Return recent daily usage history, optionally filtered to one provider."""
    ensure_usage_table(db)
    if provider:
        return db.query(
            f"""
            SELECT provider, usage_date, requests_used
            FROM {_USAGE_TABLE}
            WHERE provider = ? AND usage_date >= CURRENT_DATE - INTERVAL '{int(days)} days'
            ORDER BY usage_date DESC
            """,
            [provider],
        )
    return db.query(
        f"""
        SELECT provider, usage_date, requests_used
        FROM {_USAGE_TABLE}
        WHERE usage_date >= CURRENT_DATE - INTERVAL '{int(days)} days'
        ORDER BY usage_date DESC, provider
        """
    )

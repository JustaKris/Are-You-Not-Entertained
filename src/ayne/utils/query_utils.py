"""Query utilities for data analysis and notebooks.

This module provides convenient functions for querying the DuckDB database
and loading data into pandas DataFrames for analysis in Jupyter notebooks.

Modern best practices:
- Type hints for clarity
- Context managers for resource management
- Logging for debugging
- Clean separation of concerns
"""

from typing import Any, Dict, List, Optional

import pandas as pd

from ayne.core.logging import get_logger
from ayne.database.duckdb_client import DuckDBClient

logger = get_logger(__name__)


def get_db_client(read_only: bool = True) -> DuckDBClient:
    """Get a DuckDB client instance.

    Args:
        read_only: Whether to open database in read-only mode (default True for analysis)

    Returns:
        DuckDBClient instance

    Example:
        >>> db = get_db_client()
        >>> df = db.query("SELECT * FROM movies LIMIT 10")
        >>> db.close()
    """
    return DuckDBClient(read_only=read_only)


def query_movies(
    filters: Optional[Dict[str, Any]] = None,
    columns: Optional[List[str]] = None,
    limit: Optional[int] = None,
    order_by: Optional[str] = None,
) -> pd.DataFrame:
    """Query movies table with convenient filtering.

    Args:
        filters: Dictionary of column:value pairs for filtering
        columns: List of columns to select (None = all columns)
        limit: Maximum number of rows to return
        order_by: Column name to order by (e.g., "release_date DESC")

    Returns:
        DataFrame with query results

    Example:
        >>> # Get recent movies with budget info
        >>> df = query_movies(
        ...     filters={"release_year": 2024},
        ...     columns=["title", "budget", "revenue"],
        ...     order_by="revenue DESC",
        ...     limit=100
        ... )
    """
    # Build SELECT clause
    select_cols = ", ".join(columns) if columns else "*"

    # Build WHERE clause
    where_clause = ""
    if filters:
        conditions = [f"{col} = {repr(val)}" for col, val in filters.items()]
        where_clause = "WHERE " + " AND ".join(conditions)

    # Build ORDER BY clause
    order_clause = f"ORDER BY {order_by}" if order_by else ""

    # Build LIMIT clause
    limit_clause = f"LIMIT {limit}" if limit else ""

    # Construct full query
    query = f"""
        SELECT {select_cols}
        FROM movies
        {where_clause}
        {order_clause}
        {limit_clause}
    """

    db = get_db_client(read_only=True)
    try:
        df = db.query(query)
        logger.info(f"Queried movies table: {len(df)} rows returned")
        return df
    finally:
        db.close()


def load_full_dataset(include_nulls: bool = True) -> pd.DataFrame:
    """Load the complete movies dataset for analysis.

    This joins all relevant tables (movies, tmdb_movies, omdb_movies, numbers_movies)
    to provide a comprehensive view of all available data.

    Args:
        include_nulls: Whether to include movies with missing data

    Returns:
        DataFrame with complete movie data

    Example:
        >>> df = load_full_dataset()
        >>> print(f"Loaded {len(df)} movies")
        >>> df.info()
    """
    query = """
        SELECT
            m.*,
            t.title as tmdb_title,
            t.overview,
            t.popularity,
            t.vote_average as tmdb_vote_average,
            t.vote_count as tmdb_vote_count,
            t.budget as tmdb_budget,
            t.revenue as tmdb_revenue,
            t.runtime as tmdb_runtime,
            t.status,
            t.genres as genre_names,
            t.production_companies as production_company_name,
            t.production_countries as production_country_name,
            t.spoken_languages,
            o.rated,
            o.released,
            o.runtime as omdb_runtime,
            o.genre as omdb_genre,
            o.director,
            o.writer,
            o.actors,
            o.language,
            o.country,
            o.awards,
            o.metascore,
            o.imdb_rating,
            o.imdb_votes,
            o.box_office,
            o.rotten_tomatoes_rating,
            o.meta_critic_rating,
            n.production_budget,
            n.domestic_box_office as domestic_gross,
            n.worldwide_box_office as worldwide_gross
        FROM movies m
        LEFT JOIN tmdb_movies t ON m.tmdb_id = t.tmdb_id
        LEFT JOIN omdb_movies o ON m.imdb_id = o.imdb_id
        LEFT JOIN numbers_movies n ON m.movie_id = n.movie_id
    """

    if not include_nulls:
        query += """
        WHERE m.budget IS NOT NULL
          AND m.revenue IS NOT NULL
        """

    db = get_db_client(read_only=True)
    try:
        df = db.query(query)
        logger.info(f"Loaded full dataset: {len(df)} movies with {len(df.columns)} columns")
        return df
    finally:
        db.close()


def get_movies_with_financials(min_budget: float = 0, min_revenue: float = 0) -> pd.DataFrame:
    """Get movies with financial data for budget/revenue analysis.

    Args:
        min_budget: Minimum budget threshold
        min_revenue: Minimum revenue threshold

    Returns:
        DataFrame with movies having financial data

    Example:
        >>> # Get movies with substantial budgets
        >>> df = get_movies_with_financials(min_budget=10_000_000)
        >>> print(f"Found {len(df)} movies with budget >= $10M")
    """
    query = f"""
        SELECT
            m.*,
            t.title as tmdb_title,
            t.popularity,
            t.vote_average,
            t.vote_count,
            t.runtime,
            t.genres as genre_names,
            t.budget,
            t.revenue,
            o.director,
            o.writer,
            o.actors,
            o.imdb_rating,
            o.imdb_votes,
            o.metascore,
            o.rotten_tomatoes_rating
        FROM movies m
        INNER JOIN tmdb_movies t ON m.tmdb_id = t.tmdb_id
        LEFT JOIN omdb_movies o ON m.imdb_id = o.imdb_id
        WHERE t.budget >= {min_budget}
          AND t.revenue >= {min_revenue}
          AND t.budget IS NOT NULL
          AND t.revenue IS NOT NULL
        ORDER BY m.release_date DESC
    """

    db = get_db_client(read_only=True)
    try:
        df = db.query(query)
        logger.info(
            f"Loaded {len(df)} movies with financials (budget >= {min_budget}, revenue >= {min_revenue})"
        )
        return df
    finally:
        db.close()


def get_movies_by_year_range(start_year: int, end_year: Optional[int] = None) -> pd.DataFrame:
    """Get movies released in a specific year range.

    Args:
        start_year: Starting year (inclusive)
        end_year: Ending year (inclusive), defaults to start_year

    Returns:
        DataFrame with movies in the year range

    Example:
        >>> # Get all movies from 2020-2024
        >>> df = get_movies_by_year_range(2020, 2024)
    """
    end_year = end_year or start_year

    query = f"""
        SELECT *
        FROM movies
        WHERE EXTRACT(YEAR FROM release_date) BETWEEN {start_year} AND {end_year}
        ORDER BY release_date DESC
    """

    db = get_db_client(read_only=True)
    try:
        df = db.query(query)
        logger.info(f"Loaded {len(df)} movies from {start_year}-{end_year}")
        return df
    finally:
        db.close()


def get_table_info(table_name: str) -> pd.DataFrame:
    """Get schema information for a table.

    Args:
        table_name: Name of the table

    Returns:
        DataFrame with column information

    Example:
        >>> info = get_table_info("movies")
        >>> print(info[["column_name", "column_type", "null"]])
    """
    query = f"DESCRIBE {table_name}"

    db = get_db_client(read_only=True)
    try:
        df = db.query(query)
        logger.info(f"Retrieved schema info for table '{table_name}'")
        return df
    finally:
        db.close()


def execute_custom_query(query: str) -> pd.DataFrame:
    """Execute a custom SQL query.

    Args:
        query: SQL query string

    Returns:
        DataFrame with query results

    Example:
        >>> query = '''
        ...     SELECT genre_names, COUNT(*) as count
        ...     FROM movies
        ...     GROUP BY genre_names
        ...     ORDER BY count DESC
        ...     LIMIT 10
        ... '''
        >>> df = execute_custom_query(query)
    """
    db = get_db_client(read_only=True)
    try:
        df = db.query(query)
        logger.info(f"Custom query executed: {len(df)} rows returned")
        return df
    finally:
        db.close()


# ========================================================================
# Database Monitoring Functions
# ========================================================================


def get_enrichment_status_by_year() -> pd.DataFrame:
    """Get enrichment status breakdown by release year.

    Returns a DataFrame with columns:
    - release_year: Year the movies were released
    - total_movies: Total count of movies
    - with_base_ids: Movies with basic TMDB/IMDB IDs
    - enriched_tmdb: Movies with full TMDB details
    - enriched_omdb: Movies with OMDB data
    - pct_tmdb_enriched: Percentage enriched with TMDB
    - pct_omdb_enriched: Percentage enriched with OMDB

    Example:
        >>> df = get_enrichment_status_by_year()
        >>> print(df[df['release_year'] >= 2020])
    """
    query = """
        SELECT
            EXTRACT(YEAR FROM m.release_date) as release_year,
            COUNT(DISTINCT m.movie_id) as total_movies,
            COUNT(DISTINCT CASE WHEN m.tmdb_id IS NOT NULL THEN m.movie_id END) as with_base_ids,
            COUNT(DISTINCT CASE WHEN t.tmdb_id IS NOT NULL THEN m.movie_id END) as enriched_tmdb,
            COUNT(DISTINCT CASE WHEN o.imdb_id IS NOT NULL THEN m.movie_id END) as enriched_omdb,
            ROUND(100.0 * COUNT(DISTINCT CASE WHEN t.tmdb_id IS NOT NULL THEN m.movie_id END)
                / NULLIF(COUNT(DISTINCT m.movie_id), 0), 2) as pct_tmdb_enriched,
            ROUND(100.0 * COUNT(DISTINCT CASE WHEN o.imdb_id IS NOT NULL THEN m.movie_id END)
                / NULLIF(COUNT(DISTINCT m.movie_id), 0), 2) as pct_omdb_enriched
        FROM movies m
        LEFT JOIN tmdb_movies t ON m.tmdb_id = t.tmdb_id
        LEFT JOIN omdb_movies o ON m.imdb_id = o.imdb_id
        WHERE m.release_date IS NOT NULL
        GROUP BY release_year
        ORDER BY release_year DESC
    """

    db = get_db_client(read_only=True)
    try:
        df = db.query(query)
        logger.info(f"Retrieved enrichment status for {len(df)} years")
        return df
    finally:
        db.close()


def get_movies_due_for_update_by_year() -> pd.DataFrame:
    """Get count of movies due for refresh, grouped by release year.

    Returns movies where:
    - next_refresh_due is NULL (never refreshed) OR past due
    - Not frozen

    Returns:
        DataFrame with release_year and movies_due_for_update columns

    Example:
        >>> df = get_movies_due_for_update_by_year()
        >>> total_due = df['movies_due_for_update'].sum()
        >>> print(f"Total movies due: {total_due}")
    """
    query = """
        SELECT
            EXTRACT(YEAR FROM m.release_date) as release_year,
            COUNT(DISTINCT m.movie_id) as movies_due_for_update,
            COUNT(DISTINCT CASE WHEN r.next_refresh_due IS NULL THEN m.movie_id END) as never_refreshed,
            COUNT(DISTINCT CASE WHEN r.next_refresh_due < CURRENT_TIMESTAMP THEN m.movie_id END) as overdue
        FROM movies m
        LEFT JOIN movie_refresh_state r ON m.movie_id = r.movie_id
        WHERE m.release_date IS NOT NULL
          AND (r.frozen IS NULL OR r.frozen = FALSE)
          AND (r.next_refresh_due IS NULL OR r.next_refresh_due <= CURRENT_TIMESTAMP)
        GROUP BY release_year
        ORDER BY release_year DESC
    """

    db = get_db_client(read_only=True)
    try:
        df = db.query(query)
        logger.info(f"Retrieved update status for {len(df)} years")
        return df
    finally:
        db.close()


def get_database_summary_stats() -> Dict[str, Any]:
    """Get high-level database statistics.

    Returns:
        Dictionary with various database metrics

    Example:
        >>> stats = get_database_summary_stats()
        >>> print(f"Total movies: {stats['total_movies']}")
        >>> print(f"Enrichment rate: {stats['tmdb_enrichment_pct']:.1f}%")
    """
    query = """
        SELECT
            COUNT(DISTINCT m.movie_id) as total_movies,
            COUNT(DISTINCT CASE WHEN m.tmdb_id IS NOT NULL THEN m.movie_id END) as with_tmdb_id,
            COUNT(DISTINCT CASE WHEN m.imdb_id IS NOT NULL THEN m.movie_id END) as with_imdb_id,
            COUNT(DISTINCT CASE WHEN t.tmdb_id IS NOT NULL THEN m.movie_id END) as enriched_tmdb,
            COUNT(DISTINCT CASE WHEN o.imdb_id IS NOT NULL THEN m.movie_id END) as enriched_omdb,
            COUNT(DISTINCT CASE WHEN m.last_full_refresh IS NOT NULL THEN m.movie_id END) as fully_refreshed,
            COUNT(DISTINCT CASE WHEN m.data_frozen = TRUE THEN m.movie_id END) as frozen_movies,
            MIN(m.release_date) as earliest_movie,
            MAX(m.release_date) as latest_movie,
            COUNT(DISTINCT EXTRACT(YEAR FROM m.release_date)) as unique_years
        FROM movies m
        LEFT JOIN tmdb_movies t ON m.tmdb_id = t.tmdb_id
        LEFT JOIN omdb_movies o ON m.imdb_id = o.imdb_id
    """

    db = get_db_client(read_only=True)
    try:
        df = db.query(query)
        row = df.iloc[0]

        stats = {
            "total_movies": int(row["total_movies"]),
            "with_tmdb_id": int(row["with_tmdb_id"]),
            "with_imdb_id": int(row["with_imdb_id"]),
            "enriched_tmdb": int(row["enriched_tmdb"]),
            "enriched_omdb": int(row["enriched_omdb"]),
            "fully_refreshed": int(row["fully_refreshed"]),
            "frozen_movies": int(row["frozen_movies"]),
            "earliest_movie": row["earliest_movie"],
            "latest_movie": row["latest_movie"],
            "unique_years": int(row["unique_years"]),
            "tmdb_enrichment_pct": (
                100.0 * row["enriched_tmdb"] / row["total_movies"] if row["total_movies"] > 0 else 0
            ),
            "omdb_enrichment_pct": (
                100.0 * row["enriched_omdb"] / row["total_movies"] if row["total_movies"] > 0 else 0
            ),
        }

        logger.info("Retrieved database summary statistics")
        return stats
    finally:
        db.close()


def get_recent_update_activity(days: int = 7) -> pd.DataFrame:
    """Get update activity statistics for recent days.

    Args:
        days: Number of days to look back

    Returns:
        DataFrame with daily update counts

    Example:
        >>> df = get_recent_update_activity(days=14)
        >>> print(df.to_string())
    """
    query = f"""
        WITH date_range AS (
            SELECT CURRENT_DATE - CAST(i AS INTEGER) AS activity_date
            FROM generate_series(0, {days - 1}) AS t(i)
        )
        SELECT
            dr.activity_date::DATE as date,
            COUNT(DISTINCT CASE WHEN DATE(m.last_tmdb_update) = dr.activity_date THEN m.movie_id END) as tmdb_updates,
            COUNT(DISTINCT CASE WHEN DATE(m.last_omdb_update) = dr.activity_date THEN m.movie_id END) as omdb_updates,
            COUNT(DISTINCT CASE WHEN DATE(m.last_full_refresh) = dr.activity_date THEN m.movie_id END) as full_refreshes
        FROM date_range dr
        CROSS JOIN movies m
        GROUP BY dr.activity_date
        ORDER BY dr.activity_date DESC
    """

    db = get_db_client(read_only=True)
    try:
        df = db.query(query)
        logger.info(f"Retrieved update activity for last {days} days")
        return df
    finally:
        db.close()


def get_data_quality_metrics() -> pd.DataFrame:
    """Get data quality metrics for key fields.

    Returns:
        DataFrame with completeness percentages for important fields

    Example:
        >>> df = get_data_quality_metrics()
        >>> print(df.to_string())
    """
    query = """
        SELECT
            'Movies Table' as source_table,
            COUNT(*) as total_records,
            ROUND(100.0 * SUM(CASE WHEN m.title IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) as title_completeness,
            ROUND(100.0 * SUM(CASE WHEN m.release_date IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) as release_date_completeness,
            ROUND(100.0 * SUM(CASE WHEN m.tmdb_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) as tmdb_id_completeness,
            ROUND(100.0 * SUM(CASE WHEN m.imdb_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) as imdb_id_completeness
        FROM movies m

        UNION ALL

        SELECT
            'TMDB Movies' as source_table,
            COUNT(*) as total_records,
            ROUND(100.0 * SUM(CASE WHEN t.title IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) as title_completeness,
            ROUND(100.0 * SUM(CASE WHEN t.overview IS NOT NULL AND t.overview != '' THEN 1 ELSE 0 END) / COUNT(*), 2) as overview_completeness,
            ROUND(100.0 * SUM(CASE WHEN t.budget > 0 THEN 1 ELSE 0 END) / COUNT(*), 2) as budget_completeness,
            ROUND(100.0 * SUM(CASE WHEN t.revenue > 0 THEN 1 ELSE 0 END) / COUNT(*), 2) as revenue_completeness
        FROM tmdb_movies t

        UNION ALL

        SELECT
            'OMDB Movies' as source_table,
            COUNT(*) as total_records,
            ROUND(100.0 * SUM(CASE WHEN o.title IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) as title_completeness,
            ROUND(100.0 * SUM(CASE WHEN o.imdb_rating IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) as rating_completeness,
            ROUND(100.0 * SUM(CASE WHEN o.director IS NOT NULL AND o.director != 'N/A' THEN 1 ELSE 0 END) / COUNT(*), 2) as director_completeness,
            ROUND(100.0 * SUM(CASE WHEN o.actors IS NOT NULL AND o.actors != 'N/A' THEN 1 ELSE 0 END) / COUNT(*), 2) as actors_completeness
        FROM omdb_movies o
    """

    db = get_db_client(read_only=True)
    try:
        df = db.query(query)
        logger.info("Retrieved data quality metrics")
        return df
    finally:
        db.close()


def get_refresh_compliance_by_age_group() -> pd.DataFrame:
    """Analyze refresh compliance based on movie age groups.

    Checks if movies are being refreshed according to the expected intervals:
    - Recent (0-60 days): Every 5 days
    - New (61-180 days): Every 14 days
    - Established (181-730 days): Every 30 days
    - Mature (731-1825 days): Every 90 days
    - Archived (1826+ days): Every 180 days

    Returns:
        DataFrame with age groups, expected vs actual refresh patterns

    Example:
        >>> df = get_refresh_compliance_by_age_group()
        >>> print(df.to_string())
    """
    query = """
        WITH movie_ages AS (
            SELECT
                m.movie_id,
                m.title,
                m.release_date,
                m.last_tmdb_update,
                m.last_omdb_update,
                m.data_frozen,
                DATEDIFF('day', m.release_date, CURRENT_DATE) as days_since_release,
                DATEDIFF('day', m.last_tmdb_update, CURRENT_TIMESTAMP) as days_since_tmdb_update,
                DATEDIFF('day', m.last_omdb_update, CURRENT_TIMESTAMP) as days_since_omdb_update,
                CASE
                    WHEN DATEDIFF('day', m.release_date, CURRENT_DATE) <= 60 THEN 'Recent (0-60d)'
                    WHEN DATEDIFF('day', m.release_date, CURRENT_DATE) <= 180 THEN 'New (61-180d)'
                    WHEN DATEDIFF('day', m.release_date, CURRENT_DATE) <= 730 THEN 'Established (181-730d)'
                    WHEN DATEDIFF('day', m.release_date, CURRENT_DATE) <= 1825 THEN 'Mature (731-1825d)'
                    ELSE 'Archived (1826+d)'
                END as age_group,
                CASE
                    WHEN DATEDIFF('day', m.release_date, CURRENT_DATE) <= 60 THEN 5
                    WHEN DATEDIFF('day', m.release_date, CURRENT_DATE) <= 180 THEN 14
                    WHEN DATEDIFF('day', m.release_date, CURRENT_DATE) <= 730 THEN 30
                    WHEN DATEDIFF('day', m.release_date, CURRENT_DATE) <= 1825 THEN 90
                    ELSE 180
                END as expected_refresh_days
            FROM movies m
            WHERE m.release_date IS NOT NULL
              AND (m.data_frozen IS NULL OR m.data_frozen = FALSE)
        )
        SELECT
            age_group,
            expected_refresh_days,
            COUNT(*) as total_movies,
            COUNT(CASE WHEN last_tmdb_update IS NULL THEN 1 END) as never_updated_tmdb,
            COUNT(CASE WHEN days_since_tmdb_update > expected_refresh_days THEN 1 END) as overdue_tmdb,
            COUNT(CASE WHEN days_since_tmdb_update <= expected_refresh_days THEN 1 END) as compliant_tmdb,
            ROUND(100.0 * COUNT(CASE WHEN days_since_tmdb_update <= expected_refresh_days THEN 1 END)
                / NULLIF(COUNT(CASE WHEN last_tmdb_update IS NOT NULL THEN 1 END), 0), 1) as pct_compliant_tmdb,
            ROUND(AVG(CASE WHEN last_tmdb_update IS NOT NULL THEN days_since_tmdb_update END), 1) as avg_days_since_update
        FROM movie_ages
        GROUP BY age_group, expected_refresh_days
        ORDER BY
            CASE age_group
                WHEN 'Recent (0-60d)' THEN 1
                WHEN 'New (61-180d)' THEN 2
                WHEN 'Established (181-730d)' THEN 3
                WHEN 'Mature (731-1825d)' THEN 4
                WHEN 'Archived (1826+d)' THEN 5
            END
    """

    db = get_db_client(read_only=True)
    try:
        df = db.query(query)
        logger.info("Retrieved refresh compliance analysis")
        return df
    finally:
        db.close()


def get_consecutive_unchanged_stats() -> pd.DataFrame:
    """Get statistics on consecutive unchanged refreshes to identify freeze candidates.

    Movies with 3+ consecutive unchanged refreshes (and 1826+ days old) are frozen.
    This helps monitor the freeze pipeline and identify movies approaching the threshold.

    Returns:
        DataFrame with unchanged refresh counts and movie statistics

    Example:
        >>> df = get_consecutive_unchanged_stats()
        >>> print(df[df['consecutive_unchanged'] >= 2])  # Near freeze threshold
    """
    query = """
        SELECT
            m.consecutive_unchanged_refreshes as consecutive_unchanged,
            COUNT(*) as movie_count,
            COUNT(CASE WHEN m.data_frozen = TRUE THEN 1 END) as frozen_count,
            COUNT(CASE WHEN DATEDIFF('day', m.release_date, CURRENT_DATE) >= 1826 THEN 1 END) as old_enough_to_freeze,
            ROUND(AVG(DATEDIFF('day', m.release_date, CURRENT_DATE)), 0) as avg_age_days,
            MIN(EXTRACT(YEAR FROM m.release_date)) as earliest_year,
            MAX(EXTRACT(YEAR FROM m.release_date)) as latest_year
        FROM movies m
        WHERE m.consecutive_unchanged_refreshes > 0
          AND m.release_date IS NOT NULL
        GROUP BY m.consecutive_unchanged_refreshes
        ORDER BY m.consecutive_unchanged_refreshes DESC
    """

    db = get_db_client(read_only=True)
    try:
        df = db.query(query)
        logger.info("Retrieved consecutive unchanged refresh statistics")
        return df
    finally:
        db.close()


def get_data_freshness_by_year() -> pd.DataFrame:
    """Get data freshness metrics grouped by release year.

    Shows how recently each year's movies were updated, helping identify
    stale data cohorts that need attention.

    Returns:
        DataFrame with year, movie counts, and average days since last update

    Example:
        >>> df = get_data_freshness_by_year()
        >>> stale = df[df['avg_days_since_tmdb_update'] > 90]
    """
    query = """
        SELECT
            EXTRACT(YEAR FROM m.release_date) as release_year,
            COUNT(*) as total_movies,
            COUNT(m.last_tmdb_update) as has_tmdb_update,
            COUNT(m.last_omdb_update) as has_omdb_update,
            ROUND(AVG(DATEDIFF('day', m.last_tmdb_update, CURRENT_TIMESTAMP)), 1) as avg_days_since_tmdb_update,
            ROUND(AVG(DATEDIFF('day', m.last_omdb_update, CURRENT_TIMESTAMP)), 1) as avg_days_since_omdb_update,
            MAX(DATE(m.last_tmdb_update)) as most_recent_tmdb_update,
            MIN(DATE(m.last_tmdb_update)) as least_recent_tmdb_update
        FROM movies m
        WHERE m.release_date IS NOT NULL
          AND (m.data_frozen IS NULL OR m.data_frozen = FALSE)
        GROUP BY release_year
        HAVING COUNT(m.last_tmdb_update) > 0
        ORDER BY release_year DESC
    """

    db = get_db_client(read_only=True)
    try:
        df = db.query(query)
        logger.info(f"Retrieved data freshness for {len(df)} years")
        return df
    finally:
        db.close()


def get_api_usage_estimates() -> Dict[str, Any]:
    """Estimate API usage and time to complete pending updates.

    Based on rate limits:
    - TMDB: ~40 requests/second (3,456,000/day theoretical)
    - OMDB: 1,000 requests/day per key

    Returns:
        Dictionary with estimated completion times and request counts

    Example:
        >>> estimates = get_api_usage_estimates()
        >>> print(f"Days to complete OMDB: {estimates['omdb_days_to_complete']:.1f}")
    """
    query = """
        SELECT
            COUNT(DISTINCT CASE WHEN m.last_tmdb_update IS NULL THEN m.movie_id END) as tmdb_never_updated,
            COUNT(DISTINCT CASE WHEN m.last_omdb_update IS NULL AND m.imdb_id IS NOT NULL THEN m.movie_id END) as omdb_never_updated,
            COUNT(DISTINCT CASE WHEN t.tmdb_id IS NOT NULL THEN m.movie_id END) as enriched_tmdb,
            COUNT(DISTINCT CASE WHEN o.imdb_id IS NOT NULL THEN m.movie_id END) as enriched_omdb,
            COUNT(DISTINCT m.movie_id) as total_movies,
            COUNT(DISTINCT CASE WHEN m.tmdb_id IS NOT NULL AND t.tmdb_id IS NULL THEN m.movie_id END) as tmdb_id_no_enrichment,
            COUNT(DISTINCT CASE WHEN m.imdb_id IS NOT NULL AND o.imdb_id IS NULL THEN m.movie_id END) as imdb_id_no_enrichment
        FROM movies m
        LEFT JOIN tmdb_movies t ON m.tmdb_id = t.tmdb_id
        LEFT JOIN omdb_movies o ON m.imdb_id = o.imdb_id
        WHERE (m.data_frozen IS NULL OR m.data_frozen = FALSE)
    """

    db = get_db_client(read_only=True)
    try:
        df = db.query(query)
        row = df.iloc[0]

        # Calculate pending: movies with IDs but no enrichment data
        tmdb_pending = int(row["tmdb_id_no_enrichment"]) + int(row["tmdb_never_updated"])
        omdb_pending = int(row["imdb_id_no_enrichment"]) + int(row["omdb_never_updated"])

        # Rate limits (conservative estimates)
        tmdb_per_day = 100_000  # Conservative batch processing rate
        omdb_per_day = 1_000    # Single API key limit

        estimates = {
            "tmdb_pending": tmdb_pending,
            "omdb_pending": omdb_pending,
            "tmdb_never_updated": int(row["tmdb_never_updated"]),
            "omdb_never_updated": int(row["omdb_never_updated"]),
            "enriched_tmdb": int(row["enriched_tmdb"]),
            "enriched_omdb": int(row["enriched_omdb"]),
            "total_movies": int(row["total_movies"]),
            "tmdb_days_to_complete": tmdb_pending / tmdb_per_day if tmdb_pending > 0 else 0,
            "omdb_days_to_complete": omdb_pending / omdb_per_day if omdb_pending > 0 else 0,
            "tmdb_rate_limit_per_day": tmdb_per_day,
            "omdb_rate_limit_per_day": omdb_per_day,
        }

        logger.info("Calculated API usage estimates")
        return estimates
    finally:
        db.close()

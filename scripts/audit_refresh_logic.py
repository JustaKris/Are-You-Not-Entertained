"""Audit refresh logic and database state."""

from ayne.data_collection.refresh_strategy import get_movies_due_for_refresh_query
from ayne.database.duckdb_client import DuckDBClient


def main():
    """Audit the database and print refresh-related statistics and samples.

    Connects to the DuckDB database, runs several queries to report basic
    statistics, recent update timestamps, age distribution, movies due for
    TMDB refresh (with and without a year filter), samples of recent movies,
    and sample refresh statuses for different age categories, then closes the
    database connection.

    Returns:
    -------
    None
    """
    db = DuckDBClient()

    print("=" * 80)
    print("DATABASE STATE AUDIT")
    print("=" * 80)

    # Basic stats
    print("\n1. BASIC STATISTICS:")
    result = db.query(
        """
        SELECT
            COUNT(*) as total_movies,
            COUNT(last_tmdb_update) as has_tmdb_update,
            COUNT(last_omdb_update) as has_omdb_update,
            COUNT(CASE WHEN data_frozen = TRUE THEN 1 END) as frozen_count,
            COUNT(CASE WHEN last_tmdb_update IS NULL THEN 1 END) as never_tmdb_updated,
            COUNT(CASE WHEN last_omdb_update IS NULL THEN 1 END) as never_omdb_updated
        FROM movies
    """
    )
    print(result.to_string())

    # Recent update stats
    print("\n2. RECENT UPDATE TIMESTAMPS:")
    result = db.query(
        """
        SELECT
            MIN(last_tmdb_update) as oldest_tmdb_update,
            MAX(last_tmdb_update) as newest_tmdb_update,
            MIN(last_omdb_update) as oldest_omdb_update,
            MAX(last_omdb_update) as newest_omdb_update
        FROM movies
        WHERE last_tmdb_update IS NOT NULL OR last_omdb_update IS NOT NULL
    """
    )
    print(result.to_string())

    # Age distribution
    print("\n3. MOVIE AGE DISTRIBUTION:")
    result = db.query(
        """
        SELECT
            CASE
                WHEN DATEDIFF('day', release_date, CURRENT_DATE) <= 60 THEN 'Recent (0-60 days)'
                WHEN DATEDIFF('day', release_date, CURRENT_DATE) <= 180 THEN 'Established (60-180 days)'
                WHEN DATEDIFF('day', release_date, CURRENT_DATE) <= 365 THEN 'Mature (180-365 days)'
                ELSE 'Archived (>365 days)'
            END as age_category,
            COUNT(*) as count
        FROM movies
        GROUP BY age_category
        ORDER BY MIN(DATEDIFF('day', release_date, CURRENT_DATE))
    """
    )
    print(result.to_string())

    # Check if any movies qualify for TMDB refresh (without year filter)
    print("\n4. MOVIES DUE FOR TMDB REFRESH (no year filter, limit 10):")
    query = get_movies_due_for_refresh_query(limit=10, data_source="tmdb")
    result = db.query(query)
    if result.empty:
        print("No movies due for TMDB refresh")
    else:
        print(f"Found {len(result)} movies:")
        print(
            result[["title", "release_date", "last_tmdb_update", "days_since_release"]].to_string()
        )

    # Check with min year 1950
    print("\n5. MOVIES DUE FOR TMDB REFRESH (min_year=1950, limit 10):")
    query = get_movies_due_for_refresh_query(limit=None, data_source="tmdb")
    # Add year filter
    query = query.replace("ORDER BY", "AND m.release_date >= '1950-01-01' ORDER BY")
    query = query.replace("LIMIT", "LIMIT 10")
    result = db.query(query)
    if result.empty:
        print("No movies due for TMDB refresh with min_year=1950")
    else:
        print(f"Found {len(result)} movies:")
        print(
            result[["title", "release_date", "last_tmdb_update", "days_since_release"]].to_string()
        )

    # Sample of movies with their update status
    print("\n6. SAMPLE OF RECENT MOVIES (last 10 by release date):")
    result = db.query(
        """
        SELECT
            title,
            release_date,
            last_tmdb_update,
            last_omdb_update,
            data_frozen,
            DATEDIFF('day', release_date, CURRENT_DATE) as days_old,
            DATEDIFF('day', last_tmdb_update, CURRENT_TIMESTAMP) as days_since_tmdb_update
        FROM movies
        ORDER BY release_date DESC
        LIMIT 10
    """
    )
    print(result.to_string())

    # Check TMDB refresh intervals for different age groups
    print("\n7. SAMPLE MOVIES FROM EACH AGE CATEGORY:")
    result = db.query(
        """
        WITH age_categories AS (
            SELECT
                title,
                release_date,
                last_tmdb_update,
                DATEDIFF('day', release_date, CURRENT_DATE) as days_old,
                DATEDIFF('day', last_tmdb_update, CURRENT_TIMESTAMP) as days_since_update,
                CASE
                    WHEN DATEDIFF('day', release_date, CURRENT_DATE) <= 60 THEN 'Recent'
                    WHEN DATEDIFF('day', release_date, CURRENT_DATE) <= 180 THEN 'Established'
                    WHEN DATEDIFF('day', release_date, CURRENT_DATE) <= 365 THEN 'Mature'
                    ELSE 'Archived'
                END as category,
                ROW_NUMBER() OVER (PARTITION BY
                    CASE
                        WHEN DATEDIFF('day', release_date, CURRENT_DATE) <= 60 THEN 'Recent'
                        WHEN DATEDIFF('day', release_date, CURRENT_DATE) <= 180 THEN 'Established'
                        WHEN DATEDIFF('day', release_date, CURRENT_DATE) <= 365 THEN 'Mature'
                        ELSE 'Archived'
                    END
                    ORDER BY release_date DESC) as rn
            FROM movies
            WHERE last_tmdb_update IS NOT NULL
        )
        SELECT
            category,
            title,
            days_old,
            days_since_update,
            CASE
                WHEN category = 'Recent' AND days_since_update >= 5 THEN 'DUE (5d threshold)'
                WHEN category = 'Established' AND days_since_update >= 15 THEN 'DUE (15d threshold)'
                WHEN category = 'Mature' AND days_since_update >= 30 THEN 'DUE (30d threshold)'
                WHEN category = 'Archived' AND days_since_update >= 90 THEN 'DUE (90d threshold)'
                ELSE 'Not due'
            END as refresh_status
        FROM age_categories
        WHERE rn = 1
        ORDER BY FIELD(category, 'Recent', 'Established', 'Mature', 'Archived')
    """
    )
    print(result.to_string())

    db.close()
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()

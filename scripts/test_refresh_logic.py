"""Test refresh logic by checking if movies should be due for refresh."""

from ayne.data_collection.refresh_strategy import get_movies_due_for_refresh_query
from ayne.database.duckdb_client import DuckDBClient

db = DuckDBClient()

# Check recent movies (should need refresh every 5 days)
print("RECENT MOVIES (0-60 days old):")
result = db.query(
    """
    SELECT
        title,
        release_date,
        DATEDIFF('day', release_date, CURRENT_DATE) as days_old,
        DATEDIFF('day', last_tmdb_update, CURRENT_TIMESTAMP) as days_since_update,
        CASE
            WHEN DATEDIFF('day', last_tmdb_update, CURRENT_TIMESTAMP) >= 5 THEN 'DUE FOR REFRESH'
            ELSE 'Not due yet'
        END as status
    FROM movies
    WHERE DATEDIFF('day', release_date, CURRENT_DATE) <= 60
    ORDER BY release_date DESC
    LIMIT 10
"""
)
print(result.to_string())
print()

# Now test by manually setting an old timestamp
print("TESTING: Setting one movie's timestamp to 6 days ago...")
db.execute(
    """
    UPDATE movies
    SET last_tmdb_update = CURRENT_TIMESTAMP - INTERVAL 6 DAYS
    WHERE tmdb_id = (
        SELECT tmdb_id FROM movies
        WHERE DATEDIFF('day', release_date, CURRENT_DATE) <= 60
        LIMIT 1
    )
"""
)

# Now check if it shows as needing refresh
query = get_movies_due_for_refresh_query(limit=5, data_source="tmdb")
result = db.query(query)

print(f"\nMOVIES DUE FOR TMDB REFRESH: {len(result)}")
if not result.empty:
    print(result[["title", "release_date", "last_tmdb_update", "days_since_release"]].to_string())
else:
    print("None found - something is wrong!")

db.close()

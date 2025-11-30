"""Test that partial data is saved when OMDB quota is exceeded."""

from ayne.database.duckdb_client import DuckDBClient

db = DuckDBClient()

# Get counts before and after
print("=== CHECKING OMDB DATA SAVE STATUS ===\n")

# Total OMDB movies
result = db.query("SELECT COUNT(*) as total FROM omdb_movies")
total_before = result.iloc[0]["total"]
print(f"Total OMDB movies in database: {total_before}")

# OMDB movies from 2020+
result2 = db.query(
    """
    SELECT COUNT(*) as count_2020
    FROM movies m
    JOIN omdb_movies o ON m.imdb_id = o.imdb_id
    WHERE m.release_date >= '2020-01-01'
"""
)
print(f"OMDB movies from 2020+: {result2.iloc[0]['count_2020']}")

# Check recent updates (today)
result3 = db.query(
    """
    SELECT COUNT(*) as updated_today
    FROM movies m
    WHERE m.last_omdb_update >= CURRENT_DATE
"""
)
updated_today = result3.iloc[0]["updated_today"]
print(f"Movies with OMDB updates today: {updated_today}")

# Sample of recently updated movies
if updated_today > 0:
    result4 = db.query(
        """
        SELECT m.title, m.release_date, m.last_omdb_update
        FROM movies m
        WHERE m.last_omdb_update >= CURRENT_DATE
        ORDER BY m.last_omdb_update DESC
        LIMIT 5
    """
    )
    print("\nRecently updated movies (sample):")
    print(result4.to_string(index=False))
else:
    print("\n⚠️  NO MOVIES UPDATED TODAY - The quota handling bug is still present!")
    print("Expected: ~990 movies updated today from the latest run")

db.close()

print("\n" + "=" * 50)

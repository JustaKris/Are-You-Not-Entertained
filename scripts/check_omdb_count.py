"""Check OMDB movie count before and after quota limit hit."""

from ayne.database.duckdb_client import DuckDBClient

db = DuckDBClient()

# Total OMDB movies
result = db.query("SELECT COUNT(*) as total FROM omdb_movies")
print(f"Total OMDB movies in database: {result.iloc[0]['total']}")

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

# Movies from 2020+ that need OMDB data
result3 = db.query(
    """
    SELECT COUNT(*) as missing
    FROM movies m
    LEFT JOIN omdb_movies o ON m.imdb_id = o.imdb_id
    WHERE m.release_date >= '2020-01-01'
      AND m.imdb_id IS NOT NULL
      AND m.imdb_id != ''
      AND o.imdb_id IS NULL
"""
)
print(f"Movies from 2020+ still missing OMDB data: {result3.iloc[0]['missing']}")

# Check recent updates
result4 = db.query(
    """
    SELECT COUNT(*) as updated_today
    FROM movies m
    WHERE m.last_omdb_update >= CURRENT_DATE
"""
)
print(f"Movies with OMDB updates today: {result4.iloc[0]['updated_today']}")

db.close()

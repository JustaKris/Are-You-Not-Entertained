"""Restore test movie timestamps to current time."""

from ayne.database.duckdb_client import DuckDBClient

db = DuckDBClient()
db.execute(
    "UPDATE movies SET last_tmdb_update = CURRENT_TIMESTAMP WHERE DATEDIFF('day', last_tmdb_update, CURRENT_TIMESTAMP) > 3"
)
db.close()
print("Restored timestamps")

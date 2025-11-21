"""Quick test script to verify DuckDB setup works."""

import sys
from pathlib import Path

# Add project root to path for direct execution
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

import pandas as pd

from src.core.logging import configure_logging, get_logger
from src.database.duckdb_client import DuckDBClient

configure_logging(level="INFO")
logger = get_logger(__name__)


def test_database_setup():
    """Test that database can be created and queried."""
    logger.info("Testing DuckDB setup...")

    try:
        # Create client
        db = DuckDBClient()
        logger.info(f"✅ Connected to database: {db.db_path}")

        # Create tables
        db.create_tables_from_sql()
        logger.info("✅ Schema created successfully")

        # Verify tables exist
        tables = ["movies", "tmdb_movies", "omdb_movies"]
        for table in tables:
            exists = db.table_exists(table)
            assert exists, f"Table {table} not found"
            logger.info(f"✅ Table '{table}' exists")

        # Test insert
        test_data = pd.DataFrame(
            {"tmdb_id": [12345], "title": ["Test Movie"], "release_date": ["2024-01-01"]}
        )
        db.upsert_dataframe("movies", test_data, key_columns=["tmdb_id"])
        logger.info("✅ Insert test passed")

        # Test query
        result = db.query("SELECT * FROM movies WHERE tmdb_id = 12345")
        assert len(result) == 1
        assert result["title"].iloc[0] == "Test Movie"
        logger.info("✅ Query test passed")

        # Test update
        update_data = pd.DataFrame(
            {"tmdb_id": [12345], "title": ["Test Movie UPDATED"], "release_date": ["2024-01-01"]}
        )
        db.upsert_dataframe("movies", update_data, key_columns=["tmdb_id"])
        result = db.query("SELECT * FROM movies WHERE tmdb_id = 12345")
        assert result["title"].iloc[0] == "Test Movie UPDATED"
        logger.info("✅ Update test passed")

        # Clean up
        db.execute("DELETE FROM movies WHERE tmdb_id = 12345")

        db.close()
        logger.info("\n" + "=" * 60)
        logger.info("✅ ALL TESTS PASSED!")
        logger.info("=" * 60)
        logger.info("\nYour DuckDB setup is working correctly.")
        logger.info(f"Database location: {db.db_path}")
        logger.info("\nNext steps:")
        logger.info("1. Run: python scripts/init_database.py")
        logger.info("2. Run: python scripts/collect_all_data.py")

        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = test_database_setup()
    exit(0 if success else 1)

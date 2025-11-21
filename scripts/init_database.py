"""Initialize DuckDB database with schema."""

import sys
from pathlib import Path

# Add project root to path for direct execution
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.core.config import settings
from src.core.logging import configure_logging, get_logger
from src.database.duckdb_client import DuckDBClient

configure_logging(level=settings.log_level, use_json=settings.use_json_logging)  # type: ignore
logger = get_logger(__name__)


def main():
    """Initialize the database schema."""
    logger.info("Initializing DuckDB database...")

    try:
        # Create database client
        db = DuckDBClient()

        # Create all tables from schema
        db.create_tables_from_sql()

        # Verify tables were created
        tables = ["movies", "tmdb_movies", "omdb_movies", "numbers_movies", "movie_refresh_state"]
        logger.info("\nVerifying tables:")
        for table in tables:
            exists = db.table_exists(table)
            status = "✅" if exists else "❌"
            logger.info(f"{status} Table '{table}' exists: {exists}")

        # Show database info
        result = db.query(
            """
            SELECT table_name, COUNT(*) as row_count
            FROM information_schema.tables
            WHERE table_schema = 'main'
            GROUP BY table_name
        """
        )

        logger.info("\nDatabase tables created:")
        for _, row in result.iterrows():
            logger.info(f"  - {row['table_name']}")

        db.close()
        logger.info("\n✅ Database initialization complete!")
        logger.info(f"Database location: {db.db_path}")

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()

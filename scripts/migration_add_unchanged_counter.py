"""Migration script to add consecutive_unchanged_refreshes column and apply fixes.

This script:
1. Adds the consecutive_unchanged_refreshes column
2. Backfills last_full_refresh for movies with both TMDB and OMDB data
3. Unfreezes all movies to reset the system
"""

from ayne.core.logging import get_logger
from ayne.database.duckdb_client import DuckDBClient

logger = get_logger(__name__)


def run_migration():
    """Run the migration to add tracking column and fix existing issues."""
    logger.info("Starting migration: Add consecutive_unchanged_refreshes column")

    db = DuckDBClient()

    try:
        # Step 1: Add the new column
        logger.info("Step 1: Adding consecutive_unchanged_refreshes column...")
        db.execute(
            """
            ALTER TABLE movies
            ADD COLUMN IF NOT EXISTS consecutive_unchanged_refreshes INTEGER DEFAULT 0
        """
        )
        logger.info("✅ Column added successfully")

        # Step 2: Backfill last_full_refresh
        logger.info("Step 2: Backfilling last_full_refresh for movies with both updates...")
        db.execute(
            """
            UPDATE movies
            SET last_full_refresh = GREATEST(last_tmdb_update, last_omdb_update)
            WHERE last_tmdb_update IS NOT NULL
              AND last_omdb_update IS NOT NULL
              AND last_full_refresh IS NULL
        """
        )

        count_full_refresh = db.query(
            "SELECT COUNT(*) as count FROM movies WHERE last_full_refresh IS NOT NULL"
        )
        logger.info(
            f"✅ Backfilled last_full_refresh for {count_full_refresh['count'].iloc[0]:,} movies"
        )

        # Step 3: Unfreeze all movies
        logger.info("Step 3: Unfreezing all movies...")
        db.execute("UPDATE movies SET data_frozen = FALSE")

        count_unfrozen = db.query("SELECT COUNT(*) as count FROM movies WHERE data_frozen = FALSE")
        logger.info(f"✅ Unfroze {count_unfrozen['count'].iloc[0]:,} movies")

        # Step 4: Reset consecutive unchanged counters
        logger.info("Step 4: Resetting consecutive_unchanged_refreshes counters...")
        db.execute("UPDATE movies SET consecutive_unchanged_refreshes = 0")
        logger.info("✅ Reset all counters")

        # Verification
        logger.info("\n" + "=" * 60)
        logger.info("MIGRATION VERIFICATION")
        logger.info("=" * 60)

        stats = db.query(
            """
            SELECT
                COUNT(*) as total_movies,
                COUNT(CASE WHEN last_full_refresh IS NOT NULL THEN 1 END) as has_full_refresh,
                COUNT(CASE WHEN data_frozen = TRUE THEN 1 END) as frozen_count,
                COUNT(CASE WHEN consecutive_unchanged_refreshes = 0 THEN 1 END) as counter_reset
            FROM movies
        """
        )

        total = stats["total_movies"].iloc[0]
        full_refresh = stats["has_full_refresh"].iloc[0]
        frozen = stats["frozen_count"].iloc[0]
        reset = stats["counter_reset"].iloc[0]

        logger.info(f"Total movies: {total:,}")
        logger.info(f"Movies with last_full_refresh: {full_refresh:,}")
        logger.info(f"Frozen movies: {frozen:,}")
        logger.info(f"Counters reset to 0: {reset:,}")
        logger.info("=" * 60)

        logger.info("\n✅ Migration completed successfully!")

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_migration()

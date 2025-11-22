"""Optimized data collection script with intelligent refresh strategies.

Features:
- Age-based refresh intervals
- Async API calls with rate limiting
- Automatic data freezing for stable movies
- Efficient batch updates
"""

import argparse
import asyncio

from ayne.core.config import settings
from ayne.core.logging import configure_logging, get_logger
from ayne.data_collection.orchestrator import DataCollectionOrchestrator
from ayne.database.duckdb_client import DuckDBClient

configure_logging(level=settings.log_level, use_json=settings.use_json_logging)  # type: ignore
logger = get_logger(__name__)


async def main_async(args):
    """Main async workflow."""
    logger.info("=" * 80)
    logger.info("OPTIMIZED DATA COLLECTION WITH INTELLIGENT REFRESH")
    logger.info("=" * 80)

    db = DuckDBClient()
    orchestrator = DataCollectionOrchestrator(db)

    try:
        # Run collection
        stats = await orchestrator.run_full_collection(
            discover_start_year=args.start_year,
            discover_end_year=args.end_year,
            max_discover_pages=args.max_pages,
            refresh_limit=args.refresh_limit,
            discover_min_vote_count=args.min_votes,
        )

        # Display statistics
        logger.info("\n" + "=" * 80)
        logger.info("COLLECTION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Movies discovered: {stats['discovered']}")
        logger.info(f"TMDB data updated: {stats['tmdb_updated']}")
        logger.info(f"OMDB data updated: {stats['omdb_updated']}")
        logger.info(f"Movies frozen: {stats['frozen']}")

        # Display database statistics
        logger.info("\n" + "=" * 80)
        logger.info("DATABASE STATISTICS")
        logger.info("=" * 80)

        db_stats = db.get_collection_stats()
        if not db_stats.empty:
            row = db_stats.iloc[0]
            logger.info(f"Total movies: {row['total_movies']}")
            logger.info(f"With TMDB data: {row['with_tmdb']}")
            logger.info(f"With OMDB data: {row['with_omdb']}")
            logger.info(f"Fully refreshed: {row['fully_refreshed']}")
            logger.info(f"Frozen (stable): {row['frozen']}")
            logger.info("\nBy age category:")
            logger.info(f"  Recent (0-60 days): {row['recent_movies']}")
            logger.info(f"  Established (60-180 days): {row['established_movies']}")
            logger.info(f"  Mature (180-365 days): {row['mature_movies']}")
            logger.info(f"  Archived (>365 days): {row['archived_movies']}")

        # Show sample of recently updated movies
        if stats["tmdb_updated"] > 0 or stats["omdb_updated"] > 0:
            logger.info("\n" + "=" * 80)
            logger.info("RECENTLY UPDATED MOVIES (SAMPLE)")
            logger.info("=" * 80)

            sample = db.query(
                """
                SELECT
                    m.title,
                    m.release_date,
                    m.last_tmdb_update,
                    m.last_omdb_update,
                    m.data_frozen,
                    DATEDIFF('day', m.release_date, CURRENT_DATE) as days_old
                FROM movies m
                WHERE m.last_tmdb_update IS NOT NULL
                   OR m.last_omdb_update IS NOT NULL
                ORDER BY GREATEST(
                    COALESCE(m.last_tmdb_update, TIMESTAMP '1970-01-01'),
                    COALESCE(m.last_omdb_update, TIMESTAMP '1970-01-01')
                ) DESC
                LIMIT 10
            """
            )

            if not sample.empty:
                print("\n" + sample.to_string(index=False))

    except Exception as e:
        logger.error(f"Collection failed: {e}", exc_info=True)
        raise
    finally:
        await orchestrator.close()
        db.close()

    logger.info("\n" + "=" * 80)
    logger.info("✅ DATA COLLECTION COMPLETE!")
    logger.info("=" * 80)


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Optimized movie data collection with intelligent refresh strategies"
    )

    # Discovery options
    parser.add_argument(
        "--start-year",
        type=int,
        default=None,
        help="Start year for movie discovery (omit to skip discovery)",
    )
    parser.add_argument(
        "--end-year",
        type=int,
        default=None,
        help="End year for movie discovery (defaults to start-year)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Maximum pages to fetch per year during discovery",
    )
    parser.add_argument(
        "--min-votes",
        type=int,
        default=200,
        help="Minimum vote count for discovered movies (default: 200)",
    )

    # Refresh options
    parser.add_argument(
        "--refresh-limit",
        type=int,
        default=100,
        help="Maximum number of movies to refresh (default: 100)",
    )
    parser.add_argument(
        "--refresh-only", action="store_true", help="Only refresh existing movies, skip discovery"
    )

    args = parser.parse_args()

    # If refresh-only, ensure no discovery
    if args.refresh_only:
        args.start_year = None

    # Run async main
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()

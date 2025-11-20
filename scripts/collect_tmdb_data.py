"""Collect movie data from TMDB API and store in DuckDB."""

import sys
from pathlib import Path

# Add project root to path for direct execution
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from typing import Optional
import pandas as pd
from src.database.duckdb_client import DuckDBClient
from src.data_collection.tmdb import TMDBClient
from src.core.logging import configure_logging, get_logger
from src.core.config import settings

configure_logging(level=settings.log_level, use_json=settings.use_json_logging)  # type: ignore
logger = get_logger(__name__)


def collect_basic_movies(
    start_year: int = 2020,
    end_year: int = 2024,
    min_vote_count: int = 200,
    max_pages: Optional[int] = None
):
    """
    Collect basic movie info from TMDB and store in database.
    
    Args:
        start_year: Starting year for movie discovery
        end_year: Ending year for movie discovery
        min_vote_count: Minimum vote count filter
        max_pages: Maximum pages per year (None = all pages)
    """
    logger.info("=" * 60)
    logger.info("TMDB Basic Movie Collection")
    logger.info("=" * 60)
    
    db = DuckDBClient()
    tmdb = TMDBClient()
    
    try:
        # Discover movies
        logger.info(f"Discovering movies from {start_year} to {end_year}...")
        movies = tmdb.discover_movies(
            start_year=start_year,
            end_year=end_year,
            min_vote_count=min_vote_count,
            max_pages=max_pages
        )
        
        if not movies:
            logger.warning("No movies discovered")
            return
        
        # Save to parquet (backup)
        tmdb.save_to_parquet(movies, f"tmdb_discovered_{start_year}_{end_year}.parquet")
        
        # Convert to DataFrame
        df = pd.DataFrame(movies)
        
        # Upsert to movies table (basic info only)
        logger.info("Upserting to movies table...")
        movies_df = df[["tmdb_id", "title", "release_date"]].copy()
        db.upsert_dataframe("movies", movies_df, key_columns=["tmdb_id"])
        
        logger.info(f"✅ Successfully collected {len(movies)} movies")
        
        # Show sample
        sample = db.query("SELECT * FROM movies ORDER BY release_date DESC LIMIT 5")
        logger.info("\nSample movies in database:")
        logger.info(f"\n{sample.to_string()}")
        
    except Exception as e:
        logger.error(f"Failed to collect TMDB data: {e}", exc_info=True)
        raise
    finally:
        db.close()


def collect_detailed_features(limit: int = 50):
    """
    Collect detailed features for movies that don't have them yet.
    
    Args:
        limit: Maximum number of movies to process
    """
    logger.info("=" * 60)
    logger.info("TMDB Detailed Features Collection")
    logger.info("=" * 60)
    
    db = DuckDBClient()
    tmdb = TMDBClient()
    
    try:
        # Find movies without detailed features
        query = """
            SELECT m.tmdb_id
            FROM movies m
            LEFT JOIN tmdb_movies t ON m.tmdb_id = t.tmdb_id
            WHERE t.tmdb_id IS NULL
              AND m.tmdb_id IS NOT NULL
            ORDER BY m.release_date DESC
            LIMIT ?
        """
        
        result = db.query(query, params=[limit])
        tmdb_ids = result["tmdb_id"].tolist()
        
        if not tmdb_ids:
            logger.info("No movies need detailed features")
            return
        
        logger.info(f"Fetching details for {len(tmdb_ids)} movies...")
        
        # Fetch detailed features
        movies = tmdb.get_batch_movie_details(tmdb_ids)
        
        if not movies:
            logger.warning("No movie details retrieved")
            return
        
        # Save to parquet (backup)
        tmdb.save_to_parquet(movies, "tmdb_detailed_features.parquet")
        
        # Upsert to tmdb_movies table
        df = pd.DataFrame(movies)
        logger.info("Upserting to tmdb_movies table...")
        db.upsert_dataframe("tmdb_movies", df, key_columns=["tmdb_id"])
        
        # Update last_tmdb_update in movies table
        update_query = """
            UPDATE movies
            SET last_tmdb_update = current_timestamp
            WHERE tmdb_id IN ({})
        """.format(",".join(map(str, tmdb_ids)))
        db.execute(update_query)
        
        logger.info(f"✅ Successfully collected details for {len(movies)} movies")
        
        # Show sample
        sample = db.query("""
            SELECT tmdb_id, title, budget, revenue, runtime, vote_average
            FROM tmdb_movies
            ORDER BY last_updated_utc DESC
            LIMIT 5
        """)
        logger.info("\nSample movie features:")
        logger.info(f"\n{sample.to_string()}")
        
    except Exception as e:
        logger.error(f"Failed to collect detailed features: {e}", exc_info=True)
        raise
    finally:
        db.close()


def main():
    """Main collection workflow."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Collect TMDB movie data")
    parser.add_argument("--start-year", type=int, default=2020, help="Start year")
    parser.add_argument("--end-year", type=int, default=2024, help="End year")
    parser.add_argument("--min-votes", type=int, default=200, help="Minimum vote count")
    parser.add_argument("--max-pages", type=int, default=None, help="Max pages per year")
    parser.add_argument("--details-limit", type=int, default=50, help="Movies to get details for")
    parser.add_argument("--skip-basic", action="store_true", help="Skip basic collection")
    parser.add_argument("--skip-details", action="store_true", help="Skip details collection")
    
    args = parser.parse_args()
    
    # Collect basic info
    if not args.skip_basic:
        collect_basic_movies(
            start_year=args.start_year,
            end_year=args.end_year,
            min_vote_count=args.min_votes,
            max_pages=args.max_pages
        )
    
    # Collect detailed features
    if not args.skip_details:
        collect_detailed_features(limit=args.details_limit)
    
    logger.info("\n" + "=" * 60)
    logger.info("TMDB Data Collection Complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

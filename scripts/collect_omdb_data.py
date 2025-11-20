"""Collect movie data from OMDB API and store in DuckDB."""

import sys
from pathlib import Path

# Add project root to path for direct execution
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

import pandas as pd
from src.database.duckdb_client import DuckDBClient
from src.data_collection.omdb import OMDBClient
from src.core.logging import configure_logging, get_logger
from src.core.config import settings

configure_logging(level=settings.log_level, use_json=settings.use_json_logging)  # type: ignore
logger = get_logger(__name__)


def collect_omdb_data(limit: int = 100):
    """
    Collect OMDB data for movies that have IMDb IDs but no OMDB data yet.
    
    Args:
        limit: Maximum number of movies to process
    """
    logger.info("=" * 60)
    logger.info("OMDB Data Collection")
    logger.info("=" * 60)
    
    db = DuckDBClient()
    omdb = OMDBClient()
    
    try:
        # Find movies with IMDb IDs but no OMDB data
        query = """
            SELECT m.imdb_id, m.title
            FROM movies m
            LEFT JOIN omdb_movies o ON m.imdb_id = o.imdb_id
            WHERE m.imdb_id IS NOT NULL
              AND m.imdb_id != ''
              AND o.imdb_id IS NULL
            ORDER BY m.release_date DESC
            LIMIT ?
        """
        
        result = db.query(query, params=[limit])
        
        if result.empty:
            logger.info("No movies need OMDB data")
            return
        
        imdb_ids = result["imdb_id"].tolist()
        logger.info(f"Found {len(imdb_ids)} movies needing OMDB data")
        
        # Fetch OMDB data
        movies = omdb.get_batch_movies(imdb_ids)
        
        if not movies:
            logger.warning("No OMDB data retrieved")
            return
        
        # Save to parquet (backup)
        omdb.save_to_parquet(movies, "omdb_movies.parquet")
        
        # Upsert to omdb_movies table
        df = pd.DataFrame(movies)
        logger.info("Upserting to omdb_movies table...")
        db.upsert_dataframe("omdb_movies", df, key_columns=["imdb_id"])
        
        # Update last_omdb_update in movies table
        update_query = """
            UPDATE movies
            SET last_omdb_update = current_timestamp
            WHERE imdb_id IN ({})
        """.format(",".join([f"'{id}'" for id in [m["imdb_id"] for m in movies]]))
        db.execute(update_query)
        
        logger.info(f"✅ Successfully collected OMDB data for {len(movies)} movies")
        
        # Show sample
        sample = db.query("""
            SELECT imdb_id, title, year, imdb_rating, box_office, awards
            FROM omdb_movies
            ORDER BY last_updated_utc DESC
            LIMIT 5
        """)
        logger.info("\nSample OMDB data:")
        logger.info(f"\n{sample.to_string()}")
        
        # Show statistics
        stats = db.query("""
            SELECT 
                COUNT(*) as total_movies,
                COUNT(CASE WHEN imdb_rating IS NOT NULL THEN 1 END) as with_ratings,
                COUNT(CASE WHEN box_office IS NOT NULL THEN 1 END) as with_box_office,
                AVG(imdb_rating) as avg_rating
            FROM omdb_movies
        """)
        logger.info("\nOMDB data statistics:")
        logger.info(f"\n{stats.to_string()}")
        
    except Exception as e:
        logger.error(f"Failed to collect OMDB data: {e}", exc_info=True)
        raise
    finally:
        db.close()


def main():
    """Main collection workflow."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Collect OMDB movie data")
    parser.add_argument("--limit", type=int, default=100, help="Maximum movies to process")
    
    args = parser.parse_args()
    
    collect_omdb_data(limit=args.limit)
    
    logger.info("\n" + "=" * 60)
    logger.info("OMDB Data Collection Complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

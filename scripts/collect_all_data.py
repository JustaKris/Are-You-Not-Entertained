"""Master script to collect all movie data (TMDB + OMDB)."""

import sys
from pathlib import Path

# Add project root to path for direct execution
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.database.duckdb_client import DuckDBClient
from src.data_collection.tmdb import TMDBClient
from src.data_collection.omdb import OMDBClient
from src.core.logging import configure_logging, get_logger
from src.core.config import settings
import pandas as pd

configure_logging(level=settings.log_level, use_json=settings.use_json_logging)  # type: ignore
logger = get_logger(__name__)


def main():
    """
    Complete data collection workflow:
    1. Discover movies from TMDB (basic info)
    2. Get detailed features from TMDB
    3. Get OMDB data for movies with IMDb IDs
    """
    logger.info("=" * 70)
    logger.info("COMPLETE MOVIE DATA COLLECTION WORKFLOW")
    logger.info("=" * 70)
    
    db = DuckDBClient()
    tmdb_client = TMDBClient()
    omdb_client = OMDBClient()
    
    try:
        # ================================================================
        # STEP 1: Discover movies from TMDB
        # ================================================================
        logger.info("\n📥 STEP 1: Discovering movies from TMDB...")
        
        movies = tmdb_client.discover_movies(
            start_year=2020,
            end_year=2024,
            min_vote_count=200,
            max_pages=2  # Limit for testing
        )
        
        if movies:
            df_movies = pd.DataFrame(movies)
            movies_for_db = df_movies[["tmdb_id", "title", "release_date"]].copy()
            db.upsert_dataframe("movies", movies_for_db, key_columns=["tmdb_id"])
            logger.info(f"✅ Inserted/updated {len(movies)} movies")
        
        # ================================================================
        # STEP 2: Get detailed TMDB features
        # ================================================================
        logger.info("\n📥 STEP 2: Fetching detailed TMDB features...")
        
        # Get movies without detailed features
        tmdb_ids_query = """
            SELECT m.tmdb_id
            FROM movies m
            LEFT JOIN tmdb_movies t ON m.tmdb_id = t.tmdb_id
            WHERE t.tmdb_id IS NULL
              AND m.tmdb_id IS NOT NULL
            LIMIT 20
        """
        
        result = db.query(tmdb_ids_query)
        tmdb_ids = result["tmdb_id"].tolist()
        
        if tmdb_ids:
            logger.info(f"Fetching details for {len(tmdb_ids)} movies...")
            detailed_movies = tmdb_client.get_batch_movie_details(tmdb_ids)
            
            if detailed_movies:
                df_details = pd.DataFrame(detailed_movies)
                db.upsert_dataframe("tmdb_movies", df_details, key_columns=["tmdb_id"])
                
                # Update timestamp in movies table
                for tmdb_id in [m["tmdb_id"] for m in detailed_movies]:
                    db.execute(
                        "UPDATE movies SET last_tmdb_update = current_timestamp WHERE tmdb_id = ?",
                        [tmdb_id]
                    )
                
                logger.info(f"✅ Inserted/updated {len(detailed_movies)} detailed features")
        else:
            logger.info("No movies need detailed features")
        
        # ================================================================
        # STEP 3: Get OMDB data
        # ================================================================
        logger.info("\n📥 STEP 3: Fetching OMDB data...")
        
        # Get movies with IMDb IDs but no OMDB data
        omdb_query = """
            SELECT m.imdb_id
            FROM movies m
            INNER JOIN tmdb_movies t ON m.tmdb_id = t.tmdb_id
            LEFT JOIN omdb_movies o ON m.imdb_id = o.imdb_id
            WHERE t.imdb_id IS NOT NULL
              AND t.imdb_id != ''
              AND o.imdb_id IS NULL
            LIMIT 20
        """
        
        result = db.query(omdb_query)
        imdb_ids = result["imdb_id"].tolist()
        
        if imdb_ids:
            logger.info(f"Fetching OMDB data for {len(imdb_ids)} movies...")
            omdb_movies = omdb_client.get_batch_movies(imdb_ids)
            
            if omdb_movies:
                df_omdb = pd.DataFrame(omdb_movies)
                db.upsert_dataframe("omdb_movies", df_omdb, key_columns=["imdb_id"])
                
                # Update timestamp in movies table
                for imdb_id in [m["imdb_id"] for m in omdb_movies]:
                    db.execute(
                        "UPDATE movies SET last_omdb_update = current_timestamp WHERE imdb_id = ?",
                        [imdb_id]
                    )
                
                logger.info(f"✅ Inserted/updated {len(omdb_movies)} OMDB records")
        else:
            logger.info("No movies need OMDB data")
        
        # ================================================================
        # STEP 4: Show summary statistics
        # ================================================================
        logger.info("\n📊 COLLECTION SUMMARY:")
        logger.info("=" * 70)
        
        stats = db.query("""
            SELECT 
                COUNT(DISTINCT m.movie_id) as total_movies,
                COUNT(DISTINCT t.tmdb_id) as with_tmdb_details,
                COUNT(DISTINCT o.imdb_id) as with_omdb_data,
                COUNT(CASE WHEN t.tmdb_id IS NOT NULL AND o.imdb_id IS NOT NULL THEN 1 END) as complete_records
            FROM movies m
            LEFT JOIN tmdb_movies t ON m.tmdb_id = t.tmdb_id
            LEFT JOIN omdb_movies o ON m.imdb_id = o.imdb_id
        """)
        
        logger.info(f"\n{stats.to_string()}")
        
        # Show sample of complete movies
        sample = db.query("""
            SELECT 
                m.title,
                m.release_date,
                t.revenue,
                t.budget,
                t.vote_average as tmdb_rating,
                o.imdb_rating,
                o.box_office
            FROM movies m
            INNER JOIN tmdb_movies t ON m.tmdb_id = t.tmdb_id
            INNER JOIN omdb_movies o ON m.imdb_id = o.imdb_id
            WHERE t.revenue > 0
            ORDER BY m.release_date DESC
            LIMIT 5
        """)
        
        if not sample.empty:
            logger.info("\n📽️  Sample movies with complete data:")
            logger.info(f"\n{sample.to_string()}")
        
    except Exception as e:
        logger.error(f"Collection failed: {e}", exc_info=True)
        raise
    finally:
        db.close()
    
    logger.info("\n" + "=" * 70)
    logger.info("✅ DATA COLLECTION COMPLETE!")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()

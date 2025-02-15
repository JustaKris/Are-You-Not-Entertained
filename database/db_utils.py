from database.db_tables import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from data_collection.tmdb import TMDBClient
from data_collection.omdb import OMDBClient
from database.db_tables import TMDBMovieBase, TMDBMovie, OMDBMovie
from typing import List


def init_db(db_url: str):
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)  # Create tables if they don't exist.
    Session = sessionmaker(bind=engine)
    return Session


def get_missing_omdb_ids(session) -> List[str]:
    """
    Queries the TMDB movie base table (table 02) and the OMDB movies table (table 03)
    and returns a list of IMDb IDs that are present in the TMDB table but not already in the OMDB table.
    
    Args:
        session: An active SQLAlchemy session.
    
    Returns:
        List[str]: A list of IMDb IDs missing from the OMDB movies table.
    """
    # Query all IMDb IDs from the TMDB base table (table 02)
    tmdb_ids = {row.imdb_id for row in session.query(TMDBMovie.imdb_id).all() if row.imdb_id}

    # Query all IMDb IDs from the OMDB movies table (table 03)
    omdb_ids = {row.imdb_id for row in session.query(OMDBMovie.imdb_id).all() if row.imdb_id}

    # Return those IDs that are in the TMDB table but not in the OMDB table
    missing_ids = list(tmdb_ids - omdb_ids)
    return missing_ids


if __name__ == "__main__":
    from config.config_loader import load_config

    # Initialize local PostgreSQL session
    db_url = load_config("DB_URL")
    Session = init_db(db_url)
    session = Session()
    print("Database initialized.")

    # TMDB ---------------------------------------------------
    # Load API key and client
    TMDB_API_KEY = load_config("TMDB_API_KEY")
    tmdb_client = TMDBClient(api_key=TMDB_API_KEY)

    # Get movie IDs (and associated features)
    movies = tmdb_client.get_movie_ids(start_year=2024, min_vote_count=250)
    tmdb_client.save_movies_to_db(movies, session)  # Push IDs to DB

    # Get movie features and push to DB
    movie_ids = [movie.tmdb_id for movie in session.query(TMDBMovieBase.tmdb_id).all()]
    movies = tmdb_client.get_movie_features(movie_ids)
    tmdb_client.save_movie_features_to_db(movies, session)

    # OMDB ---------------------------------------------------
    # Load API key and client
    api_key = load_config("OMDB_API_KEY")
    omdb_client = OMDBClient(api_key=api_key, delay=0.1)

    # Test fetching and pushing multiple movies to DB:
    # imdb_ids = ["tt0111161", "tt0068646", "tt0071562"]
    imdb_ids = get_missing_omdb_ids(session)  # Add missing IDs
    movies = omdb_client.get_multiple_movies(imdb_ids=imdb_ids, save_to_file=True)
    omdb_client.save_multiple_movies_to_db(movies, session)


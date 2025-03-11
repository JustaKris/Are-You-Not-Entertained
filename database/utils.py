import pandas as pd
from database.models import Base, TMDBMovieBase, TMDBMovie, OMDBMovie
from database.queries import prepped_data_query
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from typing import List


def init_db_session(db_url: str):
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)  # Create tables if they don't exist.
    Session = sessionmaker(bind=engine)
    print("Database session initialized.")
    return Session()


def fetch_data_from_db(session):
    # Execute and fetch results
    data = session.execute(text(prepped_data_query))
    # Close the DB session
    session.close()
    # Convert to DataFrame
    df = pd.DataFrame(data.fetchall(), columns=data.keys())
    print("Data queried and prepped.")
    return df


def get_missing_tmdb_features_by_id(session, limit: int = None) -> List[str]:
    """
    Queries the TMDB movie base table (table 02) and the OMDB movies table (table 03)
    and returns a list of IMDb IDs (sorted by most recent release_date) that are present in the TMDB table
    but not already in the OMDB table.
    
    Args:
        session: An active SQLAlchemy session.
        limit (int, optional): The maximum number of missing IMDb IDs to return. 
                               If None, returns all missing IDs.
    
    Returns:
        List[str]: A list of missing IMDb IDs from the OMDB movies table, ordered by release_date descending.
    """
    # Build a subquery to get all imdb_ids already in TMDB
    tmdb_features_subq = session.query(TMDBMovie.tmdb_id)
    # print(tmdb_features_subq)
    
    # Query TMDBMovie rows whose tmdb_id is not in the TMDB features table, ordered by release_date descending.
    query = session.query(TMDBMovieBase).filter(~TMDBMovieBase.tmdb_id.in_(tmdb_features_subq)).order_by(TMDBMovieBase.release_date.desc())
    
    if limit is not None:
        query = query.limit(limit)
    
    missing_movies = query.all()
    
    # Extract the imdb_id from each movie
    missing_ids = [movie.tmdb_id for movie in missing_movies if movie.tmdb_id]
    return missing_ids


def get_missing_omdb_ids(session, limit: int = None) -> List[str]:
    """
    Queries the TMDB movie base table (table 02) and the OMDB movies table (table 03)
    and returns a list of IMDb IDs (sorted by most recent release_date) that are present in the TMDB table
    but not already in the OMDB table.
    
    Args:
        session: An active SQLAlchemy session.
        limit (int, optional): The maximum number of missing IMDb IDs to return. 
                               If None, returns all missing IDs.
    
    Returns:
        List[str]: A list of missing IMDb IDs from the OMDB movies table, ordered by release_date descending.
    """
    # Build a subquery to get all imdb_ids already in OMDB
    omdb_subq = session.query(OMDBMovie.imdb_id)
    
    # Query TMDBMovie rows whose imdb_id is not in the OMDB table, ordered by release_date descending.
    query = session.query(TMDBMovie).filter(~TMDBMovie.imdb_id.in_(omdb_subq)).order_by(TMDBMovie.release_date.desc())
    
    if limit is not None:
        query = query.limit(limit)
    
    missing_movies = query.all()
    
    # Extract the imdb_id from each movie
    missing_ids = [movie.imdb_id for movie in missing_movies if movie.imdb_id]
    return missing_ids


def clean_na(d: dict, na_values=None, replace_with=None) -> dict:
    """
    Cleans a dictionary by replacing 'NA' values.

    :param d: Dictionary to clean.
    :param na_values: Set of values considered as "NA" (default: common placeholders).
    :param replace_with: Value to replace NA values with (default: None).
    :return: New dictionary with cleaned values.
    """
    if na_values is None:
        na_values = {"N/A", "null", "None", None, "", 0}  # Default NA values

    def clean_value(v):
        if isinstance(v, list):
            return [clean_value(item) for item in v]  # Recursively clean lists
        elif isinstance(v, tuple):
            return tuple(clean_value(item) for item in v)  # Convert back to tuple
        elif isinstance(v, set):
            return {clean_value(item) for item in v}  # Convert back to set
        elif isinstance(v, dict):  
            return clean_na(v, na_values, replace_with)  # Recursively clean nested dicts
        return replace_with if v in na_values else v  # Handle normal values

    return {k: clean_value(v) for k, v in d.items()}



if __name__ == "__main__":
    from data_collection.tmdb import TMDBClient
    from data_collection.omdb import OMDBClient
    from database.models import TMDBMovieBase
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
    # movies = tmdb_client.get_movie_ids(start_year=2024, min_vote_count=250)
    # tmdb_client.save_movies_to_db(movies, session)  # Push IDs to DB

    # Get movie features and push to DB
    movie_ids = [movie.tmdb_id for movie in session.query(TMDBMovieBase.tmdb_id).all()]
    # movies = tmdb_client.get_movie_features(movie_ids)
    # tmdb_client.save_movie_features_to_db(movies, session)

    # OMDB ---------------------------------------------------
    # Load API key and client
    api_key = load_config("OMDB_API_KEY")
    omdb_client = OMDBClient(api_key=api_key, delay=0.1)

    # Test fetching and pushing multiple movies to DB:
    # imdb_ids = ["tt0111161", "tt0068646", "tt0071562"]
    imdb_ids = get_missing_omdb_ids(session)  # Add missing IDs
    movies = omdb_client.get_multiple_movies(imdb_ids=imdb_ids, save_to_file=True)
    omdb_client.save_multiple_movies_to_db(movies, session)


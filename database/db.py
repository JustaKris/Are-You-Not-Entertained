from models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from data_collection.tmdb import TMDBClient
from database.models import TMDBMovieBase

def init_db(db_url: str):
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)  # Create tables if they don't exist.
    Session = sessionmaker(bind=engine)
    return Session


if __name__ == "__main__":
    from config.config_loader import load_config

    # Initialize local PostgreSQL session
    db_url = load_config("DB_URL")
    Session = init_db(db_url)
    session = Session()
    print("Database initialized.")

    # Load API key
    TMDB_API_KEY = load_config("TMDB_API_KEY")
    tmdb_client = TMDBClient(api_key=TMDB_API_KEY)

    # Get movie IDs (and associated features)
    # movies = tmdb_client.get_movie_ids(start_year=2025, min_vote_count=250)
    # tmdb_client.save_movies_to_db(movies, session)  # Push IDs to DB

    # Get movie features and push to DB
    movie_ids = [movie.tmdb_id for movie in session.query(TMDBMovieBase.tmdb_id).all()]
    movies = tmdb_client.get_movie_features(movie_ids)
    tmdb_client.save_movie_features_to_db(movies, session)


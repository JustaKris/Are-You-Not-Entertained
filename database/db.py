from models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from data_collection.tmdb import TMDBClient

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
    movies = tmdb_client.get_movie_ids(start_year=2024, min_vote_count=350)

    # Push movies to the database
    tmdb_client.save_movies_to_db(movies, session)


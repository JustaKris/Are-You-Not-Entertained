from src.data_collection.tmdb import TMDBClient
from src.data_collection.omdb import OMDBClient
from database.models import TMDBMovieBase
from database.utils import init_db, get_missing_omdb_ids, get_missing_tmdb_features_by_id


def main():
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
    # movies = tmdb_client.get_movie_ids(start_year=1950, min_vote_count=300)
    # movies = tmdb_client.batch_get_movie_ids(start_year=1950, end_year=2026, min_vote_count=200)
    # tmdb_client.save_movies_to_db(movies, session)  # Push IDs to DB

    # # Get movie features and push to DB
    # movie_ids = [movie.tmdb_id for movie in session.query(TMDBMovieBase.tmdb_id).all()]
    # movie_ids = get_missing_tmdb_features_by_id(session)
    # movies = tmdb_client.get_movie_features(movie_ids)
    # tmdb_client.save_movie_features_to_db(movies, session)

    # OMDB ---------------------------------------------------
    # Load API key and client
    api_key = load_config("OMDB_API_KEY")
    omdb_client = OMDBClient(api_key=api_key, delay=0.05)

    # Test fetching and pushing multiple movies to DB:
    imdb_ids = get_missing_omdb_ids(session, 1002)  # Add missing IDs
    movies = omdb_client.get_multiple_movies(imdb_ids=imdb_ids, save_to_file=True)
    omdb_client.save_multiple_movies_to_db(movies, session)


if __name__ == "__main__":
    main()
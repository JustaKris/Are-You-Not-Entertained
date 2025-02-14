from data_collection.tmdb import TMDBClient
from data_collection.omdb import OMDBClient
from config.config_loader import load_config
from src.utils import load_csv


def main():
    # Load API key
    TMDB_API_KEY = load_config("TMDB_API_KEY")

    # Initialize the TMDB client
    tmdb_client = TMDBClient(api_key=TMDB_API_KEY)
    
    # Get movie IDs (and associated features)
    tmdb_client.get_movie_ids(start_year=1950, min_vote_count=350)

    # Get movie features
    movie_ids = load_csv("01_movie_ids.csv")["ID"].tolist()
    tmdb_client.get_movie_features(movie_ids)

    # OMDB ---------------------------------------------------
    # # Load API key
    # OMDB_API_KEY = load_config("OMDB_API_KEY")

    # # Replace 'YOUR_OMDB_API_KEY' with your actual OMDB API key.
    # omdb_client = OMDBClient(api_key=OMDB_API_KEY, delay=0.1)

    # # Alternatively, fetch a movie by title.
    # movie_by_title = omdb_client.get_movie_by_title("The Shawshank Redemption", year=1994, features=[
    #     "Title", "Year", "Genre", "Director", "imdbRating", "BoxOffice"
    # ])
    # print(movie_by_title)


if __name__ == "__main__":
    main()
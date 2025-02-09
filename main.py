from data_collection.tmdb import TMDBClient
from config.config_loader import load_config
from src.utils import load_csv


def main():
    # Load environment variables
    TMDB_API_KEY = load_config("TMDB_API_KEY")
    if not TMDB_API_KEY:
        print("TMDB_API_KEY not found!")
    else:
        # Initialize the TMDB client
        tmdb_client = TMDBClient(api_key=TMDB_API_KEY)
        
        # Get movie IDs (and associated features)
        tmdb_client.get_movie_ids(start_year=2024, min_vote_count=350)

        # Get movie features
        # movies = load_csv("movie_ids.csv")
        # movie_ids = movies["ID"].tolist()
        movie_ids = load_csv("01_movie_ids.csv")["ID"].tolist()
        print(len(movie_ids))
        tmdb_client.get_movie_features(movie_ids)



if __name__ == "__main__":
    main()
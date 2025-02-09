from data_collection.tmdb import TMDBClient
from config.config_loader import load_config


def main():
    # Load environment variables
    TMDB_API_KEY = load_config("TMDB_API_KEY")
    if not TMDB_API_KEY:
        print("TMDB_API_KEY not found!")
    else:
        # Initialize the TMDB client
        tmdb_client = TMDBClient(api_key=TMDB_API_KEY)
        
        # Get movie IDs (and associated features) using the method
        tmdb_client.get_movie_ids(start_year=2008, min_vote_count=350)



if __name__ == "__main__":
    main()
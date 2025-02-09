import time
import requests
import pandas as pd
from config.config_loader import load_config


TMDB_API_KEY = load_config("TMDB_API_KEY")

# Function to fetch data from TMDB API
def fetch_tmdb_data(api_key, endpoint=None):
    """
    Fetches data from TMDB API and returns only the selected features for each movie.
    
    Args:
        api_key (str): Your TMDB API key.
        endpoint (str, optional): The API endpoint. If not provided, uses the default discover endpoint.
        
    Returns:
        List[dict]: A list of movies with only the selected features.
    """
    # Base settings
    base_url = "https://api.themoviedb.org/3/"
    if endpoint is None:
        endpoint = (
            "discover/movie?include_adult=false&include_video=false&language=en-US"
            "&page=1&primary_release_year=2025&sort_by=primary_release_date.desc"
        )
    features = [
        "id", "genre_ids", "title", "original_title", "popularity",
        "overview", "release_date", "vote_average", "vote_count"
    ]
    
    # Build URL and initial parameters
    url = f"{base_url}{endpoint}"
    params = {"api_key": api_key}
    
    # Initial request to determine the total number of pages
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"Failed to fetch data: {response.status_code}")
        return {}
    
    data = response.json()
    total_pages = data.get("total_pages", 1)
    print(f"Total pages available: {total_pages}")

    total_pages = 6
    
    all_data = []
    # Loop through each page and fetch results
    for page in range(1, total_pages + 1):
        params["page"] = page
        response = requests.get(url, params=params)
        if response.status_code == 200:
            page_data = response.json()
            results = page_data.get("results", [])
            all_data.extend(results)
            print(f"Fetched page {page}")
        else:
            print(f"Failed to fetch data for page {page}: {response.status_code}")
            break
        time.sleep(0.5)  # Pause between requests to avoid rate limiting

    # Filter each movie record to include only the specified features
    filtered_data = [
        {key: movie.get(key) for key in features}
        for movie in all_data
    ]
    
    return filtered_data


if __name__ == "__main__":

    from src.utils import save_to_csv

    # Configuration
    API_KEY = TMDB_API_KEY
    OUTPUT_FILE = "tmdb_movie_data.csv"  # Name of the CSV file
    ENDPOINT = "movie/popular"  # Change to 'tv/popular' for TV shows
    ENDPOINT = "discover/movie?include_adult=false&include_video=false&language=en-US&page=1&primary_release_year=2025&sort_by=primary_release_date.desc"
    NUM_PAGES = 5  # Number of pages to fetch (each page has ~20 results)

    # Fetch data
    movie_data = fetch_tmdb_data(api_key=API_KEY, endpoint=ENDPOINT)
    
    # Save to CSV
    save_to_csv(movie_data, OUTPUT_FILE)

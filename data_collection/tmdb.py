import time
import requests
import pandas as pd
from config.config_loader import load_config


TMDB_API_KEY = load_config("TMDB_API_KEY")

# Function to fetch data from TMDB API
def fetch_tmdb_data(api_key, endpoint="movie/550", pages=None):
    """
    Fetches data from TMDB API.
    Args:
        api_key (str): Your TMDB API key.
        endpoint (str): The API endpoint (e.g., 'movie/popular', 'tv/top_rated', 'movie/550').
        pages (int, optional): Number of pages to fetch (only for paginated endpoints).
    Returns:
        List[dict] or dict: Movie details if single movie, or list of movies if paginated.
    """
    base_url = "https://api.themoviedb.org/3/"
    # base_url = "https://api.themoviedb.org/3/discover/movie?include_adult=false&include_video=false&language=en-US&page=1&primary_release_year=2025&sort_by=primary_release_date.desc"
    url = f"{base_url}{endpoint}"
    params = {"api_key": api_key}
    
    if pages is None:  # Single movie request
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch data: {response.status_code}")
            return {}
    
    # Paginated request (e.g., 'movie/popular')
    all_data = []
    for page in range(1, pages + 1):
        params["page"] = page
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            all_data.extend(data.get("results", []))
            print(f"Fetched page {page} of {endpoint}")
        else:
            print(f"Failed to fetch data for page {page}: {response.status_code}")
            break
        
        time.sleep(0.5)
    
    return all_data

# # Function to save data to CSV
# def save_to_csv(data, filename):
#     """
#     Saves data to a CSV file.
#     Args:
#         data (List[dict]): The data to save.
#         filename (str): The name of the CSV file.
#     """
#     # Convert to DataFrame and save
#     df = pd.DataFrame(data)
#     df.to_csv("./data/" + filename, index=False)
#     print(f"Data saved to {filename}")

if __name__ == "__main__":
    from src.utils import save_to_csv
    # Configuration
    API_KEY = TMDB_API_KEY
    OUTPUT_FILE = "tmdb_movie_data.csv"  # Name of the CSV file
    ENDPOINT = "movie/popular"  # Change to 'tv/popular' for TV shows
    ENDPOINT = "discover/movie?include_adult=false&include_video=false&language=en-US&page=1&primary_release_year=2025&sort_by=primary_release_date.desc"
    NUM_PAGES = 5  # Number of pages to fetch (each page has ~20 results)

    # Fetch data
    movie_data = fetch_tmdb_data(api_key=API_KEY, endpoint=ENDPOINT, pages=NUM_PAGES)
    
    # Save to CSV
    save_to_csv(movie_data, OUTPUT_FILE)

import requests
import pandas as pd
import time
# from config import TMDB_API_KEY

from dotenv import load_dotenv
import os
# Load environment variables from .env file
load_dotenv()
# Fetch the API key from environment variables
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

# import requests
# response = requests.get("https://api.themoviedb.org/3/", verify=False)  # Disable SSL verification


# Function to fetch data from TMDB API
def fetch_tmdb_data(api_key, endpoint="movie/popular", pages=1):
    """
    Fetches data from TMDB API.
    Args:
        api_key (str): Your TMDB API key.
        endpoint (str): The API endpoint (e.g., 'movie/popular', 'tv/top_rated').
        pages (int): Number of pages to fetch.
    Returns:
        List[dict]: A list of movie data.
    """
    base_url = "https://api.themoviedb.org/3/"
    all_data = []

    for page in range(1, pages + 1):
        url = f"{base_url}{endpoint}"
        params = {"api_key": api_key, "page": page}
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            all_data.extend(data.get("results", []))
            print(f"Fetched page {page} of {endpoint}")
        else:
            print(f"Failed to fetch data for page {page}: {response.status_code}")
            break
        
        # To avoid hitting the rate limit
        time.sleep(0.5)
    
    return all_data

# Function to save data to CSV
def save_to_csv(data, filename):
    """
    Saves data to a CSV file.
    Args:
        data (List[dict]): The data to save.
        filename (str): The name of the CSV file.
    """
    # Convert to DataFrame and save
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"Data saved to {filename}")

if __name__ == "__main__":
    # Configuration
    API_KEY = TMDB_API_KEY
    OUTPUT_FILE = "tmdb_movie_data.csv"  # Name of the CSV file
    ENDPOINT = "movie/popular"  # Change to 'tv/popular' for TV shows
    NUM_PAGES = 5  # Number of pages to fetch (each page has ~20 results)

    # Fetch data
    movie_data = fetch_tmdb_data(api_key=API_KEY, endpoint=ENDPOINT, pages=NUM_PAGES)
    
    # Save to CSV
    save_to_csv(movie_data, OUTPUT_FILE)

import time
import requests
import logging
from typing import List, Dict, Optional

from src.utils import save_to_csv


class TMDBClient:
    def __init__(self, api_key: str, delay: float = 0.1):
        """
        Initializes the TMDBClient with your TMDB API key.
        
        Args:
            api_key (str): Your TMDB API key.
            delay (float): Delay (in seconds) between API requests to avoid rate limiting.
        """
        self.api_key = api_key
        self.base_url = "https://api.themoviedb.org/3/"
        self.delay = delay
        self.session = requests.Session()
        # Set the API key as a default parameter for all requests
        self.session.params = {"api_key": self.api_key}
        logging.basicConfig(level=logging.INFO)
    
    def fetch_tmdb_data(
        self,
        endpoint: str,
        features: Optional[List[str]] = None,
        total_pages: Optional[int] = None,
        output_file_name: str = 'default.csv'
    ) -> None:
        """
        Fetches data from the TMDB API, filters the results based on the specified features, 
        and saves the filtered data to a CSV file.
        
        This method sends requests to the TMDB API using the provided endpoint. 
        It automatically handles pagination by determining the total number of pages from the API response 
        if `total_pages` is not specified.
        
        Args:
            endpoint (str): The API endpoint to query.
            features (Optional[List[str]]): A list of keys corresponding to the movie features to be retained 
                in the output. Each key in the final output is uppercased. If not provided, all features are retained.
            total_pages (Optional[int]): The number of pages to fetch. If None, the method uses the total number 
                of pages indicated by the API response.
            output_file_name (str): The name of the CSV file where the filtered data will be saved.
        
        Returns:
            None. The method saves the filtered data to a CSV file in "./data/tmdb/<output_file_name>".
        """
        url = f"{self.base_url}{endpoint}"
        
        # Initial request to determine the total number of pages
        try:
            response = self.session.get(url)
            response.raise_for_status()
        except requests.RequestException as e:
            logging.error(f"Failed to fetch initial data: {e}")
            return
        
        data = response.json()
    
        # Determine the number of pages to fetch
        if total_pages is None:
            total_pages = data.get("total_pages", 1)
            logging.info(f"Total pages available: {total_pages}")
    
        all_data: List[Dict] = []
        # Loop through each page and fetch results
        for page in range(1, total_pages + 1):
            try:
                # Create a new parameters dict for each request to avoid accidental side effects.
                params = {"page": page}
                response = self.session.get(url, params=params)
                response.raise_for_status()
            except requests.RequestException as e:
                logging.error(f"Failed to fetch data for page {page}: {e}")
                break
            
            page_data = response.json()
            results = page_data.get("results", [])
            all_data.extend(results)
            logging.info(f"Fetched page {page}")
            time.sleep(self.delay)
    
        # Filter each movie record to include only the specified features, uppercasing keys in the output
        if features:
            filtered_data = []
            for movie in all_data:
                filtered_movie = {}
                for key in features:
                    # Only include the key if it exists in the movie data
                    filtered_movie[key.upper()] = movie.get(key)
                filtered_data.append(filtered_movie)
            all_data = filtered_data
    
        # Save the filtered data to a CSV file in the "./data/tmdb" directory
        save_to_csv(all_data, output_file_name, "./data/tmdb")
    
    def get_movie_ids(self, start_year: int = 2025, min_vote_count: int = 350) -> None:
        """
        Constructs an endpoint for discovering movies based on a start year and minimum vote count,
        then fetches movie IDs and selected features from the TMDB API.
        
        This method builds an endpoint that fetches movies with a primary release date on or after January 1st
        of the specified start year and with a vote count greater than or equal to the provided minimum. It then
        calls `fetch_tmdb_data` to retrieve the data, filtering for the following features:
            - id
            - genre_ids
            - release_date
            - vote_count
            - vote_average
            - title
        
        The resulting data is saved to a CSV file named "movies.csv" in the "./data/tmdb" directory.
        
        Args:
            start_year (int): The starting release year for filtering movies. Defaults to 2025.
            min_vote_count (int): The minimum number of votes a movie must have to be included. Defaults to 350.
        
        Returns:
            None
        """
        endpoint = (
            f"discover/movie?include_adult=false&include_video=false&language=en-US"
            f"&page=1&primary_release_date.gte={start_year}-01-01&vote_count.gte={min_vote_count}"
            "&sort_by=primary_release_date.desc"
        )
        features = ["id", "genre_ids", "release_date", "vote_count", "vote_average", "title"]
        self.fetch_tmdb_data(endpoint=endpoint, features=features, output_file_name="movies.csv")

    
    def get_movie_features(self):
        pass


if __name__ == "__main__":
    from config.config_loader import load_config

    # Load environment variables
    TMDB_API_KEY = load_config("TMDB_API_KEY")
    if not TMDB_API_KEY:
        print("TMDB_API_KEY not found!")
    else:
        # Initialize the TMDB client
        tmdb_client = TMDBClient(api_key=TMDB_API_KEY)
        
        # Get movie IDs (and associated features) using the method
        tmdb_client.get_movie_ids(start_year=2025, min_vote_count=200)

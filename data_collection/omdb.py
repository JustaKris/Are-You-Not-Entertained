import time
import logging
import requests
from typing import Optional, List, Dict, Union
from src.utils import save_to_csv


class OMDBClient:
    def __init__(self, api_key: str, delay: float = 0.5):
        """
        Initializes the OMDBClient with your OMDB API key.

        Args:
            api_key (str): Your OMDB API key.
            delay (float): Delay (in seconds) between API requests to avoid rate limiting.
        """
        self.api_key = api_key
        self.base_url = "http://www.omdbapi.com/"
        self.delay = delay
        self.session = requests.Session()
        # Set the API key as a default parameter for all requests
        self.session.params = {"apikey": self.api_key}
        logging.basicConfig(level=logging.INFO)

    def get_movie_by_imdb_id(self, imdb_id: str, features: Optional[List[str]] = None) -> Dict:
        """
        Retrieves movie data from the OMDB API using the IMDb ID.

        Args:
            imdb_id (str): The IMDb ID of the movie (e.g., "tt0111161").
            features (Optional[List[str]]): A list of keys corresponding to the movie features to be retained.
                If provided, the final output will include only these keys (uppercased).

        Returns:
            Dict: The movie data, optionally filtered by the specified features.
        """
        # OMDB uses the 'i' parameter for IMDb ID lookups.
        params = {"i": imdb_id}
        try:
            response = self.session.get(self.base_url, params=params)
            response.raise_for_status()
        except requests.RequestException as e:
            logging.error(f"Failed to fetch data for IMDb ID {imdb_id}: {e}")
            return {}

        movie_data = response.json()
        if features:
            movie_data = {key.upper(): movie_data.get(key) for key in features}
        logging.info(f"Retrieved data for IMDb ID {imdb_id}")
        time.sleep(self.delay)
        return movie_data

    def get_movie_by_title(self, title: str, year: Optional[int] = None, features: Optional[List[str]] = None) -> Dict:
        """
        Retrieves movie data from the OMDB API by searching with the movie title (and optional release year),
        then saves the result to a CSV file in the data/omdb folder. The CSV file will be named after the movie title.

        Args:
            title (str): The title of the movie.
            year (Optional[int]): The release year of the movie to narrow the search.
            features (Optional[List[str]]): A list of keys corresponding to the movie features to be retained.
                If provided, the final output will include only these keys (uppercased).

        Returns:
            Dict: The movie data, optionally filtered by the specified features.
        """
        # OMDB uses the 't' parameter for title-based lookups.
        params = {"t": title}
        if year:
            params["y"] = year

        try:
            response = self.session.get(self.base_url, params=params)
            response.raise_for_status()
        except requests.RequestException as e:
            logging.error(f"Failed to fetch data for title '{title}': {e}")
            return {}

        movie_data = response.json()
        if features:
            movie_data = {key.upper(): movie_data.get(key) for key in features}

        # Use the returned title (or the input title if not present) to create a filename.
        movie_title = movie_data.get("Title") or title
        # sanitized_title = self._sanitize_filename(movie_title)
        sanitized_title = "Shawshank"
        file_name = f"{sanitized_title}.csv"
        save_to_csv(movie_data, file_name, "./data/omdb")
        logging.info(f"Saved movie data for '{movie_title}' to {file_name}")

        time.sleep(self.delay)
        return movie_data

    def get_multiple_movies(self, imdb_ids: List[str], features: Optional[List[str]] = None,
                            output_file_name: str = 'omdb_movies.csv') -> None:
        """
        Retrieves movie data for a list of IMDb IDs, aggregates the results,
        and saves them to a CSV file.

        Args:
            imdb_ids (List[str]): A list of IMDb IDs for which to retrieve movie details.
            features (Optional[List[str]]): A list of keys corresponding to the movie features to be retained.
                If provided, the final output will include only these keys (uppercased).
            output_file_name (str): The CSV file name to which the aggregated movie data will be saved.

        Returns:
            None
        """
        all_data: List[Dict] = []
        total_ids = len(imdb_ids)
        for idx, imdb_id in enumerate(imdb_ids, start=1):
            data = self.get_movie_by_imdb_id(imdb_id, features=features)
            if data:
                all_data.append(data)
            logging.info(f"Processed {idx}/{total_ids} movies")
        save_to_csv(all_data, output_file_name, "./data/omdb")

# Example usage:
if __name__ == "__main__":
    # Fetch API key
    api_key = load_config("OMDB_API_KEY")
    
    # Replace 'YOUR_OMDB_API_KEY' with your actual OMDB API key.
    omdb_client = OMDBClient(api_key=api_key, delay=0.1)
    
    # Fetch a single movie by IMDb ID.
    # movie = omdb_client.get_movie_by_imdb_id("tt0111161", features=[
    #     "Title", "Year", "Genre", "Director", "imdbRating", "BoxOffice"
    # ])
    # print(movie)
    
    # Alternatively, fetch a movie by title.
    movie_by_title = omdb_client.get_movie_by_title("The Shawshank Redemption", year=1994, features=[
        "Title", "Year", "Genre", "Director", "imdbRating", "BoxOffice"
    ])
    print(movie_by_title)
    
    # Fetch multiple movies (example IMDb IDs list) and save to CSV.
    # imdb_ids = ["tt0111161", "tt0068646", "tt0071562"]
    # omdb_client.get_multiple_movies(imdb_ids, features=[
    #     "Title", "Year", "Genre", "Director", "imdbRating", "BoxOffice"
    # ])

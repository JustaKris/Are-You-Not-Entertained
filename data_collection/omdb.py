import time
import re
import requests
from typing import Optional, List, Dict, Union
from src.utils import save_to_csv


class OMDBClient:
    def __init__(self, api_key: str, delay: float = 0.1):
        """
        Initializes the OMDBClient with your OMDB API key.

        Args:
            api_key (str): Your OMDB API key.
            delay (float): Delay (in seconds) between API requests.
        """
        self.api_key = api_key
        self.base_url = "http://www.omdbapi.com/"
        self.delay = delay
        self.session = requests.Session()
        # Set the API key as a default parameter for all requests
        self.session.params = {"apikey": self.api_key}

    def _sanitize_filename(self, s: str) -> str:
        """
        Sanitizes a string to be used as a filename by replacing non-alphanumeric characters with underscores.
        """
        return re.sub(fr"[^\w\-]", "_", s)

    def get_movie_by_imdb_id(self, imdb_id: str, features: Optional[List[str]] = None) -> Dict:
        """
        Retrieves movie data from the OMDB API using the IMDb ID.

        Args:
            imdb_id (str): The IMDb ID of the movie (e.g., "tt0111161").
            features (Optional[List[str]]): A list of keys to be retained (final keys are uppercased).

        Returns:
            Dict: The movie data, optionally filtered by the specified features.
        """
        params = {"i": imdb_id}
        try:
            response = self.session.get(self.base_url, params=params)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to fetch data for IMDb ID {imdb_id}: {e}")
            return {}

        movie_data = response.json()
        if features:
            movie_data = {key.upper(): movie_data.get(key) for key in features}
        time.sleep(self.delay)
        return movie_data

    def get_movie_by_title(self, title: str, year: Optional[int] = None, features: Optional[List[str]] = None) -> Dict:
        """
        Retrieves movie data from the OMDB API by searching with the movie title (and optional release year),
        then saves the result to a CSV file in the data/omdb folder. The CSV file is named based on the movie title.

        Args:
            title (str): The title of the movie.
            year (Optional[int]): The release year to narrow the search.
            features (Optional[List[str]]): A list of keys to be retained (final keys are uppercased).

        Returns:
            Dict: The movie data, optionally filtered by the specified features.
        """
        params = {"t": title}
        if year:
            params["y"] = year

        try:
            response = self.session.get(self.base_url, params=params)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to fetch data for title '{title}': {e}")
            return {}

        movie_data = response.json()

        if features:
            movie_data = {key.upper(): movie_data.get(key) for key in features}

        # print(movie_data)
        # exit()

        # Use the returned title (or input title if not present) to create a filename.
        movie_title = movie_data.get("Title") or title

        sanitized_title = self._sanitize_filename(movie_title)
        # print(sanitized_title)
        # exit()
        file_name = f"{sanitized_title}.csv"
        save_to_csv(movie_data, file_name, "./data/omdb")
        time.sleep(self.delay)
        return movie_data

    def get_multiple_movies(self, imdb_ids: List[str], features: Optional[List[str]] = None,
                            output_file_name: str = 'omdb_movies.csv') -> None:
        """
        Retrieves movie data for a list of IMDb IDs, aggregates the results,
        and saves them to a CSV file.

        Args:
            imdb_ids (List[str]): A list of IMDb IDs.
            features (Optional[List[str]]): A list of keys to be retained (final keys are uppercased).
            output_file_name (str): The CSV filename for aggregated movie data.

        Returns:
            None
        """
        all_data: List[Dict] = []
        for imdb_id in imdb_ids:
            data = self.get_movie_by_imdb_id(imdb_id, features=features)
            if data:
                all_data.append(data)
        save_to_csv(all_data, output_file_name, "./data/omdb")

# Example usage:
if __name__ == "__main__":
    from config.config_loader import load_config

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
    # movie_by_title = omdb_client.get_movie_by_title("The Shawshank Redemption", year=1994, features=[
    #     "Title", "Year", "Genre", "Director", "imdbRating", "BoxOffice"
    # ])
    # print(movie_by_title)
    
    # Fetch multiple movies (example IMDb IDs list) and save to CSV.
    # imdb_ids = ["tt0111161", "tt0068646", "tt0071562"]
    # omdb_client.get_multiple_movies(imdb_ids, features=[
    #     "Title", "Year", "Genre", "Director", "imdbRating", "BoxOffice"
    # ])

    
    # Test fetching by title:
    movie = omdb_client.get_movie_by_title("The Shawshank Redemption", year=1994, features=["Title", "Year", "Genre", "Director", "imdbRating", "BoxOffice"])
    print(movie)
    
    # Test fetching by IMDb ID:
    # movie2 = omdb_client.get_movie_by_imdb_id("tt0111161", features=["Title", "Year", "Genre", "Director", "imdbRating", "BoxOffice"])
    # print(movie2)

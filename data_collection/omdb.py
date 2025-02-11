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
        self.features = [
            "imdbID", "Title", "Year", "Genre", "Director", "Writer", "Actors",
            "imdbRating", "imdbVotes", "Metascore", "BoxOffice", "Released", "Runtime",
            "Language", "Country", "Rated", "Awards"
        ]

    def _sanitize_filename(self, s: str) -> str:
        """
        Sanitizes a string to be used as a filename by replacing non-alphanumeric characters with underscores.
        """
        return re.sub(r"[^\w\-]", "_", s)

    def _extract_ratings(self, movie_data: Dict) -> None:
        """
        Processes the 'Ratings' field in the movie_data dictionary and extracts the Rotten Tomatoes
        and Metacritic ratings, adding them as separate keys.
        """
        ratings = movie_data.get("Ratings", [])
        for rating in ratings:
            source = rating.get("Source")
            value = rating.get("Value")
            if source == "Rotten Tomatoes":
                movie_data["ROTTEN_TOMATOES_RATING"] = value
            elif source == "Metacritic":
                movie_data["META_CRITIC_RATING"] = value

    def get_movie_by_imdb_id(self, imdb_id: str) -> Dict:
        """
        Retrieves movie data from the OMDB API using the IMDb ID.

        Args:
            imdb_id (str): The IMDb ID of the movie (e.g., "tt0111161").

        Returns:
            Dict: The movie data (with selected features and added rating columns).
        """
        params = {"i": imdb_id}
        try:
            response = self.session.get(self.base_url, params=params)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to fetch data for IMDb ID {imdb_id}: {e}")
            return {}

        full_data = response.json()
        # Process the Ratings field to extract Rotten Tomatoes and Metacritic ratings.
        self._extract_ratings(full_data)
        # Build a new dictionary from our desired features (uppercased).
        new_data = {key.upper(): full_data.get(key) for key in self.features}
        # Add the extracted ratings if available.
        if "ROTTEN_TOMATOES_RATING" in full_data:
            new_data["ROTTEN_TOMATOES_RATING"] = full_data["ROTTEN_TOMATOES_RATING"]
        if "META_CRITIC_RATING" in full_data:
            new_data["META_CRITIC_RATING"] = full_data["META_CRITIC_RATING"]

        time.sleep(self.delay)
        return new_data

    def get_movie_by_title(self, title: str, year: Optional[int] = None) -> Dict:
        """
        Retrieves movie data from the OMDB API by searching with the movie title (and optional release year),
        then saves the result to a CSV file in the data/omdb folder. The CSV file is named based on the movie title.

        Args:
            title (str): The title of the movie.
            year (Optional[int]): The release year to narrow the search.

        Returns:
            Dict: The movie data (with selected features and added rating columns).
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

        full_data = response.json()
        self._extract_ratings(full_data)
        new_data = {key.upper(): full_data.get(key) for key in self.features}
        if "ROTTEN_TOMATOES_RATING" in full_data:
            new_data["ROTTEN_TOMATOES_RATING"] = full_data["ROTTEN_TOMATOES_RATING"]
        if "META_CRITIC_RATING" in full_data:
            new_data["META_CRITIC_RATING"] = full_data["META_CRITIC_RATING"]

        movie_title = new_data.get("TITLE") or title
        sanitized_title = self._sanitize_filename(movie_title)
        file_name = f"{sanitized_title}.csv"
        save_to_csv(new_data, file_name, "./data/omdb")
        print(f'{file_name} saved.')
        time.sleep(self.delay)
        return new_data

    def get_multiple_movies(self, imdb_ids: List[str], output_file_name: str = '01_omdb_movies.csv') -> None:
        """
        Retrieves movie data for a list of IMDb IDs, aggregates the results,
        prints progress, and saves them to a CSV file.

        Args:
            imdb_ids (List[str]): A list of IMDb IDs.
            output_file_name (str): The CSV filename for aggregated movie data.

        Returns:
            None
        """
        all_data: List[Dict] = []
        total = len(imdb_ids)
        for idx, imdb_id in enumerate(imdb_ids, start=1):
            data = self.get_movie_by_imdb_id(imdb_id)
            if data:
                all_data.append(data)
            print(f"Processed {idx}/{total} movies")
        save_to_csv(all_data, output_file_name, "./data/omdb")
        return all_data

# Example usage:
if __name__ == "__main__":
    from config.config_loader import load_config

    # Fetch the API key from your configuration.
    api_key = load_config("OMDB_API_KEY")
    omdb_client = OMDBClient(api_key=api_key, delay=0.1)

    # Test fetching by title:
    # movie_by_title = omdb_client.get_movie_by_title("The Shawshank Redemption", year=1994)
    # print(movie_by_title)

    # Test fetching by IMDb ID:
    movie_by_id = omdb_client.get_movie_by_imdb_id("tt0111161")
    print(movie_by_id)

    # Test fetching multiple movies:
    # imdb_ids = ["tt0111161", "tt0068646", "tt0071562"]
    # movies = omdb_client.get_multiple_movies(imdb_ids)
    # print(movies)

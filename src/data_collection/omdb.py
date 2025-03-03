import time
import re
import requests
from typing import Optional, List, Dict
from src.utils.utils import save_to_csv, store_to_csv
from database.utils import clean_na


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


    def get_movie_by_imdb_id(self, imdb_id: str, save_to_file=False) -> Dict:
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

        # If user want data to be saved to a csv
        if save_to_file:
            movie_title = new_data.get("TITLE")
            sanitized_title = self._sanitize_filename(movie_title)
            file_name = f"{sanitized_title}.csv"
            # save_to_csv(new_data, file_name, "./data/omdb")
            store_to_csv(new_data, file_name, "./data/omdb")

        time.sleep(self.delay)
        return new_data


    def get_movie_by_title(self, title: str, year: Optional[int] = None, save_to_file=False) -> Dict:
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

        # If user want data to be saved to a csv
        if save_to_file:
            movie_title = new_data.get("TITLE") or title
            sanitized_title = self._sanitize_filename(movie_title)
            file_name = f"{sanitized_title}.csv"
            save_to_csv(new_data, file_name, "./data/omdb")

        time.sleep(self.delay)
        return new_data


    def get_multiple_movies(self, imdb_ids: List[str], save_to_file: bool = False, output_file_name: str = '01_omdb_movies.csv') -> List[Dict]:
        """
        Retrieves movie data for a list of IMDb IDs, aggregates the results,
        prints progress, cleans the data (replacing 'N/A' with None), and saves them to a CSV file.
        
        Args:
            imdb_ids (List[str]): A list of IMDb IDs.
            save_to_file (bool): Whether to save the result to a CSV file.
            output_file_name (str): The CSV filename for aggregated movie data.
        
        Returns:
            List[Dict]: The cleaned list of movie data dictionaries.
        """
        all_data: List[Dict] = []
        total = len(imdb_ids)
        for idx, imdb_id in enumerate(imdb_ids, start=1):
            data = self.get_movie_by_imdb_id(imdb_id)
            if data:
                all_data.append(data)
            print(f"Processed {idx}/{total} movies")
        
        # Clean the data: replace any "N/A" with None.
        cleaned_data = [clean_na(item) for item in all_data]
        
        if save_to_file:
            save_to_csv(cleaned_data, output_file_name, "./data/omdb")
        
        return cleaned_data


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


    def parse_awards(awards_str: str):
        """
        Parses an awards string and extracts total wins, nominations, Oscar wins/nominations, and BAFTA wins/nominations.
        """
        if not awards_str or awards_str.strip().upper() == "N/A":
            return 0, 0, 0, 0, 0, 0

        total_wins = 0
        total_noms = 0
        oscar_wins = 0
        oscar_noms = 0
        bafta_wins = 0
        bafta_noms = 0

        # Look for total wins & nominations
        wins_match = re.search(r"(\d+)\s+wins?", awards_str, re.IGNORECASE)
        if wins_match:
            total_wins = int(wins_match.group(1))

        noms_match = re.search(r"(\d+)\s+nominations?", awards_str, re.IGNORECASE)
        if noms_match:
            total_noms = int(noms_match.group(1))

        # Look for Oscars
        oscar_noms_match = re.search(r"Nominated for (\d+) Oscars?", awards_str, re.IGNORECASE)
        if oscar_noms_match:
            oscar_noms = int(oscar_noms_match.group(1))

        oscar_wins_match = re.search(r"(\d+) wins?.*Oscars?", awards_str, re.IGNORECASE)
        if oscar_wins_match:
            oscar_wins = int(oscar_wins_match.group(1))

        # Look for BAFTAs
        bafta_noms_match = re.search(r"Nominated for (\d+) BAFTA", awards_str, re.IGNORECASE)
        if bafta_noms_match:
            bafta_noms = int(bafta_noms_match.group(1))

        bafta_wins_match = re.search(r"(\d+) wins?.*BAFTA", awards_str, re.IGNORECASE)
        if bafta_wins_match:
            bafta_wins = int(bafta_wins_match.group(1))

        return total_wins, total_noms, oscar_wins, oscar_noms, bafta_wins, bafta_noms


    def save_multiple_movies_to_db(self, movies: List[Dict], session) -> None:
        """
        Saves a list of movie feature dictionaries to the PostgreSQL database using SQLAlchemy.
        
        This method manually checks for an existing record in the OMDB movies table (03_omdb_movies)
        based on the imdb_id. If found, it updates the record; if not, it inserts a new record.
        It also converts numeric fields from the API (which may contain "N/A") to None.
        
        Args:
            movies (List[Dict]): List of movie feature dictionaries as produced by the OMDBClient API methods.
            session: An active SQLAlchemy session.
        
        Returns:
            None
        """
        from database.models import OMDBMovie  # Ensure this import matches your project structure

        merged_count = 0
        updated_count = 0
        inserted_count = 0

        for movie_data in movies:
            imdb_id = movie_data.get("IMDBID")
            if not imdb_id:
                continue  # Skip records without an IMDb ID

            # Convert numeric fields:
            # Convert YEAR to int if possible.
            year_val = movie_data.get("YEAR")
            if year_val and year_val != "N/A":
                try:
                    year_val = int(year_val)
                except ValueError:
                    year_val = None
            else:
                year_val = None

            # Convert IMDBRATING to float.
            imdb_rating_val = movie_data.get("IMDBRATING")
            if imdb_rating_val and imdb_rating_val != "N/A":
                try:
                    imdb_rating_val = float(imdb_rating_val)
                except ValueError:
                    imdb_rating_val = None
            else:
                imdb_rating_val = None

            # Convert METASCORE to int.
            metascore_val = movie_data.get("METASCORE")
            if metascore_val and metascore_val != "N/A":
                try:
                    metascore_val = int(metascore_val)
                except ValueError:
                    metascore_val = None
            else:
                metascore_val = None

            # Clean Rotten Tomatoes rating: remove '%' and convert to int.
            rt_rating_val = movie_data.get("ROTTEN_TOMATOES_RATING")
            if rt_rating_val and rt_rating_val != "N/A" and rt_rating_val.endswith("%"):
                try:
                    rt_rating_val = int(rt_rating_val.rstrip("%"))
                except ValueError:
                    rt_rating_val = None
            else:
                rt_rating_val = None

             # Clean BOXOFFICE: remove '$' and commas, then convert to int.
            box_office_val = movie_data.get("BOXOFFICE")
            if box_office_val and box_office_val != "N/A":
                try:
                    # Remove dollar sign and commas
                    box_office_val = box_office_val.replace("$", "").replace(",", "")
                    box_office_val = int(box_office_val)
                except ValueError:
                    box_office_val = None
            else:
                box_office_val = None

            # Clean Meta Critic rating: take the number before '/' and convert to int.
            meta_rating_val = movie_data.get("META_CRITIC_RATING")
            if meta_rating_val and meta_rating_val != "N/A" and "/" in meta_rating_val:
                try:
                    meta_rating_val = int(meta_rating_val.split('/')[0])
                except ValueError:
                    meta_rating_val = None
            else:
                meta_rating_val = None

            # Convert RUNTIME to int by extracting the numeric part.
            runtime_val = movie_data.get("RUNTIME")
            if runtime_val and runtime_val != "N/A":
                try:
                    # Assumes runtime is like "132 min"
                    runtime_val = int(runtime_val.split()[0])
                except ValueError:
                    runtime_val = None
            else:
                runtime_val = None

            # Check if the movie already exists in the database.
            existing_movie = session.query(OMDBMovie).filter_by(imdb_id=imdb_id).first()

            if existing_movie:
                # Update the existing record
                for key, value in movie_data.items():
                    attr_name = key.lower()  # Ensure attribute case consistency
                    if hasattr(existing_movie, attr_name):
                        setattr(existing_movie, attr_name, value)
                updated_count += 1
            else:
                # Insert a new record.
                new_movie = OMDBMovie(
                    imdb_id=imdb_id,
                    title=movie_data.get("TITLE"),
                    year=year_val,
                    genre=movie_data.get("GENRE"),
                    director=movie_data.get("DIRECTOR"),
                    writer=movie_data.get("WRITER"),
                    actors=movie_data.get("ACTORS"),
                    imdb_rating=imdb_rating_val,
                    imdb_votes=movie_data.get("IMDBVOTES"),
                    metascore=metascore_val,
                    box_office=box_office_val,
                    released=movie_data.get("RELEASED"),
                    runtime=movie_data.get("RUNTIME"),
                    language=movie_data.get("LANGUAGE"),
                    country=movie_data.get("COUNTRY"),
                    rated=movie_data.get("RATED"),
                    awards=movie_data.get("AWARDS"),
                    rotten_tomatoes_rating=rt_rating_val,
                    meta_critic_rating=meta_rating_val
                )
                session.add(new_movie)
                inserted_count += 1

            merged_count += 1

        session.commit()
        print(f"Merged {merged_count} movies: {updated_count} updated, {inserted_count} inserted.")




# Example usage:
if __name__ == "__main__":
    from config.config_loader import load_config

    # Fetch the API key from your configuration.
    api_key = load_config("OMDB_API_KEY")
    omdb_client = OMDBClient(api_key=api_key, delay=0.1)

    # Test fetching by title:
    # movie_by_title = omdb_client.get_movie_by_title("The Shawshank Redemption", year=1994, save_to_file=True)
    # print(movie_by_title)

    # Test fetching by IMDb ID:
    # movie_by_id = omdb_client.get_movie_by_imdb_id("tt0111161", save_to_file=True)
    # print(movie_by_id)

    # Test fetching multiple movies:
    imdb_ids = ["tt0111161", "tt0068646", "tt0071562"]
    movies = omdb_client.get_multiple_movies(imdb_ids=imdb_ids, save_to_file=True)
    print(movies)
    omdb_client.save_multiple_movies_to_db(movies, session)

    # Test saving multiple movies to the database:
    

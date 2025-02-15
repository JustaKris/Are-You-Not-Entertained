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
    
    def fetch_tmdb_data(self, endpoint: str, features: Optional[List[str]] = None, total_pages: Optional[int] = None, save_to_file: bool = False, output_file_name: str = 'default.csv') -> None:
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
        if save_to_file:
            save_to_csv(all_data, output_file_name, "./data/tmdb")

        return all_data
    
    
    def get_movie_ids(self, start_year: int = 2025, min_vote_count: int = 350, save_to_file: bool = False, output_file_name: str = '01_movie_ids.csv') -> None:
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
        data = self.fetch_tmdb_data(endpoint=endpoint, features=features, save_to_file=True if save_to_file else False, output_file_name=output_file_name)
        return data

    
    def get_movie_features(self, movie_ids: List[int], save_to_file: bool = False, output_file_name: str = '02_movie_features.csv') -> None:
        """
        Retrieves detailed movie features for each movie ID in the provided list.
        
        This method iterates over the list of movie IDs and, for each ID, retrieves detailed movie data
        from the TMDB API using the 'movie/{movie_id}' endpoint. It processes special features:
        
        - For 'genres': extracts both 'id' and 'name' as GENRE_ID and GENRE_NAME (comma-separated).
        - For 'production_companies': extracts 'id', 'name', and 'origin_country' as 
            PRODUCTION_COMPANY_ID, PRODUCTION_COMPANY_NAME, and PRODUCTION_COMPANY_ORIGIN_COUNTRY (comma-separated).
        - For 'production_countries': extracts only the 'name' as PRODUCTION_COUNTRY_NAME (comma-separated).
        - For 'spoken_languages': extracts only the 'english_name' as SPOKEN_LANGUAGES (comma-separated).
        
        All other features are retained as-is (with keys uppercased).
        
        The aggregated data is saved to a CSV file in the "./data/tmdb" directory.
        
        Args:
            movie_ids (List[int]): A list of movie IDs for which to retrieve details.
            output_file_name (str): The name of the CSV file where the movie features data will be saved.
        
        Returns:
            None
        """
        # Hard-coded list of features to extract (including the ones with special processing)
        features = [
            "id", "imdb_id", "genres", "release_date", "status", "title", "budget", "revenue", "runtime", "vote_count", "vote_average", 
            "popularity", "production_companies", "production_countries", "spoken_languages", 
            # "tagline", "belongs_to_collection", "original_title", "overview", 
        ]

        all_data: List[Dict] = []
        total_movies = len(movie_ids)
        
        for idx, movie_id in enumerate(movie_ids, start=1):
            url = f"{self.base_url}movie/{movie_id}"
            try:
                response = self.session.get(url)
                response.raise_for_status()
            except requests.RequestException as e:
                logging.error(f"Failed to fetch data for movie ID {movie_id}: {e}")
                continue

            movie_data = response.json()
            filtered_movie_data = {}
            
            for key in features:
                # Special processing for complex features:
                if key == "genres":
                    genres_list = movie_data.get("genres", [])
                    genre_ids = [str(item.get("id", "")) for item in genres_list]
                    genre_names = [item.get("name", "") for item in genres_list]
                    filtered_movie_data["GENRE_ID"] = ", ".join(genre_ids)
                    filtered_movie_data["GENRE_NAME"] = ", ".join(genre_names)
                elif key == "production_companies":
                    companies_list = movie_data.get("production_companies", [])
                    company_ids = [str(item.get("id", "")) for item in companies_list]
                    company_names = [item.get("name", "") for item in companies_list]
                    company_origins = [item.get("origin_country", "") for item in companies_list]
                    filtered_movie_data["PRODUCTION_COMPANY_ID"] = ", ".join(company_ids)
                    filtered_movie_data["PRODUCTION_COMPANY_NAME"] = ", ".join(company_names)
                    filtered_movie_data["PRODUCTION_COMPANY_ORIGIN_COUNTRY"] = ", ".join(company_origins)
                elif key == "production_countries":
                    countries_list = movie_data.get("production_countries", [])
                    country_names = [item.get("name", "") for item in countries_list]
                    filtered_movie_data["PRODUCTION_COUNTRY_NAME"] = ", ".join(country_names)
                elif key == "spoken_languages":
                    languages_list = movie_data.get("spoken_languages", [])
                    english_names = [item.get("english_name", "") for item in languages_list]
                    filtered_movie_data["SPOKEN_LANGUAGES"] = ", ".join(english_names)
                else:
                    filtered_movie_data[key.upper()] = movie_data.get(key)
            
            all_data.append(filtered_movie_data)
            logging.info(f"Fetched movie {idx}/{total_movies}: ID {movie_id}")
            time.sleep(self.delay)

        # Save the aggregated movie details to a CSV file in the "./data/tmdb" directory
        if save_to_file:
            save_to_csv(all_data, output_file_name, "./data/tmdb")
        return all_data


    # def save_movies_to_db(self, movies: List[Dict], session) -> None:
    #     """
    #     Saves a list of movie dictionaries to the PostgreSQL database using SQLAlchemy.
        
    #     Args:
    #         movies (List[Dict]): List of movie data dictionaries.
    #         session: An SQLAlchemy session.
        
    #     Returns:
    #         None
    #     """
    #     from database.models import TMDBMovieBase  # Import the Movie model defined earlier.

    #     merged_count = 0
    #     for movie_data in movies:
    #         # Map the movie_data dictionary to the Movie model.
    #         # Adjust field names as necessary.
    #         movie = TMDBMovieBase(
    #             tmdb_id=movie_data.get("ID"),
    #             title=movie_data.get("TITLE"),
    #             release_date=movie_data.get("RELEASE_DATE"),
    #             vote_count=movie_data.get("VOTE_COUNT"),
    #             vote_average=movie_data.get("VOTE_AVERAGE"),
    #             genre_ids=movie_data.get("GENRE_IDS") or movie_data.get("GENRE_ID")  # Example fallback
    #             # ... assign other fields as needed.
    #         )
    #         # Wrap merge in a no_autoflush block to avoid premature flushing.
    #         session.merge(movie)
    #         merged_count += 1

    #     session.commit()
    #     print(f"Merged {merged_count} movie ids into the database.")


    def save_movies_to_db(self, movies: List[Dict], session) -> None:
        """
        Saves a list of movie dictionaries to the PostgreSQL database using SQLAlchemy.
        
        Args:
            movies (List[Dict]): List of movie data dictionaries.
            session: An SQLAlchemy session.
        
        Returns:
            None
        """
        from database.db_tables import TMDBMovieBase  # Import the Movie model defined earlier.

        merged_count = 0
        updated_count = 0
        inserted_count = 0

        for movie_data in movies:
            # Extract movie attributes
            tmdb_id = movie_data.get("ID")
            
            # Check if the movie already exists in the database
            existing_movie = session.query(TMDBMovieBase).filter_by(tmdb_id=tmdb_id).first()
            
            if existing_movie:
                # Update the existing record
                for key, value in movie_data.items():
                    if hasattr(existing_movie, key.lower()):  # Ensure attribute exists
                        setattr(existing_movie, key.lower(), value)
                updated_count += 1
            else:
                # Insert a new record
                new_movie = TMDBMovieBase(
                    tmdb_id=tmdb_id,
                    title=movie_data.get("TITLE"),
                    release_date=movie_data.get("RELEASE_DATE"),
                    vote_count=movie_data.get("VOTE_COUNT"),
                    vote_average=movie_data.get("VOTE_AVERAGE"),
                    genre_ids=movie_data.get("GENRE_IDS") or movie_data.get("GENRE_ID")
                )
                session.add(new_movie)
                inserted_count += 1

            merged_count += 1

        session.commit()
        print(f"Merged {merged_count} movies: {updated_count} updated, {inserted_count} inserted.")


    def save_movie_features_to_db(self, movies: List[Dict], session) -> None:
        """
        Saves a list of movie feature dictionaries to the PostgreSQL database using SQLAlchemy.
        
        This method manually checks for existing records in the database and updates them if found.
        Otherwise, it inserts a new record.
        
        Args:
            movies (List[Dict]): List of movie features (each a dict) as produced by get_movie_features.
            session: An active SQLAlchemy session.
        
        Returns:
            None
        """
        from database.db_tables import TMDBMovie  # Ensure this is the correct model import

        merged_count = 0
        updated_count = 0
        inserted_count = 0

        for movie_data in movies:
            tmdb_id = movie_data.get("ID")
            
            if not tmdb_id:
                continue  # Skip entries without an ID

            # Check if the movie already exists in the database
            existing_movie = session.query(TMDBMovie).filter_by(tmdb_id=tmdb_id).first()
            
            if existing_movie:
                # Update the existing record
                for key, value in movie_data.items():
                    attr_name = key.lower()  # Ensure attribute case consistency
                    if hasattr(existing_movie, attr_name):
                        setattr(existing_movie, attr_name, value)
                updated_count += 1
            else:
                # Insert a new record
                new_movie = TMDBMovie(
                    tmdb_id=tmdb_id,
                    imdb_id=movie_data.get("IMDB_ID"),
                    genre_id=movie_data.get("GENRE_ID"),
                    genre_name=movie_data.get("GENRE_NAME"),
                    release_date=movie_data.get("RELEASE_DATE"),
                    status=movie_data.get("STATUS"),
                    title=movie_data.get("TITLE"),
                    budget=movie_data.get("BUDGET"),
                    revenue=movie_data.get("REVENUE"),
                    runtime=movie_data.get("RUNTIME"),
                    vote_count=movie_data.get("VOTE_COUNT"),
                    vote_average=movie_data.get("VOTE_AVERAGE"),
                    popularity=movie_data.get("POPULARITY"),
                    production_company_id=movie_data.get("PRODUCTION_COMPANY_ID"),
                    production_company_name=movie_data.get("PRODUCTION_COMPANY_NAME"),
                    production_company_origin_country=movie_data.get("PRODUCTION_COMPANY_ORIGIN_COUNTRY"),
                    production_country_name=movie_data.get("PRODUCTION_COUNTRY_NAME"),
                    spoken_languages=movie_data.get("SPOKEN_LANGUAGES")
                )
                session.add(new_movie)
                inserted_count += 1

            merged_count += 1

        session.commit()
        print(f"Merged {merged_count} movie features: {updated_count} updated, {inserted_count} inserted.")



if __name__ == "__main__":
    from config.config_loader import load_config
    from src.utils import load_csv

   # Load API key
    TMDB_API_KEY = load_config("TMDB_API_KEY")

    # Initialize the TMDB client
    tmdb_client = TMDBClient(api_key=TMDB_API_KEY)
    
    # Get movie IDs (and associated features)
    tmdb_client.get_movie_ids(start_year=2024, min_vote_count=350)

    # Get movie features
    movie_ids = load_csv("01_movie_ids.csv")["ID"].tolist()
    tmdb_client.get_movie_features(movie_ids)

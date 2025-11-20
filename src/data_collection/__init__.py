"""Data collection services for TMDB, OMDB, and The Numbers.

Modern service-oriented structure:
- tmdb/: TMDB API client
- omdb/: OMDB API client  
- the_numbers/: Web scraping for box office data

Usage:
    from src.data_collection.tmdb import TMDBClient
    from src.data_collection.omdb import OMDBClient
    from src.data_collection.the_numbers import scrape_the_numbers
"""

# Import clients for convenient access
from .tmdb import TMDBClient
from .omdb import OMDBClient
from .the_numbers import scrape_the_numbers

__all__ = ["TMDBClient", "OMDBClient", "scrape_the_numbers"]

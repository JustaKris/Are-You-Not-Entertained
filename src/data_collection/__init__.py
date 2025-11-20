"""Data collection services for TMDB, OMDB, and The Numbers.

Modern service-oriented structure:
- tmdb/: TMDB API client (async with rate limiting)
- omdb/: OMDB API client (async with rate limiting)
- the_numbers/: Web scraping for box office data
- orchestrator: Intelligent data collection coordinator
- refresh_strategy: Age-based refresh logic
- rate_limiter: Shared rate limiting utilities

Usage:
    from src.data_collection.tmdb import TMDBClient
    from src.data_collection.omdb import OMDBClient
    from src.data_collection.orchestrator import DataCollectionOrchestrator
    from src.data_collection.the_numbers import scrape_the_numbers
"""

# Import clients for convenient access
from .tmdb import TMDBClient
from .omdb import OMDBClient
from .the_numbers import scrape_the_numbers
from .orchestrator import DataCollectionOrchestrator
from .refresh_strategy import (
    MovieAge,
    RefreshThresholds,
    get_movie_age,
    calculate_refresh_plan
)

__all__ = [
    "TMDBClient",
    "OMDBClient",
    "scrape_the_numbers",
    "DataCollectionOrchestrator",
    "MovieAge",
    "RefreshThresholds",
    "get_movie_age",
    "calculate_refresh_plan"
]

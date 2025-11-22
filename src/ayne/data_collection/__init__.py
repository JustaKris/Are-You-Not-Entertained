"""Data collection services for TMDB, OMDB, and The Numbers.

Modern service-oriented structure:
- tmdb/: TMDB API client (async with rate limiting)
- omdb/: OMDB API client (async with rate limiting)
- the_numbers/: Web scraping for box office data
- orchestrator: Intelligent data collection coordinator
- refresh_strategy: Age-based refresh logic
- rate_limiter: Shared rate limiting utilities

Usage:
    from ayne.data_collection.tmdb import TMDBClient
    from ayne.data_collection.omdb import OMDBClient
    from ayne.data_collection.orchestrator import DataCollectionOrchestrator
    from ayne.data_collection.the_numbers import scrape_the_numbers
"""

# Import clients for convenient access
from .omdb import OMDBClient
from .orchestrator import DataCollectionOrchestrator
from .refresh_strategy import MovieAge, RefreshThresholds, calculate_refresh_plan, get_movie_age
from .the_numbers import scrape_the_numbers
from .tmdb import TMDBClient

__all__ = [
    "TMDBClient",
    "OMDBClient",
    "scrape_the_numbers",
    "DataCollectionOrchestrator",
    "MovieAge",
    "RefreshThresholds",
    "get_movie_age",
    "calculate_refresh_plan",
]

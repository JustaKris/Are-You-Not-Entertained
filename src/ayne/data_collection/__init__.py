"""Data collection services for TMDB, OMDB, and The Numbers.

Modern service-oriented structure:
- tmdb/: TMDB API client (async with rate limiting)
- omdb/: OMDB API client (async with rate limiting)
- the_numbers/: Async, rate-limited box office scraping client
- orchestrator: Intelligent data collection coordinator
- refresh_strategy: Age-based refresh logic
- rate_limiter: Shared rate limiting utilities

Usage:
    from ayne.data_collection.tmdb import TMDBClient
    from ayne.data_collection.omdb import OMDBClient
    from ayne.data_collection.the_numbers import TheNumbersClient
    from ayne.data_collection.orchestrator import DataCollectionOrchestrator
"""

# Import clients for convenient access
from .omdb import OMDBClient
from .orchestrator import DataCollectionOrchestrator
from .refresh_strategy import MovieAge, RefreshThresholds, calculate_refresh_plan, get_movie_age
from .the_numbers import TheNumbersClient
from .tmdb import TMDBClient

__all__ = [
    "DataCollectionOrchestrator",
    "MovieAge",
    "OMDBClient",
    "RefreshThresholds",
    "TMDBClient",
    "TheNumbersClient",
    "calculate_refresh_plan",
    "get_movie_age",
]

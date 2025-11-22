"""TMDB API client module."""

from .client import TMDBClient
from .models import (
    TMDBDiscoverMovie,
    TMDBDiscoverMovieNormalized,
    TMDBMovieDetails,
    TMDBMovieDetailsNormalized,
)
from .normalizers import normalize_discover_results, normalize_movie_details

__all__ = [
    "TMDBClient",
    "TMDBDiscoverMovie",
    "TMDBMovieDetails",
    "TMDBDiscoverMovieNormalized",
    "TMDBMovieDetailsNormalized",
    "normalize_discover_results",
    "normalize_movie_details",
]

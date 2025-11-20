"""OMDB API client module."""

from .client import OMDBClient
from .models import (
    OMDBMovieResponse,
    OMDBMovieNormalized
)
from .normalizers import normalize_movie_response

__all__ = [
    "OMDBClient",
    "OMDBMovieResponse",
    "OMDBMovieNormalized",
    "normalize_movie_response"
]

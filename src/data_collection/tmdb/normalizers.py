"""Normalizers for TMDB API responses."""

from typing import List, Dict, Any
from datetime import datetime, timezone

from .models import (
    TMDBDiscoverMovie,
    TMDBMovieDetails,
    TMDBDiscoverMovieNormalized,
    TMDBMovieDetailsNormalized
)


def utc_now() -> str:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def normalize_discover_results(movies: List[Dict]) -> List[Dict[str, Any]]:
    """
    Normalize TMDB discover API response to storage format.
    
    Args:
        movies: Raw movie dictionaries from TMDB discover API
        
    Returns:
        List of normalized movie dictionaries ready for storage
    """
    normalized = []
    timestamp = utc_now()
    
    for movie_data in movies:
        # Parse with Pydantic for validation
        movie = TMDBDiscoverMovie(**movie_data)
        
        # Convert to normalized storage format
        normalized_movie = TMDBDiscoverMovieNormalized(
            tmdb_id=movie.tmdb_id,
            title=movie.title,
            release_date=movie.release_date,
            vote_count=movie.vote_count,
            vote_average=movie.vote_average,
            popularity=movie.popularity,
            genre_ids=",".join(map(str, movie.genre_ids)),
            last_updated_utc=timestamp
        )
        
        normalized.append(normalized_movie.model_dump())
    
    return normalized


def normalize_movie_details(movie_data: Dict) -> Dict[str, Any]:
    """
    Normalize TMDB movie details API response to storage format.
    
    Args:
        movie_data: Raw movie dictionary from TMDB details API
        
    Returns:
        Normalized movie dictionary ready for storage
    """
    # Parse with Pydantic for validation
    movie = TMDBMovieDetails(**movie_data)
    
    # Convert to normalized storage format
    normalized_movie = TMDBMovieDetailsNormalized(
        tmdb_id=movie.id,
        imdb_id=movie.imdb_id,
        title=movie.title,
        release_date=movie.release_date,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        runtime=movie.runtime,
        vote_count=movie.vote_count,
        vote_average=movie.vote_average,
        popularity=movie.popularity,
        genres=",".join([g.name for g in movie.genres]),
        production_companies=",".join([c.name for c in movie.production_companies]),
        production_countries=",".join([c.name for c in movie.production_countries]),
        spoken_languages=",".join([lang.english_name for lang in movie.spoken_languages]),
        overview=movie.overview,
        last_updated_utc=utc_now()
    )
    
    return normalized_movie.model_dump()

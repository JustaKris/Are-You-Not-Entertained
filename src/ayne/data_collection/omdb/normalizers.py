"""Normalizers for OMDB API responses."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .models import OMDBMovieNormalized, OMDBMovieResponse


def utc_now() -> str:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def clean_numeric(val: Any) -> Optional[Any]:
    """Clean numeric values, return None for N/A or empty."""
    if val in (None, "", "N/A"):
        return None
    return val


def clean_box_office(val: Optional[str]) -> Optional[int]:
    """Clean box office value from string like '$123,456,789' to integer.

    Args:
        val: Box office string from OMDB

    Returns:
        Integer value or None
    """
    if not val or val == "N/A":
        return None
    try:
        return int(val.replace("$", "").replace(",", ""))
    except Exception:
        return None


def clean_runtime(value: Optional[str]) -> Optional[int]:
    """Clean runtime value from string like '142 min' to integer.

    Args:
        value: Runtime string from OMDB

    Returns:
        Integer minutes or None
    """
    if not value or value == "N/A":
        return None
    try:
        return int(value.split()[0])
    except Exception:
        return None


def extract_ratings(movie: OMDBMovieResponse) -> tuple[Optional[int], Optional[int]]:
    """Extract Rotten Tomatoes and Metacritic ratings from OMDB ratings list.

    Args:
        movie: Parsed OMDB movie response

    Returns:
        Tuple of (rotten_tomatoes_rating, meta_critic_rating)
    """
    rotten_tomatoes = None
    meta_critic = None

    if not movie.Ratings:
        return rotten_tomatoes, meta_critic

    for rating in movie.Ratings:
        if rating.Source == "Rotten Tomatoes":
            # e.g. "85%"
            try:
                if rating.Value.endswith("%"):
                    rotten_tomatoes = int(rating.Value.rstrip("%"))
            except Exception:
                pass
        elif rating.Source == "Metacritic":
            # e.g. "76/100"
            try:
                if "/" in rating.Value:
                    meta_critic = int(rating.Value.split("/")[0])
            except Exception:
                pass

    return rotten_tomatoes, meta_critic


def normalize_movie_response(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Normalize OMDB API response to storage format.

    Args:
        data: Raw movie dictionary from OMDB API

    Returns:
        Normalized movie dictionary ready for storage, or None if response failed
    """
    # Parse with Pydantic for validation
    movie = OMDBMovieResponse(**data)

    # Check if the API returned an error
    if movie.Response == "False":
        return None

    # Extract ratings from the Ratings array
    rotten_tomatoes, meta_critic = extract_ratings(movie)

    # Parse numeric fields
    year = None
    if movie.Year and movie.Year.isdigit():
        year = int(movie.Year)

    imdb_rating = None
    if movie.imdbRating and movie.imdbRating.replace(".", "", 1).isdigit():
        imdb_rating = float(movie.imdbRating)

    imdb_votes = None
    if movie.imdbVotes:
        try:
            imdb_votes = int(movie.imdbVotes.replace(",", ""))
        except Exception:
            pass

    metascore = None
    if movie.Metascore and movie.Metascore.isdigit():
        metascore = int(movie.Metascore)

    # Create normalized model
    normalized = OMDBMovieNormalized(
        imdb_id=movie.imdbID,
        title=movie.Title,
        year=year,
        genre=movie.Genre,
        director=movie.Director,
        writer=movie.Writer,
        actors=movie.Actors,
        imdb_rating=imdb_rating,
        imdb_votes=imdb_votes,
        metascore=metascore,
        box_office=clean_box_office(movie.BoxOffice),
        released=movie.Released,
        runtime=clean_runtime(movie.Runtime),
        language=movie.Language,
        country=movie.Country,
        rated=movie.Rated,
        awards=movie.Awards,
        rotten_tomatoes_rating=rotten_tomatoes,
        meta_critic_rating=meta_critic,
        last_updated_utc=utc_now(),
    )

    return normalized.model_dump()

"""Pydantic models for OMDB API responses."""

from typing import List, Optional

from pydantic import BaseModel


class OMDBRating(BaseModel):
    """OMDB rating from external source."""

    Source: str
    Value: str


class OMDBMovieResponse(BaseModel):
    """Model for OMDB API full response."""

    Response: str
    imdbID: Optional[str] = None
    Title: Optional[str] = None
    Year: Optional[str] = None
    Genre: Optional[str] = None
    Director: Optional[str] = None
    Writer: Optional[str] = None
    Actors: Optional[str] = None
    imdbRating: Optional[str] = None
    imdbVotes: Optional[str] = None
    Metascore: Optional[str] = None
    BoxOffice: Optional[str] = None
    Released: Optional[str] = None
    Runtime: Optional[str] = None
    Language: Optional[str] = None
    Country: Optional[str] = None
    Rated: Optional[str] = None
    Awards: Optional[str] = None
    Ratings: Optional[List[OMDBRating]] = None
    Error: Optional[str] = None

    class Config:
        """Pydantic config for field aliasing."""

        populate_by_name = True


class OMDBMovieNormalized(BaseModel):
    """Normalized OMDB movie for storage."""

    imdb_id: Optional[str]
    title: Optional[str]
    year: Optional[int]
    genre: Optional[str]
    director: Optional[str]
    writer: Optional[str]
    actors: Optional[str]
    imdb_rating: Optional[float]
    imdb_votes: Optional[int]
    metascore: Optional[int]
    box_office: Optional[int]
    released: Optional[str]
    runtime: Optional[int]
    language: Optional[str]
    country: Optional[str]
    rated: Optional[str]
    awards: Optional[str]
    rotten_tomatoes_rating: Optional[int]
    meta_critic_rating: Optional[int]
    last_updated_utc: str

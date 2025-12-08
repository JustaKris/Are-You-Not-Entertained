"""Pydantic models for OMDB API responses."""

from pydantic import BaseModel


class OMDBRating(BaseModel):
    """OMDB rating from external source."""

    Source: str
    Value: str


class OMDBMovieResponse(BaseModel):
    """Model for OMDB API full response."""

    Response: str
    imdbID: str | None = None
    Title: str | None = None
    Year: str | None = None
    Genre: str | None = None
    Director: str | None = None
    Writer: str | None = None
    Actors: str | None = None
    imdbRating: str | None = None
    imdbVotes: str | None = None
    Metascore: str | None = None
    BoxOffice: str | None = None
    Released: str | None = None
    Runtime: str | None = None
    Language: str | None = None
    Country: str | None = None
    Rated: str | None = None
    Awards: str | None = None
    Ratings: list[OMDBRating] | None = None
    Error: str | None = None

    class Config:
        """Pydantic config for field aliasing."""

        populate_by_name = True


class OMDBMovieNormalized(BaseModel):
    """Normalized OMDB movie for storage."""

    imdb_id: str | None
    title: str | None
    year: int | None
    genre: str | None
    director: str | None
    writer: str | None
    actors: str | None
    imdb_rating: float | None
    imdb_votes: int | None
    metascore: int | None
    box_office: int | None
    released: str | None
    runtime: int | None
    language: str | None
    country: str | None
    rated: str | None
    awards: str | None
    rotten_tomatoes_rating: int | None
    meta_critic_rating: int | None
    last_updated_utc: str

"""Pydantic models for TMDB API responses."""

from pydantic import BaseModel, Field


class TMDBDiscoverMovie(BaseModel):
    """Model for TMDB discover API response movie item."""

    tmdb_id: int = Field(..., alias="id")
    title: str
    release_date: str | None = None
    vote_count: int
    vote_average: float
    popularity: float
    genre_ids: list[int]

    class Config:
        """Pydantic config for field aliasing."""

        populate_by_name = True


class TMDBGenre(BaseModel):
    """TMDB genre object."""

    id: int
    name: str


class TMDBProductionCompany(BaseModel):
    """TMDB production company object."""

    id: int
    name: str
    logo_path: str | None = None
    origin_country: str


class TMDBProductionCountry(BaseModel):
    """TMDB production country object."""

    iso_3166_1: str
    name: str


class TMDBSpokenLanguage(BaseModel):
    """TMDB spoken language object."""

    english_name: str
    iso_639_1: str
    name: str


class TMDBMovieDetails(BaseModel):
    """Model for TMDB movie details API response."""

    id: int
    imdb_id: str | None = None
    title: str
    release_date: str | None = None
    status: str
    budget: int
    revenue: int
    runtime: int | None = None
    vote_count: int
    vote_average: float
    popularity: float
    genres: list[TMDBGenre]
    production_companies: list[TMDBProductionCompany]
    production_countries: list[TMDBProductionCountry]
    spoken_languages: list[TMDBSpokenLanguage]
    overview: str | None = None

    class Config:
        """Pydantic config for field aliasing."""

        populate_by_name = True


class TMDBDiscoverMovieNormalized(BaseModel):
    """Normalized TMDB discover movie for storage."""

    tmdb_id: int
    title: str
    release_date: str | None
    vote_count: int
    vote_average: float
    popularity: float
    genre_ids: str  # Comma-separated
    last_updated_utc: str


class TMDBMovieDetailsNormalized(BaseModel):
    """Normalized TMDB movie details for storage."""

    tmdb_id: int
    imdb_id: str | None
    title: str
    release_date: str | None
    status: str
    budget: int
    revenue: int
    runtime: int | None
    vote_count: int
    vote_average: float
    popularity: float
    genres: str  # Comma-separated
    production_companies: str  # Comma-separated
    production_countries: str  # Comma-separated
    spoken_languages: str  # Comma-separated
    overview: str | None
    last_updated_utc: str

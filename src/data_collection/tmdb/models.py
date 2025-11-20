"""Pydantic models for TMDB API responses."""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class TMDBDiscoverMovie(BaseModel):
    """Model for TMDB discover API response movie item."""
    
    tmdb_id: int = Field(..., alias="id")
    title: str
    release_date: Optional[str] = None
    vote_count: int
    vote_average: float
    popularity: float
    genre_ids: List[int]
    
    class Config:
        populate_by_name = True


class TMDBGenre(BaseModel):
    """TMDB genre object."""
    id: int
    name: str


class TMDBProductionCompany(BaseModel):
    """TMDB production company object."""
    id: int
    name: str
    logo_path: Optional[str] = None
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
    imdb_id: Optional[str] = None
    title: str
    release_date: Optional[str] = None
    status: str
    budget: int
    revenue: int
    runtime: Optional[int] = None
    vote_count: int
    vote_average: float
    popularity: float
    genres: List[TMDBGenre]
    production_companies: List[TMDBProductionCompany]
    production_countries: List[TMDBProductionCountry]
    spoken_languages: List[TMDBSpokenLanguage]
    overview: Optional[str] = None
    
    class Config:
        populate_by_name = True


class TMDBDiscoverMovieNormalized(BaseModel):
    """Normalized TMDB discover movie for storage."""
    
    tmdb_id: int
    title: str
    release_date: Optional[str]
    vote_count: int
    vote_average: float
    popularity: float
    genre_ids: str  # Comma-separated
    last_updated_utc: str


class TMDBMovieDetailsNormalized(BaseModel):
    """Normalized TMDB movie details for storage."""
    
    tmdb_id: int
    imdb_id: Optional[str]
    title: str
    release_date: Optional[str]
    status: str
    budget: int
    revenue: int
    runtime: Optional[int]
    vote_count: int
    vote_average: float
    popularity: float
    genres: str  # Comma-separated
    production_companies: str  # Comma-separated
    production_countries: str  # Comma-separated
    spoken_languages: str  # Comma-separated
    overview: Optional[str]
    last_updated_utc: str

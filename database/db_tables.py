from datetime import datetime
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, BigInteger, DateTime, Date


class Base(DeclarativeBase):
    pass


class TMDBMovieBase(Base):
    """
    TMDBMovieBase is an ORM model representing the base table for storing TMDB movie data.
    
    This table stores essential information about movies fetched from TMDB,
    such as title, release date, vote counts, and average rating. Additional
    columns (e.g., for genres, revenue, ratings) can be added as needed.
    """
    __tablename__ = '01_tmdb_movies_base'
    
    # Auto-generated primary key for the local database table.
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Features fetched from the TMDB API.
    tmdb_id = Column(Integer, nullable=True, unique=True)
    title = Column(String, nullable=False)
    release_date = Column(Date, nullable=True)
    vote_count = Column(Integer, nullable=True)
    vote_average = Column(Float, nullable=True)
    genre_ids = Column(Text)
    
    def __repr__(self) -> str:
        """
        Returns a string representation of the TMDBMovieBase instance,
        which is useful for debugging.
        """
        return (f"<TMDBMovieBase(id={self.id}, tmdb_id={self.tmdb_id}, "
                f"title='{self.title}', release_date='{self.release_date}')>")
    
    def as_dict(self) -> dict:
        """
        Returns a dictionary representation of the model instance.
        
        This can be useful when you need to convert the object to JSON,
        debug the model, or perform data serialization.
        """
        return {
            'id': self.id,
            'tmdb_id': self.tmdb_id,
            'title': self.title,
            'release_date': self.release_date,
            'vote_count': self.vote_count,
            'vote_average': self.vote_average,
            'genre_ids': self.genre_ids,
        }
    
    def update_from_dict(self, data: dict):
        """
        Updates the model instance with values provided in a dictionary.
        
        Only keys that match the model's attributes will be updated.
        This is useful for dynamic updates or merging API data into the model.
        
        Args:
            data (dict): A dictionary where keys correspond to attribute names.
        """
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)


class TMDBMovie(Base):
    __tablename__ = '02_tmdb_movies'
    
    # Use the TMDB movie ID as the primary key.
    tmdb_id = Column('tmdb_id', Integer, primary_key=True, unique=True)
    imdb_id = Column('imdb_id', String(50), unique=True)
    
    # For genres, we store comma-separated lists of IDs and names.
    genre_id = Column('genre_id', Text)            # e.g., "28, 12"
    genre_name = Column('genre_name', Text)          # e.g., "Action, Adventure"
    
    release_date = Column('release_date', Date)
    status = Column('status', String(50))
    title = Column('title', String(255), nullable=False)
    
    budget = Column('budget', BigInteger)
    revenue = Column('revenue', BigInteger)
    runtime = Column('runtime', Integer)
    vote_count = Column('vote_count', Integer)
    vote_average = Column('vote_average', Float)
    popularity = Column('popularity', Float)
    
    # For production companies, store IDs, names, and origin countries as comma-separated lists.
    production_company_id = Column('production_company_id', Text)
    production_company_name = Column('production_company_name', Text)
    production_company_origin_country = Column('production_company_origin_country', Text)
    
    # For production countries, we store the country names.
    production_country_name = Column('production_country_name', Text)
    
    # For spoken languages, store the english names.
    spoken_languages = Column('spoken_languages', Text)
    
    # Optionally, store a timestamp for when the record was created.
    created_at = Column('created_at', DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<MovieFeatures(tmdb_id={self.tmdb_id}, title='{self.title}')>"
    

class OMDBMovie(Base):
    """
    OMDBMovie represents a movie record fetched from the OMDB API.
    
    This model stores essential details about a movie, including basic metadata
    and rating information from multiple sources.
    """
    __tablename__ = "03_omdb_movies"

    # Use imdb_id as the primary key since it's unique.
    imdb_id = Column(String, primary_key=True, index=True, nullable=False)
    title = Column(String)
    year = Column(Integer, nullable=True)
    genre = Column(String)         # Expecting a comma-separated string.
    director = Column(String)
    writer = Column(String)
    actors = Column(String)
    imdb_rating = Column(Float, nullable=True)
    imdb_votes = Column(String)
    metascore = Column(Integer, nullable=True)
    box_office = Column(Integer)
    released = Column(Date)
    runtime = Column(String)
    language = Column(String)
    country = Column(String)
    rated = Column(String)
    awards = Column(String)
    rotten_tomatoes_rating = Column(Integer)
    meta_critic_rating = Column(Integer)

    def __repr__(self) -> str:
        """
        Returns a string representation of the OMDBMovie instance.
        """
        return f"<OMDBMovie(imdb_id='{self.imdb_id}', title='{self.title}')>"

    def as_dict(self) -> dict:
        """
        Returns a dictionary representation of the OMDBMovie instance.
        Useful for debugging or serialization.
        """
        return {
            "imdb_id": self.imdb_id,
            "title": self.title,
            "year": self.year,
            "genre": self.genre,
            "director": self.director,
            "writer": self.writer,
            "actors": self.actors,
            "imdb_rating": self.imdb_rating,
            "imdb_votes": self.imdb_votes,
            "metascore": self.metascore,
            "box_office": self.box_office,
            "released": self.released,
            "runtime": self.runtime,
            "language": self.language,
            "country": self.country,
            "rated": self.rated,
            "awards": self.awards,
            "rotten_tomatoes_rating": self.rotten_tomatoes_rating,
            "meta_critic_rating": self.meta_critic_rating,
        }

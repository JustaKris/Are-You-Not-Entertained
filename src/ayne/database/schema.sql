-- schema.sql
-- DuckDB schema for Are You Not Entertained? project
-- Updated schema matching TMDB and OMDB API structures

-- Create sequence first
CREATE SEQUENCE IF NOT EXISTS seq_movies_id START 1;

-- ---------------------------------------------------------------------
-- movies: master identity table (surrogate movie_id)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS movies (
    movie_id INTEGER PRIMARY KEY DEFAULT nextval('seq_movies_id'),
    tmdb_id INTEGER UNIQUE,
    imdb_id VARCHAR UNIQUE,
    title VARCHAR,
    release_date DATE,
    created_at TIMESTAMP DEFAULT current_timestamp,
    last_full_refresh TIMESTAMP,
    last_tmdb_update TIMESTAMP,
    last_omdb_update TIMESTAMP,
    last_numbers_update TIMESTAMP,
    data_frozen BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_movies_tmdb_id ON movies (tmdb_id);
CREATE INDEX IF NOT EXISTS idx_movies_imdb_id ON movies (imdb_id);
CREATE INDEX IF NOT EXISTS idx_movies_release_date ON movies (release_date);

-- ---------------------------------------------------------------------
-- tmdb_movies: TMDB metadata
-- Schema matches TMDBClient._normalize_movie_details output
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tmdb_movies (
    tmdb_id INTEGER PRIMARY KEY,
    imdb_id VARCHAR,
    title VARCHAR,
    release_date DATE,
    status VARCHAR,
    budget BIGINT,
    revenue BIGINT,
    runtime INTEGER,
    vote_count INTEGER,
    vote_average DOUBLE,
    popularity DOUBLE,
    genres VARCHAR,                -- Comma-separated genre names
    production_companies VARCHAR,  -- Comma-separated company names
    production_countries VARCHAR,  -- Comma-separated country names
    spoken_languages VARCHAR,      -- Comma-separated language names
    overview TEXT,
    last_updated_utc TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tmdb_movies_imdb_id ON tmdb_movies (imdb_id);
CREATE INDEX IF NOT EXISTS idx_tmdb_movies_release_date ON tmdb_movies (release_date);

-- ---------------------------------------------------------------------
-- omdb_movies: OMDB metadata
-- Schema matches OMDBClient output
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS omdb_movies (
    imdb_id VARCHAR PRIMARY KEY,
    title VARCHAR,
    year INTEGER,
    genre VARCHAR,                 -- Comma-separated genres
    director VARCHAR,
    writer VARCHAR,
    actors VARCHAR,
    imdb_rating DOUBLE,
    imdb_votes INTEGER,
    metascore INTEGER,
    box_office BIGINT,
    released VARCHAR,              -- Date string from API
    runtime INTEGER,               -- Runtime in minutes
    language VARCHAR,
    country VARCHAR,
    rated VARCHAR,                 -- Age rating (PG, R, etc.)
    awards VARCHAR,
    rotten_tomatoes_rating INTEGER,
    meta_critic_rating INTEGER,
    last_updated_utc TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_omdb_movies_year ON omdb_movies (year);
CREATE INDEX IF NOT EXISTS idx_omdb_movies_imdb_rating ON omdb_movies (imdb_rating);

-- ---------------------------------------------------------------------
-- numbers_movies: The Numbers box office / budget table
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS numbers_movies (
    movie_id INTEGER,
    domestic_box_office BIGINT,
    international_box_office BIGINT,
    worldwide_box_office BIGINT,
    release_year INTEGER,
    production_budget BIGINT,
    opening_weekend_box_office BIGINT,
    last_updated_utc TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_numbers_movies_movie_id ON numbers_movies (movie_id);

-- ---------------------------------------------------------------------
-- movie_refresh_state: controls refresh cadence
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS movie_refresh_state (
    movie_id INTEGER PRIMARY KEY,
    refresh_interval_days INTEGER DEFAULT 30,
    next_refresh_due TIMESTAMP,
    freeze_after_days INTEGER DEFAULT 365,
    frozen BOOLEAN DEFAULT FALSE,
    last_checked TIMESTAMP
);

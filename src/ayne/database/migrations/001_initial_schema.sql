CREATE SEQUENCE IF NOT EXISTS seq_movies_id START 1;

CREATE TABLE IF NOT EXISTS movies (
    movie_id INTEGER PRIMARY KEY DEFAULT nextval('seq_movies_id'),
    tmdb_id INTEGER UNIQUE,
    imdb_id VARCHAR UNIQUE,
    title VARCHAR,
    release_date DATE,
    created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    last_full_refresh TIMESTAMP,
    last_tmdb_update TIMESTAMP,
    last_omdb_update TIMESTAMP,
    last_numbers_update TIMESTAMP,
    data_frozen BOOLEAN NOT NULL DEFAULT FALSE,
    consecutive_unchanged_refreshes INTEGER NOT NULL DEFAULT 0,
    CHECK (tmdb_id IS NOT NULL OR imdb_id IS NOT NULL),
    CHECK (title IS NULL OR length(trim(title)) > 0),
    CHECK (consecutive_unchanged_refreshes >= 0),
    CHECK (
        last_full_refresh IS NULL
        OR (last_tmdb_update IS NOT NULL AND last_omdb_update IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_movies_tmdb_id ON movies (tmdb_id);
CREATE INDEX IF NOT EXISTS idx_movies_imdb_id ON movies (imdb_id);
CREATE INDEX IF NOT EXISTS idx_movies_release_date ON movies (release_date);

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
    genres VARCHAR,
    production_companies VARCHAR,
    production_countries VARCHAR,
    spoken_languages VARCHAR,
    overview TEXT,
    last_updated_utc TIMESTAMP,
    CHECK (budget IS NULL OR budget >= 0),
    CHECK (revenue IS NULL OR revenue >= 0),
    CHECK (runtime IS NULL OR runtime >= 0),
    CHECK (vote_count IS NULL OR vote_count >= 0),
    CHECK (vote_average IS NULL OR vote_average BETWEEN 0 AND 10),
    CHECK (popularity IS NULL OR popularity >= 0)
);

CREATE INDEX IF NOT EXISTS idx_tmdb_movies_imdb_id ON tmdb_movies (imdb_id);
CREATE INDEX IF NOT EXISTS idx_tmdb_movies_release_date ON tmdb_movies (release_date);

CREATE TABLE IF NOT EXISTS omdb_movies (
    imdb_id VARCHAR PRIMARY KEY,
    title VARCHAR,
    year INTEGER,
    genre VARCHAR,
    director VARCHAR,
    writer VARCHAR,
    actors VARCHAR,
    imdb_rating DOUBLE,
    imdb_votes INTEGER,
    metascore INTEGER,
    box_office BIGINT,
    released VARCHAR,
    runtime INTEGER,
    language VARCHAR,
    country VARCHAR,
    rated VARCHAR,
    awards VARCHAR,
    rotten_tomatoes_rating INTEGER,
    meta_critic_rating INTEGER,
    last_updated_utc TIMESTAMP,
    CHECK (year IS NULL OR year >= 1888),
    CHECK (imdb_rating IS NULL OR imdb_rating BETWEEN 0 AND 10),
    CHECK (imdb_votes IS NULL OR imdb_votes >= 0),
    CHECK (metascore IS NULL OR metascore BETWEEN 0 AND 100),
    CHECK (box_office IS NULL OR box_office >= 0),
    CHECK (runtime IS NULL OR runtime >= 0),
    CHECK (rotten_tomatoes_rating IS NULL OR rotten_tomatoes_rating BETWEEN 0 AND 100),
    CHECK (meta_critic_rating IS NULL OR meta_critic_rating BETWEEN 0 AND 100)
);

CREATE INDEX IF NOT EXISTS idx_omdb_movies_year ON omdb_movies (year);
CREATE INDEX IF NOT EXISTS idx_omdb_movies_imdb_rating ON omdb_movies (imdb_rating);

CREATE TABLE IF NOT EXISTS numbers_movies (
    movie_id INTEGER PRIMARY KEY,
    domestic_box_office BIGINT,
    international_box_office BIGINT,
    worldwide_box_office BIGINT,
    release_year INTEGER,
    production_budget BIGINT,
    opening_weekend_box_office BIGINT,
    source_url VARCHAR,
    last_updated_utc TIMESTAMP,
    CHECK (domestic_box_office IS NULL OR domestic_box_office >= 0),
    CHECK (international_box_office IS NULL OR international_box_office >= 0),
    CHECK (worldwide_box_office IS NULL OR worldwide_box_office >= 0),
    CHECK (release_year IS NULL OR release_year >= 1888),
    CHECK (production_budget IS NULL OR production_budget >= 0),
    CHECK (opening_weekend_box_office IS NULL OR opening_weekend_box_office >= 0)
);

CREATE TABLE IF NOT EXISTS movie_refresh_state (
    movie_id INTEGER PRIMARY KEY,
    refresh_interval_days INTEGER NOT NULL DEFAULT 30,
    next_refresh_due TIMESTAMP,
    freeze_after_days INTEGER NOT NULL DEFAULT 365,
    frozen BOOLEAN NOT NULL DEFAULT FALSE,
    last_checked TIMESTAMP,
    CHECK (refresh_interval_days > 0),
    CHECK (freeze_after_days > 0)
);

CREATE TABLE IF NOT EXISTS api_usage_daily (
    provider VARCHAR NOT NULL,
    usage_date DATE NOT NULL,
    requests_used INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (provider, usage_date),
    CHECK (length(trim(provider)) > 0),
    CHECK (requests_used >= 0)
);

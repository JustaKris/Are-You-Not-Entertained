CREATE TABLE movies_hardened (
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

INSERT INTO movies_hardened
SELECT
    movie_id,
    tmdb_id,
    imdb_id,
    title,
    release_date,
    COALESCE(created_at, current_timestamp),
    last_full_refresh,
    last_tmdb_update,
    last_omdb_update,
    last_numbers_update,
    COALESCE(data_frozen, FALSE),
    COALESCE(consecutive_unchanged_refreshes, 0)
FROM movies;

DROP TABLE movies;
ALTER TABLE movies_hardened RENAME TO movies;

CREATE INDEX idx_movies_tmdb_id ON movies (tmdb_id);
CREATE INDEX idx_movies_imdb_id ON movies (imdb_id);
CREATE INDEX idx_movies_release_date ON movies (release_date);

CREATE TABLE movie_refresh_state_hardened (
    movie_id INTEGER PRIMARY KEY,
    refresh_interval_days INTEGER NOT NULL DEFAULT 30,
    next_refresh_due TIMESTAMP,
    freeze_after_days INTEGER NOT NULL DEFAULT 365,
    frozen BOOLEAN NOT NULL DEFAULT FALSE,
    last_checked TIMESTAMP,
    CHECK (refresh_interval_days > 0),
    CHECK (freeze_after_days > 0)
);

INSERT INTO movie_refresh_state_hardened
SELECT
    movie_id,
    COALESCE(refresh_interval_days, 30),
    next_refresh_due,
    COALESCE(freeze_after_days, 365),
    COALESCE(frozen, FALSE),
    last_checked
FROM movie_refresh_state;

DROP TABLE movie_refresh_state;
ALTER TABLE movie_refresh_state_hardened RENAME TO movie_refresh_state;

INSERT INTO movies (
    tmdb_id,
    imdb_id,
    title,
    release_date,
    last_full_refresh,
    last_tmdb_update,
    last_omdb_update,
    last_numbers_update,
    data_frozen,
    consecutive_unchanged_refreshes
)
VALUES
    (
        603,
        'tt0133093',
        'The Matrix',
        DATE '1999-03-31',
        TIMESTAMP '2026-08-01 12:00:00',
        TIMESTAMP '2026-08-01 12:00:00',
        TIMESTAMP '2026-08-01 12:00:00',
        TIMESTAMP '2026-08-01 12:00:00',
        TRUE,
        3
    ),
    (
        346698,
        'tt1517268',
        'Barbie',
        DATE '2023-07-21',
        TIMESTAMP '2026-08-10 12:00:00',
        TIMESTAMP '2026-08-10 12:00:00',
        TIMESTAMP '2026-08-10 12:00:00',
        TIMESTAMP '2026-08-10 12:00:00',
        FALSE,
        0
    ),
    (
        693134,
        'tt15239678',
        'Dune: Part Two',
        DATE '2024-03-01',
        NULL,
        TIMESTAMP '2026-08-15 12:00:00',
        NULL,
        NULL,
        FALSE,
        0
    );

INSERT INTO tmdb_movies (
    tmdb_id,
    imdb_id,
    title,
    release_date,
    status,
    budget,
    revenue,
    runtime,
    vote_count,
    vote_average,
    popularity,
    genres,
    overview,
    last_updated_utc
)
VALUES
    (
        603,
        'tt0133093',
        'The Matrix',
        DATE '1999-03-31',
        'Released',
        63000000,
        467222728,
        136,
        25000,
        8.2,
        80.0,
        'Action, Science Fiction',
        'A hacker discovers the nature of his reality.',
        TIMESTAMP '2026-08-01 12:00:00'
    ),
    (
        346698,
        'tt1517268',
        'Barbie',
        DATE '2023-07-21',
        'Released',
        145000000,
        1445696700,
        114,
        18000,
        7.0,
        95.0,
        'Comedy, Adventure',
        'Barbie experiences an existential crisis.',
        TIMESTAMP '2026-08-10 12:00:00'
    ),
    (
        693134,
        'tt15239678',
        'Dune: Part Two',
        DATE '2024-03-01',
        'Released',
        190000000,
        714444358,
        167,
        12000,
        8.7,
        110.0,
        'Science Fiction, Adventure',
        'Paul Atreides unites with Chani and the Fremen.',
        TIMESTAMP '2026-08-15 12:00:00'
    );

INSERT INTO omdb_movies (
    imdb_id,
    title,
    year,
    genre,
    imdb_rating,
    imdb_votes,
    metascore,
    box_office,
    runtime,
    last_updated_utc
)
VALUES
    (
        'tt0133093',
        'The Matrix',
        1999,
        'Action, Sci-Fi',
        8.7,
        2100000,
        73,
        171479930,
        136,
        TIMESTAMP '2026-08-01 12:00:00'
    ),
    (
        'tt1517268',
        'Barbie',
        2023,
        'Adventure, Comedy',
        6.8,
        600000,
        80,
        636238421,
        114,
        TIMESTAMP '2026-08-10 12:00:00'
    );

INSERT INTO numbers_movies (
    movie_id,
    domestic_box_office,
    international_box_office,
    worldwide_box_office,
    release_year,
    production_budget,
    opening_weekend_box_office,
    source_url,
    last_updated_utc
)
SELECT
    movie_id,
    CASE tmdb_id WHEN 603 THEN 171479930 WHEN 346698 THEN 636238421 ELSE 282144358 END,
    CASE tmdb_id WHEN 603 THEN 295742798 WHEN 346698 THEN 809458279 ELSE 432300000 END,
    CASE tmdb_id WHEN 603 THEN 467222728 WHEN 346698 THEN 1445696700 ELSE 714444358 END,
    EXTRACT(YEAR FROM release_date)::INTEGER,
    CASE tmdb_id WHEN 603 THEN 63000000 WHEN 346698 THEN 145000000 ELSE 190000000 END,
    CASE tmdb_id WHEN 603 THEN 27788331 WHEN 346698 THEN 162022044 ELSE 82450565 END,
    'https://www.the-numbers.com/',
    TIMESTAMP '2026-08-15 12:00:00'
FROM movies
WHERE tmdb_id IN (603, 346698, 693134);

INSERT INTO movie_refresh_state (
    movie_id,
    refresh_interval_days,
    next_refresh_due,
    freeze_after_days,
    frozen,
    last_checked
)
SELECT
    movie_id,
    CASE tmdb_id WHEN 603 THEN 180 ELSE 30 END,
    TIMESTAMP '2026-09-01 12:00:00',
    365,
    data_frozen,
    TIMESTAMP '2026-08-15 12:00:00'
FROM movies
WHERE tmdb_id IN (603, 346698, 693134);

INSERT INTO api_usage_daily (provider, usage_date, requests_used)
VALUES
    ('tmdb', CURRENT_DATE, 3),
    ('omdb', CURRENT_DATE, 2),
    ('numbers', CURRENT_DATE, 12);

DELETE FROM tmdb_movies AS child
WHERE NOT EXISTS (
    SELECT 1
    FROM movies AS parent
    WHERE parent.tmdb_id = child.tmdb_id
);

DELETE FROM omdb_movies AS child
WHERE NOT EXISTS (
    SELECT 1
    FROM movies AS parent
    WHERE parent.imdb_id = child.imdb_id
);

DELETE FROM numbers_movies AS child
WHERE NOT EXISTS (
    SELECT 1
    FROM movies AS parent
    WHERE parent.movie_id = child.movie_id
);

DELETE FROM movie_refresh_state AS child
WHERE NOT EXISTS (
    SELECT 1
    FROM movies AS parent
    WHERE parent.movie_id = child.movie_id
);

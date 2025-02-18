# Raw SQL query
prepped_data_query = """
    select
        tmdb_b.title,
        tmdb_b.release_date,
        tmdb_b.vote_count as "tmdb_vote_count",
        tmdb_b.vote_average as "tmdb_vote_average",
        tmdb_f.genre_name as "genre_names",
        tmdb_f.budget,
        tmdb_f.revenue,
        tmdb_f.runtime as runtime_in_min,
        tmdb_f.popularity as tmdb_popularity,
        tmdb_f.production_company_name,
        tmdb_f.production_country_name,
        tmdb_f.spoken_languages,
        omdb_m.director,
        omdb_m.writer,
        omdb_m.actors,
        omdb_m.imdb_rating,
        omdb_m.imdb_votes,
        omdb_m.metascore,
        omdb_m.box_office,
        omdb_m.rated as "age_rating",
        omdb_m.awards,
        omdb_m.rotten_tomatoes_rating,
        omdb_m.meta_critic_rating
    from
        public."01_tmdb_movies_base" tmdb_b
    inner join public."02_tmdb_movies" tmdb_f on
        tmdb_b.tmdb_id = tmdb_f.tmdb_id
    inner join public."03_omdb_movies" omdb_m on
        tmdb_f.imdb_id = omdb_m.imdb_id
    where
        extract(year from tmdb_b.release_date) >= 2010;
"""
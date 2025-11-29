# Database

> **Status**: Template - Content to be filled in

DuckDB-based analytical database for movie data storage and querying.

## Overview

- **Database**: DuckDB (analytical SQL database)
- **Schema**: Star schema with fact and dimension tables
- **Location**: `data/db/movies.duckdb`

## Schema

### Tables

#### `movies` (fact table)

Core movie identity and refresh tracking:

```sql
CREATE TABLE movies (
    movie_id INTEGER PRIMARY KEY,
    tmdb_id INTEGER UNIQUE,
    imdb_id VARCHAR UNIQUE,
    title VARCHAR,
    release_date DATE,
    created_at TIMESTAMP DEFAULT current_timestamp,
    last_full_refresh TIMESTAMP,           -- Set when both TMDB and OMDB updated
    last_tmdb_update TIMESTAMP,            -- Last TMDB data fetch
    last_omdb_update TIMESTAMP,            -- Last OMDB data fetch
    last_numbers_update TIMESTAMP,         -- Last Numbers data fetch
    data_frozen BOOLEAN DEFAULT FALSE,     -- Exclude from automatic refreshes
    consecutive_unchanged_refreshes INTEGER DEFAULT 0  -- Track stability for freezing
);
```

**Key Columns:**

- `last_full_refresh`: Set when movie has both TMDB and OMDB data
- `data_frozen`: Movies frozen after 3 consecutive unchanged refreshes (archived movies only)
- `consecutive_unchanged_refreshes`: Increments on unchanged refresh, resets on change

#### `tmdb_movies` (dimension)

TMDB-specific movie data:

```sql
CREATE TABLE tmdb_movies (
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
    genres VARCHAR,                    -- Comma-separated
    production_companies VARCHAR,      -- Comma-separated
    production_countries VARCHAR,      -- Comma-separated
    spoken_languages VARCHAR,          -- Comma-separated
    overview TEXT,
    last_updated_utc TIMESTAMP
);
```

#### `omdb_movies` (dimension)

OMDB/IMDb ratings and metadata:

```sql
CREATE TABLE omdb_movies (
    imdb_id VARCHAR PRIMARY KEY,
    title VARCHAR,
    year INTEGER,
    genre VARCHAR,                     -- Comma-separated
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
    rated VARCHAR,                     -- Age rating (PG, R, etc.)
    awards VARCHAR,
    rotten_tomatoes_rating INTEGER,
    meta_critic_rating INTEGER,
    last_updated_utc TIMESTAMP
);
```

#### `numbers_movies` (dimension)

Box office and financial data (future):

```sql
CREATE TABLE numbers_movies (
    movie_id INTEGER,
    domestic_box_office BIGINT,
    international_box_office BIGINT,
    worldwide_box_office BIGINT,
    release_year INTEGER,
    production_budget BIGINT,
    opening_weekend_box_office BIGINT,
    last_updated_utc TIMESTAMP
);
```

## Key Operations

### Initialization

```python
from ayne.database.duckdb_client import DuckDBClient

db = DuckDBClient()
```

### Queries

```python
# Get all movies
movies = db.query("SELECT * FROM movies")

# Join with TMDB data
full_data = db.query("""
    SELECT m.*, t.*
    FROM movies m
    LEFT JOIN tmdb_movies t ON m.tmdb_id = t.tmdb_id
""")
```

### Upserts

```python
import pandas as pd

# Insert or update data
df = pd.DataFrame([...])
db.upsert_dataframe("movies", df, key_columns=["tmdb_id"])
```

## Query Utilities

Helper functions for common queries:

- `load_full_dataset()`: Load all movie data with joins
- `get_movies_with_financials()`: Get movies with budget/revenue
- `get_movies_by_year()`: Filter by release year

## Related Components

- [Data Orchestration](orchestration.md)
- [Refresh Strategy](refresh-strategy.md)

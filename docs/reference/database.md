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
- Primary movie information
- Foreign keys to dimension tables
- Timestamps for data refresh tracking

#### `tmdb_movies` (dimension)
- TMDB-specific movie data
- Genres, production companies
- Budget and revenue

#### `omdb_movies` (dimension)
- OMDB ratings and awards
- Cast and crew information

#### `the_numbers_movies` (dimension)
- Box office performance data
- Production budgets
- Domestic/international revenue

## Key Operations

### Initialization

```python
from src.database.duckdb_client import DuckDBClient

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

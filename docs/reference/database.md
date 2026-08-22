# Database

AYNE uses DuckDB as its local analytical store. The database is designed for a single
development or collection process at a time, with source-specific tables joined through
the `movies` identity table.

The default file is `data/db/movies.duckdb`. The schema source of truth is
`src/ayne/database/schema.sql`.

## Initialize And Inspect

From the repository root:

```powershell
uv run ayne db init
uv run ayne db test
uv run ayne db stats
```

`db init` creates the schema if it does not exist. Use `--force` only when intentionally
re-initializing and accepting the data-loss implications described by the command help.
`db test` performs connection, schema, insert, query, update, and delete checks using a
temporary test row.

## Tables

### `movies`

The master identity and collection-state table.

| Column | Purpose |
| --- | --- |
| `movie_id` | Surrogate primary key used by The Numbers data |
| `tmdb_id` | Unique TMDB identifier |
| `imdb_id` | Unique IMDb identifier used for OMDB enrichment |
| `title`, `release_date` | Shared movie identity fields |
| `created_at` | Time the identity row was created |
| `last_tmdb_update`, `last_omdb_update`, `last_numbers_update` | Last successful source update |
| `last_full_refresh` | Set once both TMDB and OMDB update timestamps exist |
| `data_frozen` | Excludes stable archived movies from routine refreshes |
| `consecutive_unchanged_refreshes` | Counts unchanged refreshes used by freezing logic |

### `tmdb_movies`

TMDB detail data keyed by `tmdb_id`. It stores status, financials, runtime, ratings,
popularity, overview, and normalized text fields for genres, companies, countries, and
languages.

### `omdb_movies`

OMDB and IMDb enrichment keyed by `imdb_id`. It stores ratings, vote counts, scores,
box-office data, credits, awards, release information, and other provider metadata.

### `numbers_movies`

The Numbers financial data keyed by `movie_id`. It stores domestic, international, and
worldwide box office, production budget, opening weekend, release year, source URL, and
the last update timestamp.

### `movie_refresh_state`

Refresh scheduling state keyed by `movie_id`. It stores the current interval, next due
time, freeze threshold, frozen state, and the last time the row was checked.

### `api_usage_daily`

The persistent provider quota ledger. The composite primary key is `(provider,
usage_date)`, and `requests_used` records requests across separate command runs. OMDB
enrichment reads this table before starting work so a daily limit is not exceeded.

## Relationships

```text
movies.movie_id ─────────────── numbers_movies.movie_id
movies.tmdb_id  ─────────────── tmdb_movies.tmdb_id
movies.imdb_id  ─────────────── omdb_movies.imdb_id
movies.movie_id ─────────────── movie_refresh_state.movie_id
```

The source tables are intentionally separate because providers have different identifiers
and coverage. Use `LEFT JOIN` when an analysis should retain movies with incomplete
enrichment.

```sql
SELECT
    m.movie_id,
    m.title,
    m.release_date,
    t.budget,
    t.revenue,
    o.imdb_rating,
    n.worldwide_box_office
FROM movies AS m
LEFT JOIN tmdb_movies AS t ON m.tmdb_id = t.tmdb_id
LEFT JOIN omdb_movies AS o ON m.imdb_id = o.imdb_id
LEFT JOIN numbers_movies AS n ON m.movie_id = n.movie_id;
```

## Python Access

Use `DuckDBClient` for direct SQL and writes. Open the database read-only for notebooks
and analysis:

```python
from ayne.database.duckdb_client import DuckDBClient

with DuckDBClient(read_only=True) as db:
    recent = db.query(
        """
        SELECT title, release_date
        FROM movies
        ORDER BY release_date DESC
        LIMIT 20
        """
    )
```

Use the query helpers for common analysis joins:

```python
from ayne.utils.query_utils import (
    get_movies_by_year_range,
    get_movies_with_financials,
    load_full_dataset,
)

movies = load_full_dataset(include_nulls=True)
financials = get_movies_with_financials(min_budget=1_000_000)
recent = get_movies_by_year_range(2020, 2024)
```

For helper behavior and data-file persistence, see the [utilities guide](../guides/utilities-guide.md).

## Operational Notes

- Keep one writer process connected to the local database during collection.
- Use `ayne db stats` before and after a collection run to compare coverage.
- Use parameterized SQL for runtime values and controlled allowlists for identifiers.
- Treat `data/db/movies.duckdb` as environment data when sharing or publishing the
  repository.
- Do not commit API keys, credentials, or sensitive raw responses.

## Related Documentation

- [Data Collection Workflow](../guides/data-collection-workflow.md) - Discovery and enrichment flow
- [Refresh Strategy](refresh-strategy.md) - Refresh cadence and freezing behavior
- [Database Monitoring](../guides/database-monitoring.md) - Notebook-based health checks

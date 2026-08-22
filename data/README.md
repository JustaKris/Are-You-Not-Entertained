# Data Directory

The `data/` directory contains the local movie database and generated data used by
analysis notebooks. Provider responses are kept separate from derived outputs so the
collection and transformation steps remain inspectable.

## Structure

```text
data/
├── db/          # DuckDB database files, including movies.duckdb
├── raw/         # Raw, immutable responses from providers
├── processed/   # Cleaned, analysis-ready outputs such as Parquet files
└── artifacts/   # Generated model and analysis artifacts
```

## Database

The default database is `data/db/movies.duckdb`. Initialize or inspect it through the
CLI from the repository root:

```powershell
uv run ayne db init
uv run ayne db test
uv run ayne db stats
```

The schema includes:

- `movies` - Movie identity and refresh tracking
- `tmdb_movies` - TMDB metadata, ratings, budget, and revenue
- `omdb_movies` - OMDB/IMDb ratings, credits, awards, and box office
- `numbers_movies` - The Numbers budget and box-office fields
- `movie_refresh_state` - Refresh cadence and due-date state
- `api_usage_daily` - Persistent per-provider daily request counts

See the [database reference](../docs/reference/database.md) for columns and joins.

## Querying From Python

Use the package query helpers rather than duplicating connection and join logic in
notebooks:

```python
from ayne.utils.query_utils import get_movies_with_financials, load_full_dataset

movies = load_full_dataset(include_nulls=True)
financial_movies = get_movies_with_financials(min_budget=1_000_000)
```

The [utilities guide](../docs/guides/utilities-guide.md) covers query and persistence
helpers.

## Data Handling Rules

- Keep raw provider responses immutable.
- Prefer Parquet for processed tabular data because it preserves types and supports
  efficient analytical reads.
- Do not put API keys or credentials in data files, notebooks, logs, or reports.
- Review the repository's ignore rules before adding large generated files. The raw and
  processed data directories are ignored by default; the local DuckDB file may be
  intentionally retained for development and should be treated as environment data.
- Regenerate derived outputs from the database or raw inputs when practical.

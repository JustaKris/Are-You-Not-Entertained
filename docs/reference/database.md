# Database

AYNE uses DuckDB as its local analytical store. The database is designed for a single
development or collection process at a time, with source-specific tables joined through
the `movies` identity table.

The default file is `data/db/movies.duckdb`. The canonical schema is the numbered SQL
sequence in `src/ayne/database/migrations/`. Writable `DuckDBClient` connections apply
pending migrations automatically, and the migration history is stored in
`schema_migrations`.

## First Setup

From the repository root:

```powershell
uv sync --group dev
uv run ayne db init
uv run ayne db test
uv run ayne validate database
```

`db init` is safe to run repeatedly. It applies pending migrations, verifies required
tables, and runs the structural contract checks. Use `--dry-run` to list the migration
sequence without opening or changing the database:

```powershell
uv run ayne db init --dry-run
```

Use `db migrate` when you want to inspect the migration state directly:

```powershell
uv run ayne db migrate
```

### Rebuild From Zero

`--force` permanently drops the configured database tables and rebuilds the database from
the migration files. Create a local backup first:

```powershell
uv run ayne db backup
uv run ayne db init --force
```

The backup command writes a UTC-timestamped DuckDB file under `data/db/archive/` and
refuses to run while another process has the database open.

There is no hand-edited schema path. Add a new numbered migration for every schema change;
never edit an applied migration. If a fully migrated database was created from an earlier
checkout of the migration files, AYNE refreshes the recorded checksums to the current
files. A checksum mismatch is still blocking when later migrations are pending, because
the migration history must be restored or the database rebuilt before continuing.

## Data Contract

The contract is intentionally staged: discovery can create an identity before enrichment,
and provider fields remain nullable when the provider has not supplied a value.

| Area | Contract |
| --- | --- |
| Movie identity | `movie_id` is the local surrogate key. Each `movies` row must have a TMDB ID, an IMDb ID, or both. The individual provider IDs remain nullable during staged collection and are unique when present. |
| Titles and dates | Titles are expected to be nonblank. `release_date` is nullable because providers may omit or disagree on dates. |
| Provider keys | `tmdb_movies.tmdb_id`, `omdb_movies.imdb_id`, and `numbers_movies.movie_id` are non-null primary keys. |
| Numeric provider data | Budgets, revenue, box office, runtimes, votes, popularity, and counts are nullable when unknown and nonnegative when present. |
| Ratings | TMDB and IMDb ratings are between 0 and 10. Metascore and critic ratings are between 0 and 100. |
| Refresh state | Refresh and freeze intervals are positive; unchanged-refresh counters are nonnegative. |
| Timestamps | Source update timestamps are nullable until a successful update. `last_full_refresh` is only valid after both TMDB and OMDB timestamps exist. |
| Relationships | Provider and refresh rows reference an existing `movies` identity row. |

Fresh databases enforce the numeric and state constraints in migration 001. Relationship
integrity is checked explicitly because DuckDB's parent-table update limitations make
physical foreign keys incompatible with the collector's normal upsert and refresh flow.
The validator checks those relationships before analysis or sharing.

## Tables

### `movies`

The master identity and collection-state table. It owns the local `movie_id`, unique
provider identifiers, shared title/date fields, source update timestamps, and freeze state.

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
usage_date)`, and `requests_used` records requests across separate command runs.

### `schema_migrations`

The applied migration ledger. Each row stores a consecutive version, migration name,
SHA-256 checksum, and application timestamp.

### `dataset_manifests`

The manifest ledger. Each row stores the schema version, source commit, generation time,
database path, per-table row counts, input hashes, and the manifest checksum.

## Validation

Run the full database quality gate after initialization, collection, migrations, or before
sharing a dataset:

```powershell
uv run ayne validate database
```

The validator checks:

- schema version, required tables, column types, and canonical nullability;
- orphaned TMDB, OMDB, The Numbers, and refresh-state rows;
- missing identities, blank titles, invalid numeric ranges, and inconsistent full-refresh flags;
- stale TMDB data older than 90 days, stale OMDB data older than 180 days, and future timestamps.

Structural, relationship, and domain findings are errors and return a nonzero exit code.
Freshness findings are warnings because a stale record can still be valid historical data.
Treat freshness warnings as failures when preparing a release:

```powershell
uv run ayne validate database --strict-freshness
```

Provider-specific checks remain available through `ayne validate tmdb` and
`ayne validate imdb`; `ayne validate all` runs the database contract first and then both
provider checks.

## Demo Database

The committed sanitized fixture at `data/fixtures/demo.sql` contains three movies and
representative rows across every application table. Build a standalone demo database
without API keys or network access:

```powershell
uv run ayne db seed-demo --output data/db/demo.duckdb
uv run ayne validate database
```

The default output is `data/db/demo.duckdb`. Use `--force` to replace an existing demo
database. The fixture is SQL rather than a binary DuckDB file so it remains reviewable,
portable, and deterministic.

## Dataset Manifests

Create a manifest after a collection or before publishing an analysis result:

```powershell
uv run ayne db manifest
```

By default the command writes a timestamped JSON file to `data/manifests/`, registers the
same record in `dataset_manifests`, records the current Git commit, counts rows in each
application table, and hashes every file under `data/raw/`. Use explicit roots for a
different input layout:

```powershell
uv run ayne db manifest `
  --output data/manifests `
  --input-root data/raw
```

The JSON contains `schema_version`, `source_commit`, `generated_at`, `row_counts`,
`input_hashes`, and `manifest_sha256`. Keep manifests with the analysis or release they
describe; they make it possible to explain which schema, source revision, and raw inputs
produced a dataset.

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
- Run `ayne validate database` after collection and `ayne db manifest` when recording a release.
- Use parameterized SQL for runtime values and controlled allowlists for identifiers.
- Treat `data/db/movies.duckdb` as environment data when sharing or publishing the repository.
- Do not commit API keys, credentials, or sensitive raw responses.

## Related Documentation

- [Data Collection Workflow](../guides/data-collection-workflow.md) - Discovery and enrichment flow
- [Refresh Strategy](refresh-strategy.md) - Refresh cadence and freezing behavior
- [Database Monitoring](../guides/database-monitoring.md) - Notebook-based health checks
- [Testing](../development/testing.md) - Database foundation test coverage

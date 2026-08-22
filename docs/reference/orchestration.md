# Data Collection Orchestration

`DataCollectionOrchestrator` coordinates database writes, asynchronous provider clients,
refresh decisions, and per-provider usage tracking. It lives in
`src/ayne/data_collection/orchestrator.py` and is used by the Typer CLI.

## Workflow Responsibilities

The orchestrator supports these stages:

1. Discover basic movie records from TMDB and upsert them into `movies`.
2. Enrich discovered records with TMDB detail data and populate IMDb IDs.
3. Enrich records with OMDB data when an IMDb ID is available.
4. Refresh existing records according to age-based intervals.
5. Track meaningful changes and freeze stable archived movies.
6. Record provider requests in `api_usage_daily`.

The Numbers scraper is available through the same orchestrator, but its enrichment is a
separate operation because it scrapes public HTML pages rather than using the combined
TMDB/OMDB workflow.

## Complete Collection

`run_full_collection` can discover new records and then refresh existing records:

```python
from ayne.data_collection.orchestrator import DataCollectionOrchestrator
from ayne.database.duckdb_client import DuckDBClient

db = DuckDBClient()
orchestrator = DataCollectionOrchestrator(db)

try:
    stats = await orchestrator.run_full_collection(
        discover_movies=True,
        max_discover_movies=1_000,
        max_discover_pages=10,
        min_vote_count=200,
        min_release_year=2020,
        refresh_limit=100,
        omdb_max_movies=500,
    )
finally:
    await orchestrator.close()
    db.close()
```

The result has four counters: `discovered`, `tmdb_updated`, `omdb_updated`, and
`frozen`. Set `discover_movies=False` to run refresh work without discovery. The CLI's
`ayne collect daily` command uses this mode by default; `--discover` enables discovery.

## Individual Stages

### Discovery

```python
discovered = await orchestrator.discover_and_store_movies(
    max_movies=500,
    min_popularity=15.0,
    min_vote_count=100,
    min_release_year=2010,
    max_pages=10,
)
```

Discovery stores basic identity fields. It does not advance the source refresh timestamp;
`last_tmdb_update` represents successful TMDB detail or refresh work. Detail enrichment
is intentionally separate so a run can control the expensive follow-up work.

`max_movies` is a retained-record cap and derives a page budget when `max_pages` is not
provided. `max_pages` is a global fetched-page budget across recursively split ranges;
the 500-page TMDB ceiling remains a per-query safety limit.

### TMDB Detail Enrichment

```python
tmdb_count = await orchestrator.enrich_tmdb_details(
    limit=500,
    min_release_year=2020,
    max_release_year=2024,
)
```

This stage fills `tmdb_movies` and copies IMDb IDs into `movies` for the OMDB stage.

### OMDB Enrichment

```python
omdb_count = await orchestrator.enrich_omdb_data(
    limit=500,
    min_release_year=2020,
    max_release_year=2024,
)
```

The requested limit is reduced to the configured per-operation cap and then to the
remaining recorded OMDB quota before requests are made. Movies without IMDb IDs are
skipped. Partial successful usage is recorded if a quota or cancellation exception ends
the batch.

### The Numbers Enrichment

```python
numbers_count = await orchestrator.enrich_numbers_data(
    limit=25,
    min_release_year=2020,
    max_release_year=2024,
)
```

The Numbers client uses a single concurrent request and a deliberately conservative rate
because it consumes public web pages. The orchestrator selects only movies without a
`numbers_movies` row, tries a bounded set of candidate URLs, and records actual request
attempts. Existing rows are not refreshed automatically yet. Use
`uv run ayne numbers enrich` for the normal CLI entry point.

## Refresh Planning

`get_movies_for_refresh` returns the rows eligible for a refresh. It can filter by year,
source, and limit:

```python
movies = orchestrator.get_movies_for_refresh(
    limit=100,
    min_release_year=2020,
    data_source="omdb",
    include_frozen=False,
)

tmdb_count, omdb_count, frozen_count = await orchestrator.refresh_movie_data(
    movies,
    fetch_tmdb=True,
    fetch_omdb=True,
    omdb_max_movies=500,
)
```

The refresh strategy uses movie age and the last source update timestamps. It compares
volatile fields before and after each successful fetch, increments unchanged-refresh
counts per movie, and freezes stable archived movies after the configured threshold.
Only successful provider fetches count as evidence for a stability cycle. Global freezing
requires both TMDB and OMDB timestamps; The Numbers is optional and does not block the
gate. See the [refresh strategy reference](refresh-strategy.md) for the intervals and
freeze criteria.

## Failure And Cleanup Behavior

Provider clients use bounded retries with exponential backoff for transient HTTP and
network failures. A batch can partially succeed; records already written remain in the
database and a later run can retry the remaining work. OMDB quota exhaustion is handled
as an expected stop condition rather than a reason to discard completed work.

Always close the orchestrator and database in a `finally` block. `close()` closes the
TMDB, OMDB, and The Numbers HTTP clients.

## CLI Entry Points

```powershell
uv run ayne tmdb update --max-movies 1000
uv run ayne tmdb enrich --max-movies 500
uv run ayne omdb enrich --max-movies 500
uv run ayne numbers enrich --max-movies 25
uv run ayne collect daily --discover --discover-limit 500 --discover-pages 25
```

Use the [CLI Guide](../guides/cli-guide.md) for all command options and the
[filtering reference](data-collection-filtering.md) for environment-specific defaults.

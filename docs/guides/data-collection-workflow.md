# Data Collection Workflow

AYNE collects movie data in stages so discovery, detail enrichment, quota use, and
refresh decisions can be controlled independently. The workflow is implemented by
`DataCollectionOrchestrator` and exposed through the `ayne` CLI.

## Lifecycle

```text
Initialize DuckDB
      |
      v
TMDB discovery -> TMDB details -> OMDB enrichment
      |                |                 |
      +----------------+-----------------+
                       v
              Refresh state and quota ledger
                       |
                       v
              The Numbers enrichment (separate)
```

## 1. Initialize The Database

Create the local schema before collecting data:

```powershell
uv run ayne db init
uv run ayne db test
uv run ayne validate database
```

The database contains the `movies` identity table, source tables for TMDB, OMDB, and
The Numbers, `movie_refresh_state`, and the `api_usage_daily` quota ledger. See the
[database reference](../reference/database.md) for relationships and table responsibilities.

## 2. Discover Movies

TMDB discovery stores basic identity fields in `movies`. Popularity, vote count, year,
status, and page limits are controlled through the environment configuration or the
discovery command:

```powershell
uv run ayne tmdb update --max-movies 1000 --min-year 2020
uv run ayne tmdb update --min-popularity 20 --min-votes 100 --max-pages 10 --dry-run
```

Discovery is intentionally separate from detail enrichment. This makes it possible to
inspect or cap the candidate set before requesting more detailed data.

## 3. Fetch TMDB Details

TMDB detail enrichment processes discovered movies that do not yet have a
`tmdb_movies` record. It stores budget, revenue, ratings, runtime, status, metadata, and
IMDb IDs:

```powershell
uv run ayne tmdb enrich --max-movies 500
```

IMDb IDs from this stage are the prerequisite for OMDB enrichment.

## 4. Enrich With OMDB

OMDB enrichment processes movies with IMDb IDs that do not yet have an `omdb_movies`
record:

```powershell
uv run ayne omdb enrich --max-movies 500
uv run ayne omdb status
```

The command checks `api_usage_daily` and caps work at the remaining configured daily
quota. Completed records remain stored if the quota is exhausted during a run.

## 5. Add The Numbers Data

The Numbers enrichment is an explicit, separate operation. It requests public HTML at a
deliberately conservative rate and stores financial data in `numbers_movies`:

```powershell
uv run ayne numbers enrich --max-movies 25 --min-year 2020
```

Keep this operation small and avoid parallel scraping. The
[rate-limiting reference](../reference/rate-limiting.md) covers the provider-specific defaults.

## Refreshing Existing Data

Routine refreshes select records by age, last source update, and frozen state. The
default combined workflow refreshes existing data without discovery:

```powershell
uv run ayne collect daily
uv run ayne collect daily --tmdb-refresh 200 --omdb-limit 500
```

The command displays a live Rich progress bar while TMDB and OMDB requests are running.
Planning and candidate-selection stages appear as status text; request stages show
completed and total counts. A run already in progress must be restarted to use this
display because command behavior is loaded when the process starts.

Enable discovery when a run should also find new movies:

```powershell
uv run ayne collect daily --discover --discover-limit 500
uv run ayne collect full --max-tmdb 5000 --max-omdb 1000 --min-year 2020
```

Use `--include-frozen` only for an intentional force refresh. The normal workflow
excludes stable archived movies.

## Refresh Cadence

The refresh strategy uses the movie's age at the time of evaluation:

| Age | TMDB | OMDB | The Numbers |
| --- | ---: | ---: | ---: |
| Recent, up to 60 days | 5 days | 5 days | 5 days |
| Established, 61 to 180 days | 15 days | 30 days | 30 days |
| Mature, 181 to 365 days | 30 days | 90 days | 90 days |
| Archived, over 365 days | 90 days | 180 days | 180 days |

An archived movie can be frozen after three consecutive refreshes without meaningful
changes. Frozen records stay out of routine refreshes until explicitly included.

## Partial Success And Retries

Provider requests use bounded retries with exponential backoff for transient HTTP and
network failures. A collection can partially succeed: rows written before a later
failure remain available, and a subsequent run can select the remaining work.

The workflow treats these cases separately:

- A missing or invalid API key stops the relevant provider operation.
- A transient request failure is retried within the client's retry policy.
- OMDB daily quota exhaustion stops further OMDB requests while preserving completed
  enrichment.
- Missing IMDb IDs are skipped for OMDB until TMDB details provide one.

## Safe Operating Sequence

For a new or empty database, use a bounded sequence first:

```powershell
uv run ayne db init
uv run ayne tmdb update --max-movies 100 --max-pages 2
uv run ayne tmdb enrich --max-movies 100
uv run ayne omdb enrich --max-movies 50
uv run ayne db stats
uv run ayne validate database
uv run ayne db manifest
```

Use `--dry-run` before increasing limits, inspect `ayne db stats` between stages, and
keep provider keys in `.env`. The
[filtering reference](../reference/data-collection-filtering.md) documents repeatable
environment profiles and command overrides.

## Related Documentation

- [CLI Guide](../guides/cli-guide.md) - Full command and option reference
- [Filtering](../reference/data-collection-filtering.md) - Filters, limits, and quota controls
- [Orchestration](../reference/orchestration.md) - Python implementation contract
- [Refresh Strategy](../reference/refresh-strategy.md) - Refresh and freezing logic
- [Database](../reference/database.md) - Schema and query access

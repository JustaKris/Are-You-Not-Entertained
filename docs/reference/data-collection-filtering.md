# Data Collection Filtering

Filtering controls which movies AYNE discovers and which records receive enrichment.
Use the checked-in YAML files for repeatable environment defaults and CLI options for
one-off changes.

## Configuration Precedence

`ayne` loads the YAML file for `ENVIRONMENT` from `configs/`. Values are resolved in
this order, from highest to lowest priority:

1. Operating-system environment variables
2. Values in `.env`
3. The selected environment YAML file
4. Defaults declared by `Settings`

The checked-in development configuration is a useful local baseline. Keep API keys and
other secrets in `.env`, never in YAML or notebooks.

```powershell
$env:ENVIRONMENT = "development"
uv run ayne config
```

## TMDB Discovery Filters

The `ayne tmdb update` command discovers basic movie records from TMDB. Its filters are
applied by the TMDB discover request:

| Setting | Type | Development value | Purpose |
| --- | --- | --- | --- |
| `tmdb_min_popularity` | float | `10.0` | Minimum TMDB popularity score |
| `tmdb_min_vote_count` | integer | `50` | Minimum TMDB vote count |
| `tmdb_min_release_year` | integer | `1950` | Earliest release year |
| `tmdb_max_release_year` | integer or null | `null` | Latest release year; null means no configured upper bound |
| `tmdb_allowed_release_statuses` | list | Released, Post Production, In Production | Statuses allowed during detail processing |
| `tmdb_max_movies` | integer or null | `null` | Per-operation discovery cap; null means unlimited |

Status filtering is applied when full TMDB details are fetched. Discovery can also be
bounded by the number of pages requested.

### CLI Overrides

Use `ayne tmdb update` for discovery-specific overrides:

```powershell
uv run ayne tmdb update --max-movies 1000 --min-popularity 20 --min-votes 100 --min-year 2010
uv run ayne tmdb update --min-year 2020 --max-year 2024 --max-pages 10 --dry-run
uv run ayne tmdb update --full
```

`--full` removes the movie cap for that invocation. It does not remove popularity,
vote-count, or year filters.

## Enrichment Filters

Enrichment operates on movies already in the database:

- `ayne tmdb enrich` fetches details for movies with a TMDB ID but no `tmdb_movies`
  record.
- `ayne omdb enrich` fetches OMDB data for movies with an IMDb ID but no
  `omdb_movies` record.
- `ayne omdb refresh` updates existing OMDB records that are due according to the
  refresh strategy.
- `ayne numbers enrich` adds missing box-office and budget data from The Numbers.

TMDB, OMDB, and The Numbers commands accept `--min-year`, `--max-year`, a command-
specific limit, and `--dry-run` where applicable:

```powershell
uv run ayne tmdb enrich --min-year 2020 --max-movies 500
uv run ayne omdb enrich --min-year 2020 --max-year 2024 --max-movies 500
uv run ayne omdb refresh --min-year 2020 --limit 100
uv run ayne numbers enrich --min-year 2020 --max-movies 25
```

The OMDB settings are:

| Setting | Type | Purpose |
| --- | --- | --- |
| `omdb_max_movies` | integer | Maximum OMDB records processed in one operation |
| `omdb_daily_request_limit` | integer | Daily quota used by the persistent usage ledger |
| `omdb_min_release_year` | integer or null | Earliest movie year considered |
| `omdb_max_release_year` | integer or null | Latest movie year considered |

The orchestrator caps OMDB work at the remaining daily quota. A second run on the same
day therefore continues to respect the recorded usage in `api_usage_daily`.

## Combined Workflows

Use the combined commands when you want one workflow to coordinate discovery, refresh,
and quota-aware enrichment:

```powershell
# Refresh existing records; discovery is off by default.
uv run ayne collect daily --tmdb-refresh 100 --omdb-limit 500

# Refresh and discover new movies in the same run.
uv run ayne collect daily --discover --discover-limit 500

# Populate a new database or run a broad collection.
uv run ayne collect full --max-tmdb 5000 --max-omdb 1000 --min-year 2020
```

`--include-frozen` is available on the combined workflows when a deliberate force
refresh is required. Prefer the default behavior so stable archived movies remain out
of routine refreshes.

## Choosing Filters

Start with a small dry run before spending provider quota:

```powershell
uv run ayne tmdb update --min-popularity 50 --min-votes 500 --max-movies 10 --dry-run
uv run ayne omdb enrich --max-movies 10 --dry-run
```

Use stricter popularity and vote thresholds for a focused mainstream dataset. Relax
them for broader film-study or catalog work, but expect more API requests and more
records with incomplete enrichment.

For daily operations, prefer `omdb_max_movies` or `--omdb-limit` below the provider's
daily quota to leave room for retries and manual runs. The persistent usage ledger is a
backstop, not a replacement for conservative scheduling.

## Troubleshooting

### Few Or No TMDB Results

Check the active settings with `uv run ayne config`. Filters may be too restrictive, or
the requested year range may not have enough qualifying movies. Use a dry run with a
lower popularity or vote threshold to inspect the effect.

### OMDB Enrichment Is Skipped

OMDB enrichment requires IMDb IDs, which are normally populated by `ayne tmdb enrich`.
Run TMDB detail enrichment first and then check the remaining quota:

```powershell
uv run ayne tmdb enrich --max-movies 100
uv run ayne omdb status
uv run ayne omdb enrich --max-movies 100
```

### Need A Different Repeatable Profile

Edit the appropriate file in `configs/`, keep the change non-sensitive, and verify it
with `uv run ayne config`. Use an environment variable or CLI option for temporary
experiments instead of changing the shared defaults.

## Related Documentation

- [CLI Guide](../guides/cli-guide.md) - Complete command reference
- [Data Collection Workflow](../guides/data-collection-workflow.md) - End-to-end collection flow
- [Refresh Strategy](refresh-strategy.md) - Age-based refresh and freezing rules
- [Database](database.md) - Tables, relationships, and query helpers

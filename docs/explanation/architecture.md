# Architecture

AYNE is organized as a local, inspectable data pipeline. The supported runtime path is
small by design: a Typer command starts a collection operation, an orchestrator coordinates
provider clients and refresh policy, and a DuckDB wrapper persists the result for analysis.

## Runtime Shape

```text
PowerShell command
       |
       v
ayne.cli.main
       |
       +--> core.config and core.logging
       |
       v
DataCollectionOrchestrator
       |
       +--> TMDBClient
       +--> OMDBClient
       +--> TheNumbersClient
       +--> refresh_strategy
       +--> api_usage quota ledger
       |
       v
DuckDBClient --> data/db/movies.duckdb
       |
       v
query_utils --> pandas DataFrames and notebooks
```

The orchestrator is the controlling boundary for collection. It keeps discovery, detail
enrichment, refresh decisions, quota accounting, and database writes coordinated without
making the provider clients responsible for workflow policy.

## Package Boundaries

| Package | Responsibility | Current role |
| --- | --- | --- |
| `ayne.cli` | Typer commands for collection, validation, and database operations | Supported entry point |
| `ayne.core` | Settings, YAML and `.env` loading, logging, and project exceptions | Shared runtime foundation |
| `ayne.data_collection` | Provider clients, rate limiting, retries, API usage tracking, and refresh policy | Supported pipeline implementation |
| `ayne.database` | DuckDB connection wrapper and schema definition | Supported persistence boundary |
| `ayne.utils` | Query, I/O, and plotting helpers used by analysis workflows | Supported analysis support |
| `ayne.api` | Future service-facing interfaces | Extension surface, not a completed API |
| `ayne.ml` | Future feature engineering, model training, and serialization workflows | Extension surface, not a completed modeling platform |
| `ayne.web` | Future browser-facing presentation or service delivery | Extension surface, not a completed web application |

The package layout keeps provider integration and storage details out of the CLI command
modules. Commands assemble the operation and present results; the data collection and
database layers own the behavior.

## Collection Flow

1. `ayne.cli.main` registers the command groups and loads shared settings.
2. A collection command creates a `DuckDBClient` and `DataCollectionOrchestrator`.
3. The orchestrator selects candidates using the configured filters and refresh strategy.
4. Provider clients make asynchronous HTTP requests through a shared rate limiter and
   bounded retry policy.
5. Normalized provider records are written to source-specific DuckDB tables. The master
   `movies` table keeps stable identity and tracking fields.
6. The `api_usage_daily` table records provider usage so later commands can respect daily
   limits across separate runs.
7. Query helpers open the database read-only for notebooks, reports, and analysis.

TMDB discovery and detail enrichment form the normal starting path. OMDB depends on the
IMDb identifiers produced by TMDB detail enrichment. The Numbers is deliberately a
separate enrichment operation because it scrapes public HTML and has a more conservative
request policy.

The [data collection workflow](../guides/data-collection-workflow.md) documents the
operator-facing sequence, while the [orchestration reference](../reference/orchestration.md)
documents the Python contract.

## Persistence Model

DuckDB stores a master identity table and source-specific tables rather than flattening
every provider response into one write path:

- `movies` stores stable identity, release dates, and refresh tracking.
- `tmdb_movies` stores TMDB metadata, ratings, financial fields, and normalized lists.
- `omdb_movies` stores IMDb and OMDB ratings, credits, awards, and box office fields.
- `numbers_movies` stores domestic, international, worldwide, and budget figures.
- `movie_refresh_state` stores cadence and freeze state used by refresh decisions.
- `api_usage_daily` stores provider request counts by date.

The [database reference](../reference/database.md) describes columns and relationships. The
[utilities guide](../guides/utilities-guide.md) covers the read-oriented helpers that join
these tables for analysis.

## Operational Invariants

- Provider credentials remain in environment configuration rather than source files.
- Requests pass through provider-specific pacing and bounded retry behavior.
- Collection limits are explicit so a first run can be bounded and inspected.
- Partial provider success is retained in DuckDB; a later run can select remaining work.
- Routine refreshes exclude frozen records unless an operator explicitly forces them.
- The database is a local single-user analytical store. A multi-user transactional service
  would require a different persistence boundary.

The [rate limiting reference](../reference/rate-limiting.md) and
[refresh strategy reference](../reference/refresh-strategy.md) explain the two policies that
most directly shape runtime behavior.

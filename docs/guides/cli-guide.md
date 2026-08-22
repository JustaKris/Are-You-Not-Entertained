# CLI Guide

Complete guide to using the AYNE command-line interface.

## Overview

The AYNE CLI provides a modern, user-friendly interface for all data collection, validation, and database management tasks. Built with [Typer](https://typer.tiangolo.com/), it offers:

- ✅ **Type-safe commands** with automatic validation
- ✅ **Beautiful output** with Rich formatting
- ✅ **Dry-run mode** for safe previews
- ✅ **Comprehensive help** with `--help` on any command
- ✅ **Progress indicators** for long-running tasks

## Installation

After installing the package, the `ayne` command becomes available:

```powershell
# Install package with CLI dependencies
uv sync

# Verify installation
uv run ayne --help
```

The examples below assume the project environment is activated. Otherwise, prefix each command with `uv run` (for example, `uv run ayne db init`).

## Command Structure

All commands follow this pattern:

```powershell
ayne [GROUP] [COMMAND] [OPTIONS]
```

Command groups:

- `db` - Database management
- `tmdb` - TMDB data collection
- `omdb` - OMDB data enrichment
- `numbers` - The Numbers financial enrichment
- `collect` - Combined workflows
- `validate` - Data validation

## Quick Start

```powershell
# Initialize database
ayne db init

# Test database connectivity
ayne db test

# Discover movies from TMDB
ayne tmdb update --max-movies 1000

# Enrich with OMDB data
ayne omdb enrich --max-movies 500

# Optionally fill missing financial data
ayne numbers enrich --max-movies 25

# Run daily refresh
ayne collect daily

# Validate data quality
ayne validate database
ayne validate all
```

## Database Commands

### Initialize Database

Initialize the database and apply all pending migrations:

```powershell
# Standard initialization
ayne db init

# Rebuild from zero (drops all configured database tables)
ayne db init --force

# Preview the migration sequence without changing the database
ayne db init --dry-run
```

The migration ledger is stored in `schema_migrations`. Use the explicit migration
command to inspect applied versions and checksums:

```powershell
ayne db migrate
```

### Test Database

Run connectivity and CRUD tests:

```powershell
# Quick test
ayne db test

# Verbose output with statistics
ayne db test --verbose
```

### Show Statistics

Display database statistics:

```powershell
ayne db stats
```

### Validate The Database Contract

Run structural, relationship, domain, and freshness checks:

```powershell
# Errors fail the command; stale data is reported as a warning
ayne validate database

# Treat stale TMDB and OMDB records as failures too
ayne validate database --strict-freshness
```

### Create A Demo Database

Build a small sanitized database from the committed fixture without provider credentials:

```powershell
ayne db seed-demo --output data/db/demo.duckdb
```

Use `--force` to replace an existing demo database.

### Back Up The Local Database

Create a timestamped local backup before rebuilding the database or running another
destructive maintenance operation:

```powershell
ayne db backup
```

The default destination is `data/db/archive/` with a UTC timestamp in the filename. Use
`--output` to provide an explicit backup file path. Live databases and backups are local
environment data and are ignored by Git; use `data/fixtures/demo.sql` for the committed
sanitized database source.

### Record A Dataset Manifest

Record the schema version, Git commit, table row counts, and hashes of files under
`data/raw/`:

```powershell
ayne db manifest
```

The JSON manifest is written to `data/manifests/` and registered in the database.

## TMDB Commands

The TMDB commands are organized into three distinct operations:

1. **`update`** - Discover new movies (basic info only, fast)
2. **`enrich`** - Fetch detailed data for discovered movies (complete info, slower)
3. **`refresh`** - Update existing movies that need data refresh (age-based)

**TMDB discovery limits and budgets**

- **500-page maximum per query**: TMDB's discover endpoint returns about 20 movies per page and will not accept a page beyond 500 for one query.
- **Automatic splitting**: AYNE recursively splits broad year ranges when a query would exceed that per-query ceiling.
- **Work budget**: `--max-movies` caps stored discovery records and derives the number of pages to fetch when `--max-pages` is omitted. `--max-pages` is a global fetched-page budget across all recursively split ranges.
- **No daily quota assumption**: TMDB does not publish the same daily quota model as OMDB, but rate limiting, retries, response time, and local resources still make bounded runs useful.
- **Two-stage process**:
  1. **Discovery** (`tmdb update`): Fast bulk collection (20 movies/request, basic info)
  2. **Enrichment** (`tmdb enrich`): Individual detail fetches (1 movie/request, complete data)

### Discover Movies

Discover and store new movies from TMDB (basic info only):

```powershell
# Full discovery for the configured filters; still respects page safety and pacing
ayne tmdb update --full

# Optional: use explicit ranges when you want separate, reviewable batches
ayne tmdb update --min-year 2020 --max-year 2024 --max-movies 5000
ayne tmdb update --min-year 2015 --max-year 2019 --max-movies 5000
ayne tmdb update --min-year 2010 --max-year 2014 --max-movies 5000

# Limited discovery with filters
ayne tmdb update --max-movies 1000 --min-popularity 20 --min-votes 100

# Preview without changes
ayne tmdb update --max-movies 1000 --dry-run
```

**Options:**

- `--full` - Remove the movie cap for this invocation; it does not disable page safety, pacing, retries, or filters
- `--max-movies N` - Cap retained discovery records and derive a page-fetch budget when `--max-pages` is omitted
- `--min-popularity N` - Minimum popularity score (default: 10.0)
- `--min-votes N` - Minimum vote count (default: 50)
- `--min-year YYYY` - Minimum release year (default: 1950)
- `--max-year YYYY` - Maximum release year (default: current year)
- `--max-pages N` - Global maximum number of TMDB pages fetched across all split ranges; overrides the derived budget
- `--dry-run` - Preview without making changes

**Note:** The system automatically handles TMDB's 500-page-per-query limit by recursively
splitting year ranges. A failed or duplicate page can leave a bounded run with fewer
records than its requested movie cap, and `--max-pages` intentionally stops work when
the global page budget is reached.

### Enrich Movies with Details

Fetch detailed TMDB data for movies that only have basic info:

```powershell
# Enrich all discovered movies (up to limit)
ayne tmdb enrich --limit 500

# Enrich recent movies only
ayne tmdb enrich --min-year 2023 --limit 100

# Enrich specific year range
ayne tmdb enrich --min-year 2020 --max-year 2024 --limit 1000

# Preview what would be enriched
ayne tmdb enrich --limit 500 --dry-run
```

**Options:**

- `--limit N` / `--max-movies N` - Maximum number of detail requests; omitted means the configured cap, or all matching records when `tmdb_max_movies` is `null`
- `--min-year YYYY` - Only enrich movies from this year onwards
- `--max-year YYYY` - Only enrich movies up to this year
- `--dry-run` - Preview without making changes

**What it does:**

Fetches complete movie information including:

- Budget and revenue
- Genres and production companies
- Cast and crew (via TMDB)
- IMDb ID (required for OMDB enrichment)
- Ratings and vote counts
- Production countries and languages

### Refresh TMDB Data

Update existing movies that are due for refresh based on age-based intervals:

**What it does**: Updates movies that already have TMDB details and are due for a refresh. This command only touches movies that need updating based on refresh intervals.

```powershell
# Refresh recent releases (recommended for daily updates)
ayne tmdb refresh --min-year 2024 --limit 50

# Refresh any movies needing update
ayne tmdb refresh --limit 100

# Refresh specific year range
ayne tmdb refresh --min-year 2020 --max-year 2024 --limit 500

# Preview refresh candidates
ayne tmdb refresh --limit 100 --dry-run
```

**Options:**

- `--limit N` - Maximum number of movies to refresh; omitted means the configured cap,
  or unlimited when `tmdb_max_movies` is `null`
- `--min-year YYYY` - Only refresh movies from this year onwards
- `--max-year YYYY` - Only refresh movies up to this year
- `--dry-run` - Preview without making changes

**When to use:**

- **Daily updates**: `--min-year 2024 --limit 50` to keep recent releases current
- **Weekly updates**: `--min-year 2023 --limit 200` for last 1-2 years
- **Monthly updates**: `--limit 1000` for broader updates

**Refresh intervals** (automatic, based on movie age):

- Recent (0-60 days): Every 5 days
- Established (60-180 days): Every 15 days
- Mature (180-365 days): Every 30 days
- Archived (>365 days): Every 90-180 days

## OMDB Commands

The OMDB commands mirror TMDB structure:

1. **`enrich`** - Add OMDB data to movies that don't have it yet
2. **`refresh`** - Update existing OMDB data

### Enrich Movies with OMDB Data

Add OMDB data (IMDb ratings, box office, awards, etc.) to movies:

```powershell
# Standard enrichment
ayne omdb enrich --max-movies 1000

# Enrich recent releases only
ayne omdb enrich --min-year 2023 --max-movies 500

# Enrich specific year range
ayne omdb enrich --min-year 2020 --max-year 2024 --max-movies 1000

# Preview what would be enriched
ayne omdb enrich --max-movies 500 --dry-run
```

**Options:**

- `--max-movies N` - Maximum number of movies to enrich (uses config default)
- `--min-year YYYY` - Only enrich movies from this year onwards
- `--max-year YYYY` - Only enrich movies up to this year
- `--dry-run` - Preview without making changes

**Requirements:**

- Movies must have IMDb IDs (obtained from TMDB enrichment)
- Run `ayne tmdb enrich` first if movies don't have IMDb IDs

**Note:** OMDB has daily API limits. Use `--max-movies` to control quota usage. The
command also checks the persistent `api_usage_daily` ledger before starting. If the
remaining daily quota is lower than the requested cap, only the remaining quota is used.
Completed records are retained when a quota limit or cancellation interrupts a batch.

### Refresh OMDB Data

Update existing OMDB data for movies:

```powershell
# Refresh recent movies
ayne omdb refresh --min-year 2024 --limit 50

# Refresh any movies with OMDB data
ayne omdb refresh --limit 100

# Refresh specific year range
ayne omdb refresh --min-year 2020 --max-year 2024 --limit 200

# Preview refresh candidates
ayne omdb refresh --limit 100 --dry-run
```

**Options:**

- `--limit N` - Maximum number of movies to refresh; omitted means the configured cap,
  and the operation remains constrained by the daily OMDB quota
- `--min-year YYYY` - Only refresh movies from this year onwards
- `--max-year YYYY` - Only refresh movies up to this year
- `--dry-run` - Preview without making changes

## The Numbers Commands

The Numbers is an optional enrichment source for production budgets, domestic and
international box office, worldwide box office, and opening-weekend values. It scrapes
public HTML pages rather than using an official API, so it is deliberately separate from
the TMDB/OMDB workflow.

### Enrich Missing Financial Records

`ayne numbers enrich` selects movies that do not yet have a `numbers_movies` row and
tries a small set of title/year URL candidates sequentially:

```powershell
# Inspect candidates without making requests
ayne numbers enrich --max-movies 10 --dry-run

# Add recent financial records at a small batch size
ayne numbers enrich --min-year 2020 --max-year 2024 --max-movies 25

# Use the configured default of 50 movies and 1 request/second
ayne numbers enrich
```

**Options:**

- `--max-movies N` - Maximum missing movie records to process; the default is
  `numbers_max_movies` (`50` in the checked-in development configuration)
- `--min-year YYYY` - Only process movies from this year onwards
- `--max-year YYYY` - Only process movies up to this year
- `--dry-run` - Preview candidates without making requests

The client allows one request at a time and defaults to `1.0` request/second. A movie
may require several bounded candidate requests before it is found or marked unavailable.
Missing pages are normal partial results, and actual attempted requests are recorded in
the daily usage ledger. Existing `numbers_movies` rows are not refreshed automatically
by this command yet.

## Recommended Workflows

### Initial Data Population

Build your movie database from scratch:

```powershell
# Step 1: Discover movies in bounded batches; broad ranges auto-split per query
ayne tmdb update --min-year 2020 --max-year 2024 --max-movies 5000
ayne tmdb update --min-year 2015 --max-year 2019 --max-movies 5000
ayne tmdb update --min-year 2010 --max-year 2014 --max-movies 5000

# Step 2: Enrich all discovered movies with details
ayne tmdb enrich --limit 5000

# Step 3: Add OMDB data (mind the API limits)
ayne omdb enrich --max-movies 1000

# Check progress
ayne db stats
```

### Daily Updates (Recommended)

Keep recent movie data current with daily automation:

```powershell
# Option 1: Manual daily run
ayne tmdb refresh --min-year 2024 --limit 50
ayne omdb refresh --min-year 2024 --limit 30

# Option 2: Using collect command
ayne collect daily --tmdb-refresh 50 --omdb-limit 30

# Schedule via Task Scheduler (Windows) - runs at 2 AM daily
# Program: pwsh.exe
# Start in: D:\path\to\project
# Arguments: -NoProfile -Command "uv run ayne tmdb refresh --min-year 2024 --limit 50"
```

### Weekly Updates

Broader update scope for weekly maintenance:

```powershell
# Update last 1-2 years of movies
ayne tmdb refresh --min-year 2023 --limit 200
ayne omdb refresh --min-year 2023 --limit 150

# Or specific ranges
ayne tmdb refresh --min-year 2020 --max-year 2024 --limit 500
```

### Monthly Updates

Comprehensive refresh for monthly maintenance:

```powershell
# Update all movies needing refresh (no year filter)
ayne tmdb refresh --limit 1000
ayne omdb refresh --limit 500

# Or with collect command
ayne collect full --refresh-limit 1000 --max-omdb 500
```

### Collecting Large TMDB Ranges

TMDB automatically splits broad year ranges so the per-query 500-page ceiling is not
silently exceeded. Use `--full` for an uncapped retained-record operation, or use
`--max-movies` and `--max-pages` to keep a run deliberately bounded:

```powershell
# Collect by decade
ayne tmdb update --min-year 2020 --max-year 2029 --full
ayne tmdb update --min-year 2010 --max-year 2019 --full
ayne tmdb update --min-year 2000 --max-year 2009 --full

# Or by 5-year periods
ayne tmdb update --min-year 2020 --max-year 2024 --max-movies 5000
ayne tmdb update --min-year 2015 --max-year 2019 --max-movies 5000

# Then enrich a deliberate 10,000-record batch
ayne tmdb enrich --limit 10000
```

### Targeted Updates

Update specific subsets:

```powershell
# Recent popular movies only
ayne tmdb update --min-year 2023 --min-popularity 50 --max-movies 1000
ayne tmdb enrich --min-year 2023 --limit 1000

# High-quality movies (high vote counts)
ayne tmdb update --min-year 2020 --min-votes 1000 --max-movies 2000

# Specific year analysis
ayne tmdb update --min-year 2023 --max-year 2023 --max-movies 1000
ayne tmdb enrich --min-year 2023 --max-year 2023 --limit 1000
ayne omdb enrich --min-year 2023 --max-year 2023 --max-movies 1000
```

## Collection Workflows

### Daily Refresh

Recommended for scheduled daily runs:

```powershell
# Standard daily refresh
ayne collect daily

# With discovery enabled
ayne collect daily --discover --discover-limit 500

# Custom limits
ayne collect daily --tmdb-refresh 200 --omdb-limit 500

# Include frozen movies (force refresh)
ayne collect daily --include-frozen

# Preview workflow
ayne collect daily --dry-run
```

**Options:**

- `--tmdb-refresh N` - Number of TMDB records to refresh (default: 100)
- `--omdb-limit N` - Maximum OMDB enrichments (uses config default)
- `--discover` - Also discover new movies
- `--discover-limit N` - Limit for discovery
- `--discover-pages N` - Global TMDB page cap for discovery; overrides the derived page budget
- `--include-frozen` - Include frozen movies in refresh (force refresh)

During a live refresh, Rich reports the current stage and request progress. You will see
planning and candidate-selection stages followed by `Refreshing TMDB` and `Refreshing OMDB`
bars such as `42/100`. The combined workflow only displays the final summary after all
selected stages finish, so a command started before this progress support was installed
must be stopped and started again to show the bars.

- `--dry-run` - Preview without changes

**Use Case:** Schedule this command to run daily with Windows Task Scheduler. Use
`pwsh.exe` as the program, set the project directory as **Start in**, and pass
`-NoProfile -Command "uv run ayne collect daily"` as the arguments.

### Full Collection

For initial data population or comprehensive updates:

```powershell
# Full collection with limits
ayne collect full --max-tmdb 5000 --max-omdb 1000

# With filters
ayne collect full --min-year 2020 --min-popularity 20

# Unlimited TMDB discovery
ayne collect full --max-omdb 1000

# Include frozen movies in refresh
ayne collect full --include-frozen --refresh-limit 500

# Preview workflow
ayne collect full --dry-run
```

**Options:**

- `--max-tmdb N` - Maximum TMDB discoveries and derived page budget (omitted = unlimited)
- `--max-omdb N` - Maximum OMDB enrichments
- `--discover-pages N` - Global TMDB page cap for discovery; overrides the derived page budget
- `--min-popularity N` - Minimum popularity filter
- `--min-year YYYY` - Minimum release year
- `--refresh-limit N` - Maximum movies to refresh (default: 100)
- `--include-frozen` - Include frozen movies in refresh (force refresh)
- `--dry-run` - Preview without changes

## Validation Commands

### Validate TMDB Data

Check TMDB data quality:

```powershell
# Standard validation
ayne validate tmdb

# Verbose output with samples
ayne validate tmdb --verbose
```

**Checks:**

- Missing titles
- Missing release dates
- Invalid popularity scores
- Invalid vote counts
- Stale data (>90 days old)

### Validate OMDB Data

Check OMDB/IMDb data quality:

```powershell
# Standard validation
ayne validate imdb

# Verbose output with samples
ayne validate imdb --verbose
```

**Checks:**

- Missing IMDb IDs
- Invalid IMDb ratings
- Invalid Metascores
- Unprocessed movies (have ID, no data)
- Stale data (>180 days old)

### Validate All

Run database contract validation followed by the TMDB and OMDB checks:

```powershell
# Validate everything
ayne validate all

# Verbose mode
ayne validate all --verbose
```

## Configuration Commands

### Show Version

Display version and environment info:

```powershell
ayne version
```

### Show Configuration

Display all current settings:

```powershell
ayne config
```

Shows:

- Environment (development/staging/production)
- Log level and format
- Database path
- API endpoints and rate limits
- Filter settings
- Collection limits

## Common Workflows

### Daily Maintenance

```powershell
# Run daily workflow
ayne collect daily --discover --discover-limit 100

# Validate data quality
ayne validate all
```

### Targeted Updates

```powershell
# Update only recent movies
ayne tmdb update --min-year 2024 --max-movies 500

# Enrich high-popularity movies without OMDB data
ayne omdb enrich --max-movies 1000

# Validate specific dataset
ayne validate tmdb
```

### Development/Testing

```powershell
# Preview operations
ayne tmdb update --max-movies 100 --dry-run
ayne omdb enrich --max-movies 50 --dry-run
ayne collect daily --dry-run

# Small test collection
ayne collect full --max-tmdb 100 --max-omdb 50

# Verify database
ayne db test --verbose
ayne db stats
```

## Configuration Override

All commands respect configuration hierarchy:

1. **Environment variables** (highest priority)
2. **.env file**
3. **YAML config** (environment-specific)
4. **CLI arguments**
5. **Code defaults** (lowest priority)

### Examples

```powershell
# Override via environment variable for this PowerShell session
$env:TMDB_MIN_RELEASE_YEAR = "2024"
ayne tmdb update

# Override via .env file
# Edit .env and set: TMDB_MIN_POPULARITY=20
ayne tmdb update

# Override via CLI argument (highest priority for that run)
ayne tmdb update --min-year 2020 --min-popularity 15
```

## Dry Run Best Practices

Always use `--dry-run` when:

- Testing new filter combinations
- Verifying quota usage before large operations
- Debugging unexpected behavior
- Learning command behavior

```powershell
# Safe exploration
ayne tmdb update --full --dry-run
ayne collect daily --discover --dry-run
ayne db init --dry-run
```

## Error Handling

The CLI provides clear error messages and appropriate exit codes:

- **Exit 0**: Success
- **Exit 1**: Error occurred

### Common Issues

**"Import 'typer' could not be resolved"**

```powershell
# Install dependencies
uv sync
```

**"Database not found"**

```powershell
# Initialize database first
ayne db init
```

**"API rate limit exceeded"**

```powershell
# Reduce request rates or increase delays in config
# Check settings with:
ayne config
```

**"No movies discovered"**

```powershell
# Check filters - they might be too restrictive
ayne tmdb update --min-popularity 5 --min-votes 10
```

## Advanced Usage

### Combining Commands

```powershell
# Chain operations (PowerShell)
ayne db init; ayne tmdb update --max-movies 1000; ayne omdb enrich --max-movies 500; ayne validate all

# Conditional execution (PowerShell)
ayne db test
if ($LASTEXITCODE -eq 0) { ayne collect daily }
```

### Logging

Control log level via environment:

```powershell
# Verbose logging
$env:LOG_LEVEL="DEBUG"
ayne collect daily

# Minimal logging
$env:LOG_LEVEL="WARNING"
ayne collect full
```

### JSON Output

For programmatic processing:

```powershell
# Enable JSON logging
$env:USE_JSON_LOGGING="true"
ayne collect daily > collection.json
```

## Help System

Every command has built-in help:

```powershell
# Top-level help
ayne --help

# Group help
ayne db --help
ayne tmdb --help

# Command help
ayne tmdb update --help
ayne collect daily --help
ayne validate all --help
```

## Migration from Scripts

The current workflow is exposed through the `ayne` CLI. The old collection scripts are
not part of the repository anymore, so use the command that matches the operation:

| Operation | CLI command |
| --- | --- |
| Initialize the database | `uv run ayne db init` |
| Test database connectivity | `uv run ayne db test` |
| Discover movies from TMDB | `uv run ayne tmdb update` |
| Enrich discovered movies with TMDB details | `uv run ayne tmdb enrich` |
| Add OMDB ratings and metadata | `uv run ayne omdb enrich` |
| Run the scheduled refresh workflow | `uv run ayne collect daily` |

Benefits of CLI:

- No separate script entry points to maintain
- Consistent configuration through `.env` and environment YAML
- Colored output and progress indicators
- Dry-run support for collection commands
- Command-specific help through `--help`

## See Also

- [Data Collection Workflow](data-collection-workflow.md)
- [Filtering and Configuration](../reference/data-collection-filtering.md)
- [Database Schema](../reference/database.md)

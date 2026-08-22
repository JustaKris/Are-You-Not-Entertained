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

# Run daily refresh
ayne collect daily

# Validate data quality
ayne validate all
```

## Database Commands

### Initialize Database

Create database schema and tables:

```powershell
# Standard initialization
ayne db init

# Force re-initialization (drops existing tables)
ayne db init --force

# Preview what would be created
ayne db init --dry-run
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

## TMDB Commands

The TMDB commands are organized into three distinct operations:

1. **`update`** - Discover new movies (basic info only, fast)
2. **`enrich`** - Fetch detailed data for discovered movies (complete info, slower)
3. **`refresh`** - Update existing movies that need data refresh (age-based)

**⚠️ Important: TMDB API Limits**

- **500-page maximum**: TMDB's discover endpoint has a hard limit of 500 pages (~10,000 movies max per query)
- **Workaround**: Use `--min-year` and `--max-year` to query different time ranges
- **Two-stage process**:
  1. **Discovery** (`tmdb update`): Fast bulk collection (20 movies/request, basic info)
  2. **Enrichment** (`tmdb enrich`): Individual detail fetches (1 movie/request, complete data)

### Discover Movies

Discover and store new movies from TMDB (basic info only):

```powershell
# Full discovery (limited to ~10,000 movies by TMDB API)
ayne tmdb update --full

# Strategy: Use year ranges to work around 500-page limit
ayne tmdb update --min-year 2020 --max-year 2024 --max-movies 5000
ayne tmdb update --min-year 2015 --max-year 2019 --max-movies 5000
ayne tmdb update --min-year 2010 --max-year 2014 --max-movies 5000

# Limited discovery with filters
ayne tmdb update --max-movies 1000 --min-popularity 20 --min-votes 100

# Preview without changes
ayne tmdb update --max-movies 1000 --dry-run
```

**Options:**

- `--full` - Unlimited discovery (automatic year-range splitting handles 500-page limit)
- `--max-movies N` - Limit to N movies
- `--min-popularity N` - Minimum popularity score (default: 10.0)
- `--min-votes N` - Minimum vote count (default: 50)
- `--min-year YYYY` - Minimum release year (default: 1950)
- `--max-year YYYY` - Maximum release year (default: current year)
- `--max-pages N` - Maximum API pages per year range
- `--dry-run` - Preview without making changes

**Note:** The system now automatically handles TMDB's 500-page limit by recursively splitting year ranges. You can safely specify wide ranges without manual adjustment.

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

- `--limit N` - Maximum number of movies to enrich (default: 100)
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

- `--limit N` - Maximum number of movies to refresh (default: 100)
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

**Note:** OMDB has daily API limits. Use `--max-movies` to control quota usage.

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

- `--limit N` - Maximum number of movies to refresh (default: 100)
- `--min-year YYYY` - Only refresh movies from this year onwards
- `--max-year YYYY` - Only refresh movies up to this year
- `--dry-run` - Preview without making changes

## Recommended Workflows

### Initial Data Population

Build your movie database from scratch:

```powershell
# Step 1: Discover movies in chunks (works around 500-page limit)
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

### Working Around TMDB 500-Page Limit

Strategy to collect large datasets:

```powershell
# Collect by decade
ayne tmdb update --min-year 2020 --max-year 2029 --full
ayne tmdb update --min-year 2010 --max-year 2019 --full
ayne tmdb update --min-year 2000 --max-year 2009 --full

# Or by 5-year periods
ayne tmdb update --min-year 2020 --max-year 2024 --max-movies 5000
ayne tmdb update --min-year 2015 --max-year 2019 --max-movies 5000

# Then enrich all discoveries
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
- `--include-frozen` - Include frozen movies in refresh (force refresh)
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

- `--max-tmdb N` - Maximum TMDB discoveries (None = unlimited)
- `--max-omdb N` - Maximum OMDB enrichments
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

Run comprehensive validation:

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
ayne db init --force --dry-run
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

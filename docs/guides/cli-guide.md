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

```bash
# Install package with CLI dependencies
uv sync

# Verify installation
ayne --help
```

## Command Structure

All commands follow this pattern:

```bash
ayne [GROUP] [COMMAND] [OPTIONS]
```

Command groups:

- `db` - Database management
- `tmdb` - TMDB data collection
- `omdb` - OMDB data enrichment
- `collect` - Combined workflows
- `validate` - Data validation

## Quick Start

```bash
# Initialize database
ayne db init

# Test database connectivity
ayne db test

# Discover movies from TMDB
ayne tmdb update --max-movies 1000

# Enrich with OMDB data
ayne omdb update --max-movies 500

# Run daily refresh
ayne collect daily

# Validate data quality
ayne validate all
```

## Database Commands

### Initialize Database

Create database schema and tables:

```bash
# Standard initialization
ayne db init

# Force re-initialization (drops existing tables)
ayne db init --force

# Preview what would be created
ayne db init --dry-run
```

### Test Database

Run connectivity and CRUD tests:

```bash
# Quick test
ayne db test

# Verbose output with statistics
ayne db test --verbose
```

### Show Statistics

Display database statistics:

```bash
ayne db stats
```

## TMDB Commands

### Discover Movies

Discover and store new movies from TMDB:

```bash
# Full discovery (unlimited)
ayne tmdb update --full

# Limited discovery
ayne tmdb update --max-movies 1000

# With filters
ayne tmdb update --min-popularity 20 --min-votes 100 --min-year 2020

# Preview without changes
ayne tmdb update --max-movies 1000 --dry-run
```

**Options:**

- `--full` - Unlimited discovery (overrides `--max-movies`)
- `--max-movies N` - Limit to N movies
- `--min-popularity N` - Minimum popularity score (default: 10.0)
- `--min-votes N` - Minimum vote count (default: 50)
- `--min-year YYYY` - Minimum release year (default: 1950)
- `--max-pages N` - Maximum API pages to fetch
- `--dry-run` - Preview without making changes

### Refresh TMDB Data

Refresh existing TMDB data using age-based strategy:

```bash
# Refresh 100 movies (default)
ayne tmdb refresh

# Custom limit
ayne tmdb refresh --limit 500

# Preview refresh candidates
ayne tmdb refresh --limit 100 --dry-run
```

## OMDB Commands

### Enrich Movies

Add OMDB data (IMDb ratings, box office, etc.):

```bash
# Standard enrichment
ayne omdb update --max-movies 1000

# Preview what would be enriched
ayne omdb update --max-movies 500 --dry-run
```

**Note:** OMDB has daily API limits. Use `--max-movies` to control quota usage.

### Refresh OMDB Data

Refresh existing OMDB data:

```bash
# Refresh 100 movies
ayne omdb refresh --limit 100

# Preview refresh candidates
ayne omdb refresh --limit 200 --dry-run
```

## Collection Workflows

### Daily Refresh

Recommended for scheduled daily runs:

```bash
# Standard daily refresh
ayne collect daily

# With discovery enabled
ayne collect daily --discover --discover-limit 500

# Custom limits
ayne collect daily --tmdb-refresh 200 --omdb-limit 500

# Preview workflow
ayne collect daily --dry-run
```

**Options:**

- `--tmdb-refresh N` - Number of TMDB records to refresh (default: 100)
- `--omdb-limit N` - Maximum OMDB enrichments (uses config default)
- `--discover` - Also discover new movies
- `--discover-limit N` - Limit for discovery
- `--dry-run` - Preview without changes

**Use Case:** Schedule this command to run daily via cron or Task Scheduler:

```bash
# Linux/Mac cron (runs daily at 2 AM)
0 2 * * * cd /path/to/project && uv run ayne collect daily

# Windows Task Scheduler
# Schedule: Daily at 2:00 AM
# Action: Start a program
# Program: pwsh.exe
# Arguments: -Command "cd D:\path\to\project; uv run ayne collect daily"
```

### Full Collection

For initial data population or comprehensive updates:

```bash
# Full collection with limits
ayne collect full --max-tmdb 5000 --max-omdb 1000

# With filters
ayne collect full --min-year 2020 --min-popularity 20

# Unlimited TMDB discovery
ayne collect full --max-omdb 1000

# Preview workflow
ayne collect full --dry-run
```

**Options:**

- `--max-tmdb N` - Maximum TMDB discoveries (None = unlimited)
- `--max-omdb N` - Maximum OMDB enrichments
- `--min-popularity N` - Minimum popularity filter
- `--min-year YYYY` - Minimum release year
- `--refresh-limit N` - Maximum movies to refresh (default: 100)
- `--dry-run` - Preview without changes

## Validation Commands

### Validate TMDB Data

Check TMDB data quality:

```bash
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

```bash
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

```bash
# Validate everything
ayne validate all

# Verbose mode
ayne validate all --verbose
```

## Configuration Commands

### Show Version

Display version and environment info:

```bash
ayne version
```

### Show Configuration

Display all current settings:

```bash
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

### Initial Setup

```bash
# 1. Initialize database
ayne db init

# 2. Test connectivity
ayne db test

# 3. Run full collection
ayne collect full --max-tmdb 5000 --max-omdb 1000

# 4. Validate data
ayne validate all
```

### Daily Maintenance

```bash
# Run daily workflow
ayne collect daily --discover --discover-limit 100

# Validate data quality
ayne validate all
```

### Targeted Updates

```bash
# Update only recent movies
ayne tmdb update --min-year 2024 --max-movies 500

# Enrich high-popularity movies without OMDB data
ayne omdb update --max-movies 1000

# Validate specific dataset
ayne validate tmdb
```

### Development/Testing

```bash
# Preview operations
ayne tmdb update --max-movies 100 --dry-run
ayne omdb update --max-movies 50 --dry-run
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

```bash
# Override via environment variable
export TMDB_MIN_RELEASE_YEAR=2024
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

```bash
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

```bash
# Install dependencies
uv sync
```

**"Database not found"**

```bash
# Initialize database first
ayne db init
```

**"API rate limit exceeded"**

```bash
# Reduce request rates or increase delays in config
# Check settings with:
ayne config
```

**"No movies discovered"**

```bash
# Check filters - they might be too restrictive
ayne tmdb update --min-popularity 5 --min-votes 10
```

## Advanced Usage

### Combining Commands

```bash
# Chain operations (PowerShell)
ayne db init; ayne tmdb update --max-movies 1000; ayne omdb update --max-movies 500; ayne validate all

# Conditional execution (PowerShell)
ayne db test && ayne collect daily
```

### Logging

Control log level via environment:

```bash
# Verbose logging
$env:LOG_LEVEL="DEBUG"
ayne collect daily

# Minimal logging
$env:LOG_LEVEL="WARNING"
ayne collect full
```

### JSON Output

For programmatic processing:

```bash
# Enable JSON logging
$env:USE_JSON_LOGGING="true"
ayne collect daily > collection.json
```

## Help System

Every command has built-in help:

```bash
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

If migrating from old scripts:

| Old Script | New CLI Command |
|------------|-----------------|
| `python scripts/init_database.py` | `ayne db init` |
| `python scripts/test_database.py` | `ayne db test` |
| `python scripts/collect_optimized.py --discover` | `ayne tmdb update` |
| `python scripts/collect_optimized.py` | `ayne collect daily` |

Benefits of CLI:

- ✅ No need for `python scripts/` prefix
- ✅ Cleaner argument names
- ✅ Better error messages
- ✅ Colored output
- ✅ Progress indicators
- ✅ Dry-run support
- ✅ Comprehensive help

## Next Steps

- **Model Training**: `ayne ml train` (coming soon)
- **API Server**: `ayne serve` (coming soon)
- **Data Export**: `ayne export` (coming soon)

## See Also

- [Data Collection Workflow](../reference/data-collection-workflow.md)
- [Configuration Guide](../../configs/README.md)
- [Database Schema](../reference/database.md)

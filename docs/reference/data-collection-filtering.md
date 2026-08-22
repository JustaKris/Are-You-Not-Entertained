# Data Collection Filtering and Configuration

This guide explains how to configure and control TMDB data collection with filtering options to ensure you only collect movies that meet your specific criteria.

## Overview

The data collection system provides configurable filters to control which movies are collected from TMDB. These filters help you:

- **Save API requests** by filtering out irrelevant movies
- **Improve data quality** by setting minimum thresholds
- **Control collection volume** with per-API limits
- **Focus on specific movie categories** (e.g., theatrical releases only)

## Configuration Structure

All filtering settings are managed through:

1. **YAML Configuration Files** (`configs/*.yaml`) - Environment-specific defaults
2. **Settings Class** (`src/ayne/core/config/settings.py`) - Application settings
3. **Command-Line Arguments** (`scripts/collect_optimized.py`) - Runtime overrides

### Configuration Hierarchy

Settings are loaded with the following priority (highest to lowest):

1. Command-line arguments (highest priority)
2. Environment variables
3. YAML configuration file
4. Default values in Settings class

## Available Filters

### 1. TMDB Popularity Filter

**Setting:** `tmdb_min_popularity`
**Type:** Float
**Default:** `10.0`

Minimum TMDB popularity score for movie collection. Popularity is a metric calculated by TMDB based on:

- Number of votes for the day
- Number of views for the day
- Number of users who marked it as a favorite
- Number of users who added it to their watchlist
- Release date

**Example:**

```yaml
tmdb_min_popularity: 10.0  # Only movies with popularity >= 10
```

**Typical ranges:**

- Popular blockbusters: 50+
- Mainstream releases: 10-50
- Niche/indie films: 1-10

### 2. Vote Count Filter

**Setting:** `tmdb_min_vote_count`
**Type:** Integer
**Default:** `50`

Minimum number of user votes required on TMDB. This ensures data quality by filtering out movies with insufficient user engagement.

**Example:**

```yaml
tmdb_min_vote_count: 50  # Only movies with 50+ votes
```

**Recommendations:**

- **High quality dataset:** 200+ votes
- **Balanced dataset:** 50-100 votes
- **Comprehensive dataset:** 10-50 votes

### 3. Release Year Filter

**Settings:**

- `tmdb_min_release_year` (integer)
- `tmdb_max_release_year` (integer or null)

**Defaults:**

- Min: `1950`
- Max: `null` (current year)

Minimum and maximum release years for movie collection. Filters out movies outside the specified range.

**Example:**

```yaml
tmdb_min_release_year: 1950
tmdb_max_release_year:       # null = current year (recommended)
```

**Note:** The system now includes **automatic year-range splitting** that handles TMDB's 500-page limit. You can safely request wide year ranges (e.g., 1950-2024) without manual adjustment - the client will automatically split the request as needed.

### 4. Release Status Filter

**Setting:** `tmdb_allowed_release_statuses`
**Type:** List of strings
**Default:** `["Released", "Post Production", "In Production"]`

Allowed release statuses for movie collection. TMDB provides the following statuses:

- **Released** - Movie has been released in theaters/streaming
- **Post Production** - Filming complete, in editing/post-production
- **In Production** - Currently being filmed
- **Planned** - Announced but not yet in production
- **Rumored** - Unconfirmed project
- **Canceled** - Project canceled

**Example:**

```yaml
tmdb_allowed_release_statuses:
  - Released
  - Post Production
  - In Production
```

**Note:** Status filtering is applied when fetching full movie details, not during initial discovery.

### 5. Collection Limits

Control the maximum number of movies collected per API to manage API quotas and processing time.

#### TMDB Collection Limit

**Setting:** `tmdb_max_movies`
**Type:** Integer or null
**Default:** `null` (unlimited)

Maximum number of movies to collect from TMDB per run.

**Example:**

```yaml
tmdb_max_movies: null  # Unlimited (production)
tmdb_max_movies: 5000  # Limited (staging/testing)
```

#### OMDB Collection Limit

**Setting:** `omdb_max_movies`
**Type:** Integer
**Default:** `1000`

Maximum number of movies to collect from OMDB per run. OMDB has a daily limit of 1000 requests for free accounts.

**Example:**

```yaml
omdb_max_movies: 1000  # Respect OMDB's daily limit
```

### 6. OMDB Year Filtering

**Settings:**

- `omdb_min_release_year` (integer or null)
- `omdb_max_release_year` (integer or null)

**Defaults:** `null` (no limit)

Optional year range filters for OMDB enrichment. Useful for focusing OMDB quota on specific time periods.

**Example:**

```yaml
omdb_min_release_year: 2020  # Only enrich recent movies
omdb_max_release_year:       # null = no upper limit
```

## Configuration Files

### Development Configuration

**File:** `configs/development.yaml`

```yaml
# Data Collection Settings
# TMDB Collection Limits
tmdb_max_movies: null  # null = unlimited

# OMDB Collection Limits
omdb_max_movies: 1000  # OMDB has a 1000 request/day limit

# TMDB Filtering Settings
tmdb_min_popularity: 10.0
tmdb_min_vote_count: 50
tmdb_min_release_year: 1950
tmdb_max_release_year:       # null = current year (auto-split handles 500-page limit)
tmdb_allowed_release_statuses:
  - Released
  - Post Production
  - In Production

# OMDB Filtering Settings
omdb_min_release_year:       # null = no limit
omdb_max_release_year:       # null = no limit
```

### Staging Configuration

**File:** `configs/staging.yaml`

```yaml
# Data Collection Settings
# TMDB Collection Limits
tmdb_max_movies: 5000  # Limit for staging environment

# OMDB Collection Limits
omdb_max_movies: 1000  # OMDB has a 1000 request/day limit

# TMDB Filtering Settings
tmdb_min_popularity: 10.0
tmdb_min_vote_count: 50
tmdb_min_release_year: 1950
tmdb_allowed_release_statuses:
  - Released
  - Post Production
  - In Production
```

### Production Configuration

**File:** `configs/production.yaml`

```yaml
# Data Collection Settings
# TMDB Collection Limits
tmdb_max_movies: null  # null = unlimited for production

# OMDB Collection Limits
omdb_max_movies: 1000  # OMDB has a 1000 request/day limit

# TMDB Filtering Settings
tmdb_min_popularity: 10.0
tmdb_min_vote_count: 50
tmdb_min_release_year: 1950
tmdb_allowed_release_statuses:
  - Released
  - Post Production
  - In Production
```

## Using Filters in Scripts

### Basic Usage

The `collect_optimized.py` script uses configuration defaults automatically:

```bash
# Use all defaults from config
python scripts/collect_optimized.py --discover --refresh-limit 100
```

### Override Filters via Command Line

You can override any filter at runtime:

```bash
# Custom popularity and vote thresholds
python scripts/collect_optimized.py \
  --discover \
  --min-popularity 20.0 \
  --min-votes 100 \
  --min-year 2000 \
  --max-movies 1000 \
  --refresh-limit 100
```

### Command-Line Arguments

| Argument | Type | Description |
| ---------- | ------ | ------------- |
| `--discover` | flag | Enable movie discovery (off by default) |
| `--max-movies` | int | Maximum movies to discover |
| `--max-pages` | int | Maximum pages per year range during discovery |
| `--min-popularity` | float | Minimum TMDB popularity score |
| `--min-votes` | int | Minimum vote count |
| `--min-year` | int | Minimum release year |
| `--refresh-limit` | int | Maximum movies to refresh |
| `--refresh-only` | flag | Skip discovery, only refresh existing |
| `--omdb-max-movies` | int | Maximum OMDB requests per run |

## Programmatic Usage

### Using the Orchestrator

```python
from ayne.core.config import settings
from ayne.data_collection.orchestrator import DataCollectionOrchestrator
from ayne.database.duckdb_client import DuckDBClient

# Create orchestrator
db = DuckDBClient()
orchestrator = DataCollectionOrchestrator(db)

# Discover with custom filters
stats = await orchestrator.discover_and_store_movies(
    max_movies=1000,              # Limit to 1000 movies
    min_popularity=15.0,          # Higher popularity threshold
    min_vote_count=100,           # More votes required
    min_release_year=2010,        # Only recent movies
    allowed_statuses=["Released"] # Only released movies
)

print(f"Discovered {stats} movies")
```

### Using Settings Defaults

```python
from ayne.core.config import settings

# Settings automatically loaded from YAML config
print(f"Min popularity: {settings.tmdb_min_popularity}")
print(f"Min votes: {settings.tmdb_min_vote_count}")
print(f"Min year: {settings.tmdb_min_release_year}")
print(f"Allowed statuses: {settings.tmdb_allowed_release_statuses}")
```

## Filter Recommendations by Use Case

### High-Quality Dataset (Mainstream Movies)

Focus on popular, well-rated movies with significant user engagement.

```yaml
tmdb_min_popularity: 20.0
tmdb_min_vote_count: 200
tmdb_min_release_year: 1990
tmdb_allowed_release_statuses:
  - Released
```

**Best for:** Box office prediction, trend analysis, mainstream recommendations

### Comprehensive Dataset (All Movies)

Broader coverage including niche and indie films.

```yaml
tmdb_min_popularity: 5.0
tmdb_min_vote_count: 20
tmdb_min_release_year: 1950
tmdb_allowed_release_statuses:
  - Released
  - Post Production
```

**Best for:** Academic research, comprehensive catalogs, film studies

### Recent Releases Only

Focus on newest movies with fresh data.

```yaml
tmdb_min_popularity: 10.0
tmdb_min_vote_count: 50
tmdb_min_release_year: 2020
tmdb_allowed_release_statuses:
  - Released
  - Post Production
  - In Production
```

**Best for:** Current box office tracking, upcoming release predictions

### Production-Ready Dataset

Balanced approach for production deployments.

```yaml
tmdb_min_popularity: 10.0
tmdb_min_vote_count: 50
tmdb_min_release_year: 1950
tmdb_allowed_release_statuses:
  - Released
  - Post Production
  - In Production
```

**Best for:** General-purpose applications, user-facing products

## API Quota Management

### Understanding API Limits

**TMDB:**

- No explicit daily limit for API keys
- Rate limiting: ~40 requests per second recommended
- Discovery returns ~20 movies per page

**OMDB:**

- Free tier: 1000 requests per day
- Each movie detail fetch = 1 request

### Strategies to Stay Within Limits

1. **Use `omdb_max_movies`** to cap daily OMDB requests:

   ```yaml
   omdb_max_movies: 800  # Leave buffer for retries
   ```

2. **Prioritize high-value movies** with stricter filters:

   ```yaml
   tmdb_min_popularity: 15.0  # Fewer but better movies
   tmdb_min_vote_count: 100
   ```

3. **Use intelligent refresh** strategy (built-in):
   - Old movies refresh less frequently
   - Recent movies refresh more often
   - Frozen movies don't refresh

4. **Schedule multiple small runs** instead of one large run:

   ```bash
   # Run 4 times per day with 250 OMDB limit each
   python scripts/collect_optimized.py --refresh-limit 250
   ```

## Validation and Testing

### Verify Your Configuration

```python
from ayne.core.config import settings

# Check current settings
print("Current Data Collection Settings:")
print(f"  Environment: {settings.environment}")
print(f"  TMDB Max Movies: {settings.tmdb_max_movies}")
print(f"  OMDB Max Movies: {settings.omdb_max_movies}")
print(f"  Min Popularity: {settings.tmdb_min_popularity}")
print(f"  Min Votes: {settings.tmdb_min_vote_count}")
print(f"  Min Year: {settings.tmdb_min_release_year}")
print(f"  Allowed Statuses: {settings.tmdb_allowed_release_statuses}")
```

### Test Filters

```bash
# Dry run with very restrictive filters
python scripts/collect_optimized.py \
  --discover \
  --min-popularity 50.0 \
  --min-votes 500 \
  --max-movies 10 \
  --refresh-limit 0
```

## Troubleshooting

### Movies Not Being Collected

**Check:**

1. Filters may be too restrictive
2. Increase logging level: `log_level: DEBUG` in config
3. Check API keys are valid
4. Verify network connectivity

### Too Many Movies Being Collected

**Solutions:**

1. Increase `tmdb_min_popularity` threshold
2. Increase `tmdb_min_vote_count` requirement
3. Set `tmdb_max_movies` limit
4. Restrict `tmdb_allowed_release_statuses`

### OMDB Quota Exceeded

**Solutions:**

1. Lower `omdb_max_movies` setting
2. Use `--refresh-only` to skip discovery
3. Increase refresh intervals
4. Upgrade OMDB API plan

## Best Practices

1. **Start Conservative:** Begin with stricter filters and relax as needed
2. **Monitor Metrics:** Track how many movies match your criteria
3. **Environment-Specific:** Use different configs for dev/staging/prod
4. **Document Changes:** Comment your config changes with reasoning
5. **Version Control:** Keep configs in git to track filter evolution
6. **Regular Reviews:** Periodically review if filters still meet your needs

## Related Documentation

- [Data Collection Workflow](data-collection-workflow.md)
- [TMDB Client Reference](tmdb-client.md)
- [CLI Guide](../guides/cli-guide.md)
- [Refresh Strategy](refresh-strategy.md)

# Quick Reference: Data Collection Commands

Quick reference for common data collection tasks with the updated filtering system.

## Prerequisites

1. Ensure your `.env` file contains API keys:

   ```env
   TMDB_API_KEY=your_tmdb_api_key_here
   OMDB_API_KEY=your_omdb_api_key_here
   ```

2. Initialize the database (first time only):

   ```bash
   python scripts/init_database.py
   ```

## Basic Commands

### Refresh Existing Movies Only

Update existing movies without discovering new ones:

```bash
python scripts/collect_optimized.py --refresh-only --refresh-limit 100
```

### Discover New Movies

Discover new movies using config defaults:

```bash
python scripts/collect_optimized.py --discover --max-movies 1000
```

### Discover + Refresh

Full collection workflow:

```bash
python scripts/collect_optimized.py --discover --max-movies 500 --refresh-limit 100
```

## Custom Filtering

### High-Quality Movies Only

Focus on popular, well-rated movies:

```bash
python scripts/collect_optimized.py \
  --discover \
  --min-popularity 20.0 \
  --min-votes 200 \
  --max-movies 500
```

### Recent Movies Only

Collect movies from recent years:

```bash
python scripts/collect_optimized.py \
  --discover \
  --min-year 2020 \
  --max-movies 1000
```

### Comprehensive Collection

Broader coverage with lower thresholds:

```bash
python scripts/collect_optimized.py \
  --discover \
  --min-popularity 5.0 \
  --min-votes 20 \
  --min-year 1950 \
  --max-movies 5000
```

## Managing API Quotas

### Stay Within OMDB Daily Limit

Limit OMDB requests to stay within free tier (1000/day):

```bash
python scripts/collect_optimized.py \
  --discover \
  --max-movies 500 \
  --omdb-max-movies 800 \
  --refresh-limit 200
```

### Small Incremental Updates

Multiple small runs throughout the day:

```bash
# Run 4 times per day
python scripts/collect_optimized.py --refresh-limit 250 --omdb-max-movies 250
```

### Discovery Without OMDB

Discover movies but skip OMDB enrichment:

```bash
python scripts/collect_optimized.py --discover --max-movies 1000 --refresh-limit 0
```

## Testing and Validation

### Dry Run (Small Sample)

Test your filters with a small batch:

```bash
python scripts/collect_optimized.py \
  --discover \
  --min-popularity 50.0 \
  --max-movies 10 \
  --refresh-limit 5
```

### Check Configuration

View current configuration settings:

```python
from ayne.core.config import settings

print(f"Min Popularity: {settings.tmdb_min_popularity}")
print(f"Min Votes: {settings.tmdb_min_vote_count}")
print(f"Min Year: {settings.tmdb_min_release_year}")
print(f"TMDB Max: {settings.tmdb_max_movies}")
print(f"OMDB Max: {settings.omdb_max_movies}")
```

## Common Workflows

### Initial Database Population

First-time setup with comprehensive data:

```bash
# Step 1: Discover movies
python scripts/collect_optimized.py \
  --discover \
  --max-movies 10000 \
  --refresh-limit 0

# Step 2: Enrich with TMDB details (automatic during refresh)
python scripts/collect_optimized.py \
  --refresh-only \
  --refresh-limit 1000

# Step 3: Add OMDB data (within daily limit)
python scripts/collect_optimized.py \
  --refresh-only \
  --refresh-limit 800 \
  --omdb-max-movies 800
```

### Daily Maintenance

Keep data fresh with daily runs:

```bash
# Morning run: Discover new releases
python scripts/collect_optimized.py \
  --discover \
  --max-movies 100 \
  --refresh-limit 200 \
  --omdb-max-movies 300

# Evening run: Refresh older movies
python scripts/collect_optimized.py \
  --refresh-only \
  --refresh-limit 500 \
  --omdb-max-movies 500
```

### Weekly Deep Refresh

Comprehensive update once per week:

```bash
python scripts/collect_optimized.py \
  --discover \
  --max-movies 1000 \
  --refresh-limit 2000 \
  --omdb-max-movies 1000
```

## Scheduled Automation

### Linux/Mac (cron)

Edit crontab:

```bash
crontab -e
```

Add scheduled job:

```cron
# Daily at 3 AM
0 3 * * * cd /path/to/project && python scripts/collect_optimized.py --refresh-only --refresh-limit 800
```

### Windows (Task Scheduler)

Create a batch file `data_collection.bat`:

```batch
@echo off
cd /d "D:\Programming\Repositories\Are-You-Not-Entertained"
python scripts/collect_optimized.py --refresh-only --refresh-limit 800
```

Schedule with Task Scheduler to run daily.

## Command-Line Arguments Reference

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--discover` | flag | Off | Enable movie discovery |
| `--max-movies` | int | Config | Maximum movies to discover |
| `--max-pages` | int | None | Maximum pages per year range (auto-splits if needed) |
| `--min-popularity` | float | Config | Minimum popularity score |
| `--min-votes` | int | Config | Minimum vote count |
| `--min-year` | int | Config | Minimum release year |
| `--refresh-limit` | int | 100 | Maximum movies to refresh |
| `--refresh-only` | flag | Off | Skip discovery |
| `--omdb-max-movies` | int | Config | Maximum OMDB requests |

## Troubleshooting

### No Movies Discovered

**Check:**

```bash
# Verify filters aren't too restrictive
python scripts/collect_optimized.py --discover --min-popularity 1.0 --min-votes 1 --max-movies 10
```

### Rate Limiting Errors

**Solution:** Add delays or reduce concurrency in config:

```yaml
api_rate_limit: 20  # Reduce from 40
```

### OMDB Quota Exceeded

**Check remaining quota:**

```python
from ayne.data_collection.omdb import OMDBClient

client = OMDBClient()
# Check your OMDB account dashboard
```

**Reduce usage:**

```bash
python scripts/collect_optimized.py --omdb-max-movies 500
```

## Best Practices

1. **Start Small:** Test with `--max-movies 10` first
2. **Monitor Logs:** Check logs directory for detailed output
3. **Respect Limits:** Stay within OMDB's 1000/day limit
4. **Schedule Wisely:** Spread collections throughout the day
5. **Use Defaults:** Config defaults are production-ready
6. **Version Control:** Track config changes in git

## Related Documentation

- [Data Collection Filtering](../reference/data-collection-filtering.md) - Detailed filter configuration
- [Data Collection Workflow](../reference/data-collection-workflow.md) - How the system works
- [Configuration Guide](../reference/data-collection-filtering.md#configuration-files) - YAML config details

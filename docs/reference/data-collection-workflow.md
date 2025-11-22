# Data Collection Workflow

Comprehensive guide to how we collect, enrich, and refresh movie data from TMDB and OMDB APIs.

## Overview

Our data collection system uses a **two-phase approach**:

1. **Discovery Phase**: Find movies using TMDB's discover endpoint
2. **Enrichment Phase**: Enhance movies with detailed data from TMDB and OMDB

This is orchestrated by the `DataCollectionOrchestrator` with intelligent refresh strategies to minimize API calls while keeping data current.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  DataCollectionOrchestrator                 │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ TMDB Client  │  │ OMDB Client  │  │ Refresh Strategy│  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │             Rate Limiter (Token Bucket)               │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │  DuckDB Database │
                  │                  │
                  │  • movies        │
                  │  • tmdb_movies   │
                  │  • omdb_movies   │
                  └──────────────────┘
```

## Phase 1: Discovery (TMDB)

### What We Do

Find movies released in specific years that meet quality criteria.

### API Endpoint Used

```
GET https://api.themoviedb.org/3/discover/movie
```

### Query Parameters

```python
params = {
    "primary_release_date.gte": "2024-01-01",  # Start of year
    "primary_release_date.lte": "2024-12-31",  # End of year
    "vote_count.gte": 200,                     # Quality filter
    "sort_by": "primary_release_date.desc",     # Newest first
    "include_adult": "false",                   # Family-friendly
    "include_video": "false",                   # No videos
    "page": 1                                   # Pagination
}
```

### What We Get

Basic movie information:
- `tmdb_id`: TMDB identifier
- `title`: Movie title
- `release_date`: Release date (YYYY-MM-DD)
- `vote_average`: TMDB rating
- `vote_count`: Number of votes
- `popularity`: Popularity score

### Storage

Stored in `movies` table (main table):
```sql
INSERT INTO movies (tmdb_id, title, release_date)
VALUES (?, ?, ?)
ON CONFLICT (tmdb_id) DO UPDATE SET ...
```

### Example Code

```python
# Discover movies from 2020-2024
orchestrator = DataCollectionOrchestrator(db)

stats = await orchestrator.discover_and_store_movies(
    start_year=2020,
    end_year=2024,
    min_vote_count=200,  # Only popular movies
    max_pages=5          # Limit to 5 pages per year
)

print(f"Discovered {stats['discovered']} movies")
```

## Phase 2: Enrichment

### 2A: TMDB Details

**What**: Get comprehensive movie information

**API Endpoint**:
```
GET https://api.themoviedb.org/3/movie/{movie_id}
```

**What We Get**:
- Financial: `budget`, `revenue`
- Metadata: `runtime`, `genres`, `production_companies`
- Identifiers: `imdb_id` (crucial for OMDB)
- Extended info: `overview`, `tagline`, `original_title`

**Storage**: `tmdb_movies` table

### 2B: OMDB Enrichment

**What**: Add ratings and awards data

**Requires**: `imdb_id` from TMDB details (Phase 2A)

**API Endpoint**:
```
GET http://www.omdbapi.com/?i={imdb_id}
```

**What We Get**:
- **Ratings**: IMDb, Rotten Tomatoes, Metacritic
- **Awards**: Text description of wins/nominations
- **Box office**: US box office earnings
- **Additional**: Director, actors, MPAA rating

**Storage**: `omdb_movies` table

## Refresh Strategy

Not all movies need frequent updates. We use **age-based refresh intervals**:

### Movie Age Categories

```python
class MovieAge:
    RECENT = "0-60 days since release"
    ESTABLISHED = "60-180 days"
    MATURE = "180-365 days"
    ARCHIVED = ">365 days"
```

### Refresh Intervals

| Age Category | TMDB Refresh | OMDB Refresh | Rationale |
|-------------|--------------|--------------|-----------|
| **Recent** (0-60 days) | Every 5 days | Every 5 days | Data changes frequently |
| **Established** (60-180 days) | Every 15 days | Every 30 days | Moderate changes |
| **Mature** (180-365 days) | Every 30 days | Every 90 days | Fewer changes |
| **Archived** (>365 days) | Every 90 days | Every 180 days | Stable data |

### Data Freezing

Movies can be "frozen" (no more automatic updates) if:
- Age > 365 days
- No data changes for 3 consecutive refresh cycles

This saves API calls for stable, old movies.

### Example: Refresh Decision

```python
# Movie released 100 days ago
release_date = datetime.now() - timedelta(days=100)

# Age category: ESTABLISHED (60-180 days)
age = get_movie_age(release_date)  # Returns MovieAge.ESTABLISHED

# TMDB: Refresh if last update > 15 days ago
needs_tmdb = needs_tmdb_refresh(release_date, last_tmdb_update)

# OMDB: Refresh if last update > 30 days ago
needs_omdb = needs_omdb_refresh(release_date, last_omdb_update)
```

## Complete Workflow Example

### Scenario: Collect 2024 Movies

```python
from src.data_collection.orchestrator import DataCollectionOrchestrator
from src.database.duckdb_client import DuckDBClient

# Initialize
db = DuckDBClient()
orchestrator = DataCollectionOrchestrator(db)

# Run full collection workflow
stats = await orchestrator.run_full_collection(
    # Discovery settings
    discover_start_year=2024,
    discover_end_year=2024,
    discover_min_vote_count=200,
    max_discover_pages=10,
    
    # Refresh settings
    refresh_limit=100  # Update up to 100 existing movies
)

print(f"""
Collection Complete:
- Movies discovered: {stats['discovered']}
- TMDB updated: {stats['tmdb_updated']}
- OMDB updated: {stats['omdb_updated']}
- Movies frozen: {stats['frozen']}
""")

# Cleanup
await orchestrator.close()
db.close()
```

### What Happens Internally

1. **Discovery**:
   ```
   → TMDB discover API (2024-01-01 to 2024-12-31)
   → Paginate through results
   → Normalize data
   → Store in `movies` table
   ```

2. **Identify Movies for Refresh**:
   ```
   → Query database for movies needing updates
   → Apply age-based refresh rules
   → Exclude frozen movies
   → Return up to 100 movies
   ```

3. **Calculate Refresh Plan**:
   ```
   For each movie:
     → Check release date and last update times
     → Determine: needs_tmdb, needs_omdb
   ```

4. **Fetch TMDB Details**:
   ```
   → Extract tmdb_ids for movies needing TMDB updates
   → Batch fetch with rate limiting
   → Normalize and store in `tmdb_movies`
   → Update `last_tmdb_update` timestamp
   ```

5. **Fetch OMDB Data**:
   ```
   → Extract imdb_ids from `tmdb_movies` for movies needing OMDB
   → Batch fetch with rate limiting
   → Normalize and store in `omdb_movies`
   → Update `last_omdb_update` timestamp
   ```

6. **Freeze Check**:
   ```
   → For each updated movie:
     → If >365 days old AND stable for 3 cycles
     → Set `data_frozen = TRUE`
   ```

## Rate Limiting & Concurrency

### Token Bucket Algorithm

Both API clients share the same rate limiting approach:

```python
class AsyncRateLimiter:
    def __init__(self, requests_per_second=4.0, max_concurrent=10):
        self.tokens = requests_per_second  # Current tokens
        self.max_tokens = requests_per_second  # Bucket capacity
        self.refill_rate = requests_per_second  # Tokens/second
        self.semaphore = asyncio.Semaphore(max_concurrent)
```

### How It Works

```
1. Request wants to make API call
2. Check if token available
   └─ If yes: consume token, proceed
   └─ If no: wait for token refill
3. Token refills at rate of `requests_per_second`
4. Semaphore limits concurrent requests
```

### Configuration

```python
# TMDB: More aggressive (stable API)
tmdb_client = TMDBClient(
    requests_per_second=4.0,
    max_concurrent=10
)

# OMDB: More conservative (stricter limits)
omdb_client = OMDBClient(
    requests_per_second=2.0,
    max_concurrent=5
)
```

## Error Handling & Resilience

### Automatic Retries

```python
# Both clients use exponential backoff
await retry_with_backoff(
    func=make_request,
    retry_count=3,
    base_delay=1.0,    # First retry after 1s
    max_delay=10.0     # Max 10s between retries
)
```

**Retry schedule**:
- Attempt 1: Immediate
- Attempt 2: Wait 1s
- Attempt 3: Wait 2s
- Attempt 4: Wait 4s

### Graceful Degradation

```python
# Individual failures don't stop batch processing
results = await asyncio.gather(*tasks, return_exceptions=True)

for result in results:
    if isinstance(result, Exception):
        logger.error(f"Failed: {result}")
        # Continue processing other movies
    else:
        movies.append(result)
```

### Partial Success

If 100 movies are queued for OMDB update:
- 95 succeed → Store those 95
- 5 fail → Log errors, continue
- Next refresh cycle will retry the 5 failures

## Database Schema

### Primary Table: `movies`

```sql
CREATE TABLE movies (
    movie_id INTEGER PRIMARY KEY,
    tmdb_id INTEGER UNIQUE,
    imdb_id VARCHAR,
    title VARCHAR,
    release_date DATE,
    
    -- Tracking timestamps
    last_tmdb_update TIMESTAMP,
    last_omdb_update TIMESTAMP,
    last_full_refresh TIMESTAMP,
    
    -- Freezing for stable movies
    data_frozen BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Detail Tables

**`tmdb_movies`**: Full TMDB data
- Linked by `tmdb_id`
- Contains: budget, revenue, genres, etc.

**`omdb_movies`**: OMDB enrichment
- Linked by `imdb_id`
- Contains: ratings, awards, box office

## Performance Considerations

### API Call Budgets

**Daily limits** (approximate):
- TMDB: 40,000 requests/day (free tier)
- OMDB: 1,000 requests/day (free tier)

**Our typical usage**:
- Discovery: ~50 requests/year (with pagination)
- Details: ~100 movies/refresh × 2 APIs = 200 requests
- Total: ~250 requests per full collection run

**Sustainable frequency**:
- Run discovery: Weekly or monthly
- Run refresh: Daily (100 movies × 2 APIs = 200 requests)

### Batch Size Recommendations

```python
# Discovery: One year at a time
discover_movies(start_year=2024, end_year=2024)

# Refresh: 50-100 movies per run
refresh_limit=100  # Keeps us well under daily limits
```

### Concurrency Limits

```python
# Safe defaults
tmdb_client = TMDBClient(
    requests_per_second=4.0,   # Conservative
    max_concurrent=10          # Balance speed/stability
)

omdb_client = OMDBClient(
    requests_per_second=2.0,   # Extra conservative
    max_concurrent=5           # Respect free tier
)
```

## Monitoring & Logging

### Key Metrics to Track

1. **API Request Counts**: Track daily usage
2. **Success Rates**: % of successful requests
3. **Refresh Coverage**: % of movies up-to-date
4. **Frozen Movies**: Count of stable, frozen movies
5. **Error Types**: Network, rate limit, not found, etc.

### Log Levels

```python
# INFO: Normal operations
logger.info("Discovered 150 movies for year 2024")

# WARNING: Potential issues
logger.warning("No valid IMDb IDs found for OMDB fetch")

# ERROR: Failures
logger.error("Failed to fetch TMDB details for movie 12345")
```

## Best Practices

### 1. Start Small

```python
# Test with small batches first
stats = await orchestrator.run_full_collection(
    discover_start_year=2024,
    max_discover_pages=1,  # Just first page
    refresh_limit=10       # Just 10 movies
)
```

### 2. Monitor API Quotas

```python
# Check usage regularly
# TMDB: https://www.themoviedb.org/settings/api
# OMDB: Check your email for daily reports
```

### 3. Use Refresh Limits

```python
# Don't try to update everything at once
refresh_limit=100  # Reasonable daily batch
```

### 4. Respect Data Freezing

```python
# Let old, stable movies stay frozen
include_frozen=False  # Default behavior
```

### 5. Schedule Appropriately

```bash
# Daily refresh (cron example)
0 2 * * * python scripts/collect_optimized.py --refresh-only --refresh-limit 100

# Weekly discovery
0 3 * * 0 python scripts/collect_optimized.py --start-year 2024 --end-year 2024
```

## Troubleshooting

### Problem: No OMDB Data

**Diagnosis**:
```sql
-- Check for missing IMDb IDs
SELECT COUNT(*) FROM movies m
LEFT JOIN tmdb_movies t ON m.tmdb_id = t.tmdb_id
WHERE t.imdb_id IS NULL;
```

**Solution**: Ensure TMDB details fetched first

### Problem: Rate Limit Errors

**Solution**: Reduce rate
```python
client = TMDBClient(requests_per_second=2.0)  # Slower
```

### Problem: Stale Data

**Check**:
```sql
SELECT COUNT(*) FROM movies
WHERE last_tmdb_update < CURRENT_DATE - INTERVAL '30 days';
```

**Solution**: Increase refresh limit or run more frequently

## Related Documentation

- [TMDB Client](tmdb-client.md) - TMDB API details
- [OMDB Client](omdb-client.md) - OMDB API details
- [Refresh Strategy](refresh-strategy.md) - Age-based refresh logic
- [Rate Limiting](rate-limiting.md) - Token bucket implementation
- [Data Orchestration](orchestration.md) - Orchestrator details

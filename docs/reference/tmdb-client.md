# TMDB API Client

The TMDB (The Movie Database) API client provides async/await functionality for efficient movie data collection with built-in rate limiting and retry logic.

## Overview

The TMDB client is designed for batch data collection with the following features:

- **Async/await** using `httpx.AsyncClient` for concurrent requests
- **Rate limiting** via token bucket algorithm (default: 4 requests/second)
- **Automatic retries** with exponential backoff for failed requests
- **Concurrent request management** with configurable max concurrent requests
- **Normalized data** returned in consistent format

## Key Endpoints Used

### Discover Movies — `/discover/movie`

**Purpose**: Find movies by year and filter criteria

**Parameters**:

- `primary_release_date.gte`: Start date (YYYY-MM-DD)
- `primary_release_date.lte`: End date (YYYY-MM-DD)
- `vote_count.gte`: Minimum vote count (default: 200)
- `sort_by`: Sort order (default: "primary_release_date.desc")
- `include_adult`: Include adult content (default: false)
- `include_video`: Include video content (default: false)
- `page`: Page number for pagination

**Response**: List of movies with basic information (id, title, release_date, etc.)

**Rate Limit**: 4 requests/second (configurable)

### Movie Details — `/movie/{movie_id}`

**Purpose**: Fetch detailed information for a specific movie

**Parameters**:

- `movie_id`: TMDB movie ID

**Response**: Comprehensive movie data including:

- Basic info (title, overview, release_date)
- Financial data (budget, revenue)
- Metadata (runtime, genres, production companies)
- External IDs (IMDb ID)

**Rate Limit**: 4 requests/second (configurable)

## Data Collection Strategy

### Discovery Phase

1. **Year-based discovery**: Iterate through specified year range
2. **Pagination handling**: Automatically fetch all pages for each year
3. **Concurrent page fetching**: Fetch multiple pages simultaneously (with rate limiting)
4. **Data normalization**: Convert API responses to consistent format

### Detail Fetching

1. **Batch processing**: Fetch details for multiple movies concurrently
2. **Progress tracking**: Optional callbacks for monitoring progress
3. **Error handling**: Continue on individual failures, log errors
4. **Type safety**: Return typed dictionaries with known fields

## Usage Examples

### Basic Initialization

```python
from ayne.data_collection.tmdb import TMDBClient

# Initialize with default settings
client = TMDBClient()

# Initialize with custom settings
client = TMDBClient(
    api_key="your_api_key",
    requests_per_second=2.0,  # Slower rate
    max_concurrent=5,         # Fewer concurrent requests
    output_dir=Path("custom/path")
)
```

### Discover Movies

```python
# Discover movies for single year
movies = await client.discover_movies(start_year=2024)

# Discover movies for year range
movies = await client.discover_movies(
    start_year=2020,
    end_year=2024,
    min_vote_count=500,  # Higher threshold
    max_pages=10         # Limit pages per year
)
```

### Fetch Movie Details

```python
# Single movie
details = await client.get_movie_details(tmdb_id=550)

# Batch of movies
tmdb_ids = [550, 551, 552, 553]
movies = await client.get_batch_movie_details(tmdb_ids)

# With progress callback
def progress(current, total):
    print(f"Fetched {current}/{total} movies")

movies = await client.get_batch_movie_details(
    tmdb_ids,
    progress_callback=progress
)
```

## Rate Limiting Implementation

### Token Bucket Algorithm

- **Tokens**: Represent allowed requests
- **Refill rate**: Tokens added per second (requests_per_second)
- **Bucket capacity**: Maximum burst size
- **Semaphore**: Controls concurrent request limit

### Configuration

```python
# Default settings (4 req/s, 10 concurrent)
client = TMDBClient()

# Conservative settings (2 req/s, 5 concurrent)
client = TMDBClient(
    requests_per_second=2.0,
    max_concurrent=5
)

# Aggressive settings (8 req/s, 20 concurrent)
# WARNING: May hit API rate limits
client = TMDBClient(
    requests_per_second=8.0,
    max_concurrent=20
)
```

## Error Handling

### Retry Logic

- **Automatic retries**: Up to 3 attempts for failed requests
- **Exponential backoff**: Increasing delays between retries (1s, 2s, 4s)
- **Exception types handled**:
  - Network errors (connection timeouts, DNS failures)
  - HTTP errors (429 rate limit, 500 server errors)
  - Timeout errors

### Graceful Degradation

- Individual movie failures don't stop batch processing
- Failed requests logged with details
- Partial results returned for successful fetches

## Data Normalization

### Discover Results

Normalized fields:

- `tmdb_id`: Movie ID
- `title`: Movie title
- `release_date`: Release date (YYYY-MM-DD)
- `vote_average`: Average rating
- `vote_count`: Number of votes
- `popularity`: Popularity score

### Movie Details

Normalized fields:

- `tmdb_id`: Movie ID
- `imdb_id`: IMDb ID (for OMDB integration)
- `title`: Movie title
- `original_title`: Original language title
- `release_date`: Release date
- `runtime`: Runtime in minutes
- `budget`: Production budget (USD)
- `revenue`: Box office revenue (USD)
- `genres`: List of genre names
- `production_companies`: List of production company names
- `overview`: Plot summary

## Integration with Orchestrator

The TMDB client is typically used via the `DataCollectionOrchestrator`:

```python
from ayne.data_collection.orchestrator import DataCollectionOrchestrator
from ayne.database.duckdb_client import DuckDBClient

# Create orchestrator (includes TMDB client)
db = DuckDBClient()
orchestrator = DataCollectionOrchestrator(db)

# Run collection
stats = await orchestrator.run_full_collection(
    discover_start_year=2024,
    refresh_limit=100
)
```

## Best Practices

1. **Use conservative rate limits** initially to avoid API bans
2. **Monitor API quota usage** via TMDB dashboard
3. **Implement backoff strategies** if hitting rate limits frequently
4. **Cache results** to avoid redundant API calls
5. **Use batch operations** instead of individual requests when possible
6. **Handle errors gracefully** and log failures for investigation

## API Reference

For complete TMDB API documentation, see: [TMDB API Docs](https://developers.themoviedb.org/3)

## Related Components

- [Rate Limiting](rate-limiting.md) - Token bucket implementation
- [Data Orchestration](orchestration.md) - High-level collection workflow
- [Refresh Strategy](refresh-strategy.md) - Intelligent refresh logic

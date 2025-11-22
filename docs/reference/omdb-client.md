# OMDB API Client

The OMDB (Open Movie Database) API client provides async functionality for fetching detailed movie ratings, awards, and metadata to enrich the core TMDB data.

## Overview

The OMDB client is designed to complement TMDB data with additional ratings and metadata:

- **Async/await** using `httpx.AsyncClient` for concurrent requests
- **Rate limiting** via shared `AsyncRateLimiter` (default: 2 requests/second)
- **Batch operations** for efficient multi-movie fetching
- **Automatic retries** with exponential backoff
- **Data normalization** to consistent storage format
- **Graceful error handling** for missing or invalid IMDb IDs

## API Endpoint

OMDB uses a single, simple endpoint for all queries:

### Movie by IMDb ID

**Base URL**: `http://www.omdbapi.com/`

**Method**: GET

**Required Parameters**:

- `apikey`: Your OMDB API key
- `i`: IMDb ID (e.g., "tt0111161" for The Shawshank Redemption)

**Optional Parameters**:

- `plot`: "short" (default) or "full"
- `type`: "movie", "series", or "episode"

**Response**: JSON object with movie details

**Rate Limit**: Free tier typically allows 1,000 requests/day

## Data We Collect

### Core OMDB Fields

The OMDB API provides rich data that complements TMDB:

**Ratings & Scores**:

- `imdbRating`: IMDb user rating (0-10)
- `imdbVotes`: Number of IMDb votes (e.g., "2,500,000")
- `Metascore`: Metacritic score (0-100)
- `Ratings`: Array of ratings from multiple sources:
  - IMDb
  - Rotten Tomatoes (percentage)
  - Metacritic

**Awards & Recognition**:

- `Awards`: Text description (e.g., "Won 2 Oscars. 12 wins & 15 nominations")
- Useful for analyzing critical acclaim vs. commercial success

**Additional Metadata**:

- `Rated`: MPAA rating (G, PG, PG-13, R, etc.)
- `Runtime`: Length in minutes
- `Genre`: Comma-separated genres
- `Director`: Director name(s)
- `Writer`: Writer name(s)
- `Actors`: Main cast (comma-separated)
- `Plot`: Synopsis
- `Language`: Primary language(s)
- `Country`: Country of origin
- `BoxOffice`: Box office earnings (US format, e.g., "$28,341,469")
- `Released`: Release date

## Usage Examples

### Basic Initialization

```python
from ayne.data_collection.omdb import OMDBClient

# Initialize with default settings
client = OMDBClient()

# Initialize with custom settings
client = OMDBClient(
    api_key="your_api_key",
    requests_per_second=1.0,  # Slower rate for free tier
    max_concurrent=3,         # Fewer concurrent requests
    output_dir=Path("custom/path")
)
```

### Fetch Single Movie

```python
# Fetch by IMDb ID
movie = await client.get_movie_by_imdb_id("tt0111161")

if movie:
    print(f"Title: {movie['title']}")
    print(f"IMDb Rating: {movie['imdb_rating']}")
    print(f"Metascore: {movie['metascore']}")
    print(f"Awards: {movie['awards']}")
```

### Batch Fetching

```python
# Fetch multiple movies
imdb_ids = ["tt0111161", "tt0068646", "tt0071562", "tt0468569"]
movies = await client.get_batch_movies(imdb_ids)

print(f"Successfully fetched {len(movies)} movies")
```

### With Progress Tracking

```python
def progress_callback(current, total):
    print(f"Progress: {current}/{total} ({current/total*100:.1f}%)")

imdb_ids = ["tt0111161", "tt0068646", "tt0071562"]
movies = await client.get_batch_movies(
    imdb_ids,
    progress_callback=progress_callback
)
```

## Rate Limiting Strategy

### Why Conservative Limits?

OMDB has stricter rate limits than TMDB:

- **Free tier**: 1,000 requests/day
- **Paid tier**: Higher limits available

### Our Default Configuration

```python
# Default: 2 requests/second, 5 concurrent
client = OMDBClient(
    requests_per_second=2.0,
    max_concurrent=5
)
```

This translates to:

- ~7,200 requests/hour (theoretical max)
- ~172,800 requests/day (theoretical max)
- In practice, much lower due to concurrent limits

### Token Bucket Implementation

Uses shared `AsyncRateLimiter`:

- Tokens replenish at `requests_per_second` rate
- Semaphore limits concurrent requests
- Async context manager ensures proper resource handling

## Error Handling

### Automatic Retries

```python
# Configured in _request method
await retry_with_backoff(
    make_request,
    retry_count=3,      # Try up to 3 times
    base_delay=1.0,     # Start with 1s delay
    max_delay=10.0,     # Max 10s between retries
    exceptions=(httpx.HTTPError, httpx.TimeoutException)
)
```

### Graceful Degradation

```python
# Individual failures don't stop batch processing
movies = await client.get_batch_movies(imdb_ids)

# Returns only successful fetches
# Failures are logged but don't raise exceptions
```

### Common Error Scenarios

1. **Invalid IMDb ID**: Returns `None`, logs error
2. **Network timeout**: Retries up to 3 times
3. **Rate limit exceeded**: Backs off automatically
4. **Movie not found**: Returns `None`, not an error

## Data Normalization

Raw OMDB responses are normalized before storage.

### Input (Raw OMDB Response)

```json
{
  "Response": "True",
  "imdbID": "tt0111161",
  "Title": "The Shawshank Redemption",
  "imdbRating": "9.3",
  "imdbVotes": "2,500,000",
  "Metascore": "80",
  "Awards": "Nominated for 7 Oscars...",
  "Ratings": [
    {"Source": "Internet Movie Database", "Value": "9.3/10"},
    {"Source": "Rotten Tomatoes", "Value": "91%"},
    {"Source": "Metacritic", "Value": "80/100"}
  ],
  "BoxOffice": "$28,341,469",
  ...
}
```

### Output (Normalized)

```python
{
    "imdb_id": "tt0111161",
    "title": "The Shawshank Redemption",
    "imdb_rating": 9.3,              # Converted to float
    "imdb_votes": 2500000,           # Cleaned and converted
    "metascore": 80,                 # Converted to int
    "rotten_tomatoes_score": 91,    # Extracted and converted
    "awards": "Nominated for 7 Oscars...",
    "box_office": 28341469,          # Cleaned and converted
    # ... other normalized fields
}
```

### Normalization Logic

Located in `src/data_collection/omdb/normalizers.py`:

```python
def normalize_movie_response(data: Dict) -> Optional[Dict[str, Any]]:
    """Convert OMDB API response to normalized format.
    
    Handles:
    - Type conversions (strings to numbers)
    - Cleaning (remove commas, currency symbols)
    - Extraction (ratings from nested structure)
    - Null handling (empty strings to None)
    """
```

## Integration with Data Collection

### Typical Workflow

OMDB data is fetched **after** TMDB data:

1. **TMDB Discovery**: Find movies by year/criteria
2. **TMDB Details**: Fetch full details including `imdb_id`
3. **OMDB Enrichment**: Use IMDb IDs to fetch ratings/awards
4. **Storage**: Save to `omdb_movies` table

### Orchestrator Integration

```python
from ayne.data_collection.orchestrator import DataCollectionOrchestrator

# Orchestrator manages the workflow
orchestrator = DataCollectionOrchestrator(db)

# Refresh workflow automatically:
# 1. Determines which movies need OMDB updates
# 2. Extracts their IMDb IDs from tmdb_movies table
# 3. Fetches OMDB data in batches
# 4. Updates omdb_movies table
# 5. Updates timestamps in movies table
stats = await orchestrator.refresh_movie_data(
    movies_df,
    fetch_omdb=True
)
```

### Why After TMDB?

- OMDB requires IMDb IDs
- TMDB provides IMDb IDs in movie details
- Allows us to skip OMDB for movies without IMDb IDs

## Database Schema

### Storage Table: `omdb_movies`

```sql
CREATE TABLE omdb_movies (
    imdb_id VARCHAR PRIMARY KEY,
    title VARCHAR,
    year INTEGER,
    rated VARCHAR,              -- MPAA rating
    released DATE,
    runtime INTEGER,            -- minutes
    genre VARCHAR,
    director VARCHAR,
    writer VARCHAR,
    actors VARCHAR,
    plot TEXT,
    language VARCHAR,
    country VARCHAR,
    awards TEXT,
    imdb_rating DOUBLE,
    imdb_votes INTEGER,
    metascore INTEGER,
    rotten_tomatoes_score INTEGER,
    box_office BIGINT,          -- USD cents
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Relationship to Other Tables

```
movies (main table)
  ├─ tmdb_id → tmdb_movies (TMDB details)
  │            └─ imdb_id → omdb_movies (OMDB enrichment)
  ├─ imdb_id (copied from tmdb_movies)
  └─ last_omdb_update (timestamp tracking)
```

## Best Practices

### 1. Always Check for IMDb IDs

```python
# Filter out movies without IMDb IDs before calling OMDB
imdb_ids = [id for id in movie_ids if id and id.startswith('tt')]
```

### 2. Respect Rate Limits

```python
# For free tier, be extra conservative
client = OMDBClient(requests_per_second=1.0)
```

### 3. Handle Missing Data

```python
# OMDB data is optional enrichment
movie = await client.get_movie_by_imdb_id(imdb_id)
if movie:
    # Use OMDB data
else:
    # Continue without OMDB data
```

### 4. Batch Operations

```python
# Always prefer batch operations over individual requests
# Bad: Multiple individual calls
for imdb_id in imdb_ids:
    await client.get_movie_by_imdb_id(imdb_id)

# Good: Single batch call
await client.get_batch_movies(imdb_ids)
```

### 5. Monitor API Quota

- Track daily request count
- Set up alerts for quota thresholds
- Consider paid tier if exceeding free limits

## Comparison: OMDB vs TMDB

| Feature | TMDB | OMDB |
|---------|------|------|
| **Primary Use** | Discovery & details | Ratings & awards |
| **Rate Limit** | 4/sec (we use) | 2/sec (we use) |
| **Free Tier** | 40,000/day | 1,000/day |
| **Identifier** | `tmdb_id` | `imdb_id` |
| **Ratings** | User votes only | IMDb, RT, Metacritic |
| **Box Office** | Budget/revenue | US box office |
| **Awards** | ❌ No | ✅ Yes |
| **Collection Order** | First | Second |

## Troubleshooting

### OMDB Data Not Updating

**Check**:

1. Is the movie in `tmdb_movies` with valid `imdb_id`?
2. Does the movie pass refresh interval check?
3. Are OMDB API credentials configured?

```python
# Debug: Check if movie has IMDb ID
query = "SELECT tmdb_id, imdb_id FROM tmdb_movies WHERE tmdb_id = ?"
result = db.query(query, [12345])
```

### Rate Limit Errors

**Solution**: Reduce `requests_per_second`

```python
client = OMDBClient(requests_per_second=0.5)  # Slower
```

### Missing Ratings

Some movies may not have all rating sources:

- IMDb rating usually present
- Rotten Tomatoes may be missing
- Metacritic may be missing

This is normal and handled by normalization.

## API Reference

For complete OMDB API documentation: [OMDB API Docs](http://www.omdbapi.com/)

## Related Components

- [TMDB Client](tmdb-client.md) - Primary data source
- [Data Orchestration](orchestration.md) - Workflow coordination
- [Refresh Strategy](refresh-strategy.md) - When to update OMDB data
- [Rate Limiting](rate-limiting.md) - Token bucket implementation

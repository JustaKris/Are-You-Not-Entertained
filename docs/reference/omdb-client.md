# OMDB API Client

> **Status**: Template - Content to be filled in

The OMDB (Open Movie Database) API client provides async functionality for fetching detailed movie ratings and metadata.

## Overview

- Async/await using `httpx.AsyncClient`
- Rate limiting (default: 2 requests/second)
- Batch operations for multiple movies
- Data normalization

## Key Endpoints

### Movie by IMDb ID

**Purpose**: Fetch movie details using IMDb ID

**Parameters**:
- `i`: IMDb ID (e.g., "tt0111161")
- `plot`: Plot length ("short" or "full")

**Response**:
- Ratings (IMDb, Rotten Tomatoes, Metacritic)
- Awards information
- Cast and crew
- Additional metadata

## Usage Examples

```python
from src.data_collection.omdb import OMDBClient

# Initialize client
client = OMDBClient()

# Fetch single movie
movie = await client.get_movie_by_imdb_id("tt0111161")

# Fetch batch
imdb_ids = ["tt0111161", "tt0068646", "tt0071562"]
movies = await client.get_batch_movies(imdb_ids)
```

## Rate Limiting

- Default: 2 requests/second
- Configurable max concurrent requests
- Token bucket algorithm

## Data Normalization

Normalized fields:
- `imdb_id`: IMDb identifier
- `imdb_rating`: IMDb rating (0-10)
- `imdb_votes`: Number of IMDb votes
- `metascore`: Metacritic score (0-100)
- `rotten_tomatoes`: Rotten Tomatoes score
- Additional fields...

## Integration

Used by `DataCollectionOrchestrator` to enrich movies with ratings and awards data after TMDB collection.

## Related Components

- [TMDB Client](tmdb-client.md)
- [Data Orchestration](orchestration.md)
- [Rate Limiting](rate-limiting.md)

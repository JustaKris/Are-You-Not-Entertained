# Rate Limiting

> **Status**: Template - Content to be filled in

Token bucket algorithm implementation for API rate limiting.

## Overview

Shared rate limiter used by all API clients to prevent exceeding API quotas.

## Token Bucket Algorithm

- **Tokens**: Represent allowed requests
- **Bucket capacity**: Maximum burst size
- **Refill rate**: Tokens added per second
- **Semaphore**: Controls concurrent requests

## Implementation

```python
from ayne.data_collection.rate_limiter import AsyncRateLimiter

# Create rate limiter
limiter = AsyncRateLimiter(
    requests_per_second=4.0,
    max_concurrent=10
)

# Use in async context
async with limiter:
    # Make API request
    response = await client.get(url)
```

## Configuration

Default settings by API:

- **TMDB**: 4 req/s, 10 concurrent
- **OMDB**: 2 req/s, 5 concurrent

## Retry Logic

Exponential backoff for failed requests:

- Retry count: 3 attempts
- Backoff: 1s, 2s, 4s
- Handles: Network errors, timeouts, rate limit responses

## Related Components

- [TMDB Client](tmdb-client.md)
- [OMDB Client](omdb-client.md)

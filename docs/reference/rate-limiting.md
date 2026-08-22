# Rate Limiting And Retries

AYNE applies request pacing and bounded concurrency inside each asynchronous provider
client. The limiter prevents a client from issuing requests too quickly and uses a
semaphore to bound in-flight requests.

## Provider Defaults

| Client | Requests per second | Delay between requests | Maximum concurrent requests |
| --- | ---: | ---: | ---: |
| TMDB | `4.0` | `0.25s` | `10` |
| OMDB | `2.0` | `0.5s` | `5` |
| The Numbers | `settings.numbers_requests_per_second` (default `1.0`) | `1 / rate` (`1.0s` by default) | `1` |

The The Numbers defaults are intentionally conservative because the client scrapes
public HTML pages and has no official API. Its CLI also limits the number of movies per
run through `numbers_max_movies`. Adjust `numbers_requests_per_second` in the selected
file under `configs/`; the development default of `1.0` gives approximately `1.0s`
between requests, while `0.15` gives approximately `6.7s` between requests.
The client permits one request at a time and records each attempted candidate request,
including attempts that return a missing page.

## Request Limiter

`AsyncRateLimiter` combines a minimum delay between requests with an `asyncio.Semaphore`:

```python
from ayne.data_collection.rate_limiter import AsyncRateLimiter

limiter = AsyncRateLimiter(requests_per_second=2.0, max_concurrent=5)

async with limiter:
    response = await client.get(url)
```

The limiter is normally created and owned by the provider client. It is not a shared
global limiter across all providers. Configure a custom rate when constructing a client
in a controlled integration or test.

## Retry Behavior

Provider clients use `retry_with_backoff` for transient HTTP and network failures. The
delay doubles from the base delay and is capped by the configured maximum. HTTP 429
responses are retried with the same backoff. HTTP 401 responses are treated as quota or
credential failures and are raised immediately.

The default retry counts are three attempts for TMDB and OMDB and two attempts for The
Numbers. Non-transient client errors such as 400, 401, and 404 are raised immediately;
408 and 429 responses, server errors, and network errors are retried. A retry does not
bypass the rate limiter; each attempt must acquire it.

```python
from ayne.data_collection.rate_limiter import retry_with_backoff

result = await retry_with_backoff(
    make_request,
    retry_count=3,
    base_delay=1.0,
    max_delay=10.0,
)
```

## Quota Tracking

Rate limiting controls request frequency. It does not by itself track a provider's
daily quota. AYNE records requests in `api_usage_daily`; OMDB enrichment checks the
remaining configured daily budget before starting a batch and records partial successful
usage when a batch stops. The Numbers usage is observational rather than a provider quota.
See the
[filtering reference](data-collection-filtering.md) for command-level quota controls.

## Operational Guidance

- Keep provider defaults unless you have verified the provider's current terms.
- Use `--max-movies`, `--limit`, or the combined workflow limits to bound a run.
- Use `--dry-run` to inspect candidate counts without making provider requests.
- Treat repeated 401 or 429 responses as a configuration or quota problem rather than
  increasing retry counts.
- Keep The Numbers runs small and avoid parallel scraping.

## Related Documentation

- [TMDB Client](tmdb-client.md) - Discovery and detail requests
- [OMDB Client](omdb-client.md) - Enrichment and quota behavior
- [Data Collection Workflow](../guides/data-collection-workflow.md) - End-to-end flow
- [Security](../development/security.md) - Secret and provider-data handling

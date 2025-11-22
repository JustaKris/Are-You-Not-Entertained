"""Shared rate limiting utilities for API clients.

Provides:
- AsyncRateLimiter: Token bucket rate limiter with semaphore
- Retry decorators with exponential backoff
"""

import asyncio
import time
from functools import wraps
from typing import Any, Callable

import httpx

from ayne.core.logging import get_logger

logger = get_logger(__name__)


class AsyncRateLimiter:
    """Async rate limiter using token bucket algorithm.

    Features:
    - Requests per second limiting
    - Concurrent request limiting (semaphore)
    - Thread-safe with asyncio.Lock

    Usage:
        limiter = AsyncRateLimiter(requests_per_second=4.0, max_concurrent=10)

        async with limiter:
            # Make API request
            response = await client.get(url)
    """

    def __init__(self, requests_per_second: float = 4.0, max_concurrent: int = 10):
        """Initialize rate limiter.

        Args:
            requests_per_second: Maximum requests per second
            max_concurrent: Maximum concurrent requests
        """
        self.requests_per_second = requests_per_second
        self.min_delay = 1.0 / requests_per_second
        self.max_concurrent = max_concurrent

        # State
        self._last_request_time = 0.0
        self._lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(max_concurrent)

        logger.debug(
            f"Rate limiter initialized: {requests_per_second} req/s, "
            f"max concurrent: {max_concurrent}"
        )

    async def __aenter__(self):
        """Acquire semaphore and enforce rate limit."""
        await self._semaphore.acquire()
        await self._enforce_rate_limit()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Release semaphore."""
        self._semaphore.release()
        return False

    async def _enforce_rate_limit(self):
        """Enforce minimum delay between requests."""
        async with self._lock:
            now = time.time()
            time_since_last = now - self._last_request_time

            if time_since_last < self.min_delay:
                wait_time = self.min_delay - time_since_last
                await asyncio.sleep(wait_time)

            self._last_request_time = time.time()


async def retry_with_backoff(
    func: Callable,
    retry_count: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (httpx.HTTPStatusError, httpx.RequestError),
) -> Any:
    """Retry async function with exponential backoff.

    Args:
        func: Async function to retry
        retry_count: Maximum number of retry attempts
        base_delay: Base delay in seconds (doubled each retry)
        max_delay: Maximum delay between retries
        exceptions: Tuple of exceptions to catch and retry

    Returns:
        Result of successful function call

    Raises:
        Last exception if all retries fail
    """
    last_exception = None

    for attempt in range(retry_count):
        try:
            return await func()
        except exceptions as e:
            last_exception = e

            # Check if it's a rate limit error
            if isinstance(e, httpx.HTTPStatusError) and e.response.status_code == 429:
                wait_time = min(base_delay * (2**attempt), max_delay)
                logger.warning(
                    f"Rate limited (429), waiting {wait_time:.1f}s before retry "
                    f"{attempt + 1}/{retry_count}"
                )
                await asyncio.sleep(wait_time)
            elif attempt < retry_count - 1:
                wait_time = min(base_delay * (2**attempt), max_delay)
                logger.warning(
                    f"Request failed: {e}, retrying in {wait_time:.1f}s "
                    f"(attempt {attempt + 1}/{retry_count})"
                )
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"All {retry_count} retry attempts failed")
                raise

    if last_exception:
        raise last_exception


def with_retry(retry_count: int = 3, base_delay: float = 1.0):
    """Decorator to add retry logic with exponential backoff to async functions.

    Usage:
        @with_retry(retry_count=3, base_delay=1.0)
        async def fetch_data():
            # API call
            pass

    Args:
        retry_count: Maximum number of retry attempts
        base_delay: Base delay in seconds
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_with_backoff(
                lambda: func(*args, **kwargs), retry_count=retry_count, base_delay=base_delay
            )

        return wrapper

    return decorator

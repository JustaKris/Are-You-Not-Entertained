"""Unit tests for TMDB discovery progress reporting."""

import asyncio
from typing import Any

import httpx

from ayne.data_collection.rate_limiter import retry_with_backoff
from ayne.data_collection.tmdb.client import TMDBClient


def test_discovery_reports_page_progress_and_preserves_result_order() -> None:
    client = object.__new__(TMDBClient)

    async def fake_request(endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        assert endpoint == "discover/movie"
        assert params["page"] == 1
        return {"total_pages": 2}

    async def fake_discover_movies_page(**kwargs: Any) -> list[dict[str, Any]]:
        page = kwargs["page"]
        return [{"tmdb_id": page, "title": f"Movie {page}"}]

    client._request = fake_request  # type: ignore[attr-defined]
    client.discover_movies_page = fake_discover_movies_page  # type: ignore[method-assign]
    events: list[tuple[str, int | None, int | None]] = []

    movies = asyncio.run(
        client.discover_movies(
            min_release_year=2020,
            max_release_year=2020,
            max_pages=2,
            progress_callback=lambda stage, completed, total: events.append(
                (stage, completed, total)
            ),
        )
    )

    assert [movie["tmdb_id"] for movie in movies] == [1, 2]
    assert events[0] == ("Planning TMDB pages (2020)", None, None)
    assert events[1] == ("Fetching TMDB pages (2020-2020)", 0, 2)
    assert events[-2:] == [
        ("Fetching TMDB pages (2020-2020)", 1, 2),
        ("Fetching TMDB pages (2020-2020)", 2, 2),
    ]


def test_discovery_reports_failed_pages_as_completed() -> None:
    client = object.__new__(TMDBClient)

    async def fake_request(endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        return {"total_pages": 2}

    async def fake_discover_movies_page(**kwargs: Any) -> list[dict[str, Any]]:
        if kwargs["page"] == 1:
            raise RuntimeError("request failed")
        return [{"tmdb_id": 2, "title": "Movie 2"}]

    client._request = fake_request  # type: ignore[attr-defined]
    client.discover_movies_page = fake_discover_movies_page  # type: ignore[method-assign]
    events: list[tuple[str, int | None, int | None]] = []

    movies = asyncio.run(
        client.discover_movies(
            min_release_year=2020,
            max_release_year=2020,
            max_pages=2,
            progress_callback=lambda stage, completed, total: events.append(
                (stage, completed, total)
            ),
        )
    )

    assert movies == [{"tmdb_id": 2, "title": "Movie 2"}]
    assert events[-1] == ("Fetching TMDB pages (2020-2020)", 2, 2)


def test_movie_cap_derives_a_global_page_budget() -> None:
    client = object.__new__(TMDBClient)
    fetched_pages: list[int] = []

    async def fake_request(endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        assert endpoint == "discover/movie"
        assert params["page"] == 1
        return {"total_pages": 100}

    async def fake_discover_movies_page(**kwargs: Any) -> list[dict[str, Any]]:
        fetched_pages.append(kwargs["page"])
        return [{"tmdb_id": page, "title": f"Movie {page}"} for page in [kwargs["page"]]]

    client._request = fake_request  # type: ignore[attr-defined]
    client.discover_movies_page = fake_discover_movies_page  # type: ignore[method-assign]

    movies = asyncio.run(
        client.discover_movies(
            min_release_year=2020,
            max_release_year=2020,
            max_movies=21,
        )
    )

    assert fetched_pages == [1, 2]
    assert len(movies) == 2


def test_explicit_page_cap_is_global_across_split_ranges() -> None:
    client = object.__new__(TMDBClient)
    fetched_ranges: list[tuple[int, int, int]] = []

    async def fake_request(endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        assert endpoint == "discover/movie"
        if params["primary_release_date.gte"] == "2020-01-01":
            return {"total_pages": 501}
        return {"total_pages": 500}

    async def fake_discover_movies_page(**kwargs: Any) -> list[dict[str, Any]]:
        fetched_ranges.append(
            (kwargs["min_release_year"], kwargs["max_release_year"], kwargs["page"])
        )
        return [{"tmdb_id": len(fetched_ranges), "title": "Movie"}]

    client._request = fake_request  # type: ignore[attr-defined]
    client.discover_movies_page = fake_discover_movies_page  # type: ignore[method-assign]

    movies = asyncio.run(
        client.discover_movies(
            min_release_year=2020,
            max_release_year=2021,
            max_pages=3,
        )
    )

    assert len(movies) == 3
    assert len(fetched_ranges) == 3
    assert all((min_year, max_year) == (2020, 2020) for min_year, max_year, _ in fetched_ranges)


def test_non_transient_http_errors_are_not_retried() -> None:
    attempts = 0

    async def fail_with_not_found() -> None:
        nonlocal attempts
        attempts += 1
        request = httpx.Request("GET", "https://api.example.test/movie/22939")
        response = httpx.Response(404, request=request)
        raise httpx.HTTPStatusError("not found", request=request, response=response)

    try:
        asyncio.run(retry_with_backoff(fail_with_not_found, retry_count=3))
    except httpx.HTTPStatusError as error:
        assert error.response.status_code == 404
    else:
        raise AssertionError("Expected HTTPStatusError")

    assert attempts == 1

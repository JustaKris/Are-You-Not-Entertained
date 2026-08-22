"""Unit tests for TMDB discovery progress reporting."""

import asyncio
from typing import Any

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

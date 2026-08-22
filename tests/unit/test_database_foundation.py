"""Tests for migrations, database contracts, fixtures, and manifests."""

import asyncio
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast

import duckdb
import pytest

from ayne.data_collection.omdb import OMDBClient
from ayne.data_collection.orchestrator import DataCollectionOrchestrator
from ayne.data_collection.refresh_strategy import get_movies_due_for_refresh_query
from ayne.data_collection.the_numbers import TheNumbersClient
from ayne.data_collection.tmdb import TMDBClient
from ayne.database.duckdb_client import DuckDBClient
from ayne.database.manifest import create_dataset_manifest
from ayne.database.migrations import current_schema_version, migration_status
from ayne.database.validation import validate_database


@pytest.fixture
def db(tmp_path: Path):
    """Return a migrated temporary database."""
    client = DuckDBClient(db_path=tmp_path / "foundation.duckdb")
    yield client
    client.close()


def test_writable_client_applies_migrations_idempotently(db):
    assert current_schema_version(db._conn) == 4
    assert [item["status"] for item in migration_status(db._conn)] == [
        "applied",
        "applied",
        "applied",
        "applied",
    ]

    db.close()
    reopened = DuckDBClient(db_path=db.db_path)
    try:
        assert current_schema_version(reopened._conn) == 4
        assert len(reopened.query("SELECT * FROM schema_migrations")) == 4
    finally:
        reopened.close()


def test_completed_database_recovers_from_old_migration_checksums(db):
    db.execute(
        "UPDATE schema_migrations SET name = ?, checksum = ? WHERE version = ?",
        ["old_initial_schema", "old-checksum", 1],
    )
    db.close()

    reopened = DuckDBClient(db_path=db.db_path)
    try:
        status = reopened.query(
            "SELECT name, checksum FROM schema_migrations WHERE version = 1"
        ).iloc[0]
        assert status["name"] == "initial_schema"
        assert status["checksum"] != "old-checksum"
    finally:
        reopened.close()


def test_validator_reports_orphan_rows(db):
    db.execute(
        "INSERT INTO tmdb_movies (tmdb_id, title) VALUES (?, ?)",
        [603, "Orphan movie"],
    )

    report = validate_database(db._conn)

    assert any(issue.code == "ORPHAN_TMDB" for issue in report.errors)


def test_schema_rejects_invalid_rating_range(db):
    db.execute("INSERT INTO movies (tmdb_id, title) VALUES (?, ?)", [603, "The Matrix"])

    with pytest.raises(duckdb.ConstraintException):
        db.execute(
            "INSERT INTO tmdb_movies (tmdb_id, vote_average) VALUES (?, ?)",
            [603, 11.0],
        )


def test_upsert_preserves_related_rows(db):
    db.execute(
        "INSERT INTO movies (tmdb_id, title) VALUES (?, ?)",
        [603, "The Matrix"],
    )
    db.execute(
        "INSERT INTO tmdb_movies (tmdb_id, imdb_id, title) VALUES (?, ?, ?)",
        [603, "tt0133093", "The Matrix"],
    )

    db.upsert_records(
        "movies",
        [{"tmdb_id": 603, "title": "The Matrix (updated)"}],
        key_columns=["tmdb_id"],
    )

    assert db.query("SELECT title FROM movies WHERE tmdb_id = 603").iloc[0]["title"] == (
        "The Matrix (updated)"
    )
    assert len(db.query("SELECT * FROM tmdb_movies WHERE tmdb_id = 603")) == 1


def test_refresh_reports_provider_progress_without_network(db):
    class FakeTmdbClient:
        async def get_batch_movie_details(
            self, tmdb_ids, allowed_statuses=None, progress_callback=None
        ):
            if progress_callback:
                progress_callback(1, len(tmdb_ids))
            return [
                {"tmdb_id": 603, "imdb_id": "tt0133093", "title": "The Matrix", "vote_average": 8.0}
            ]

        async def close(self):
            pass

    class FakeOmdbClient:
        async def get_batch_movies(self, imdb_ids, progress_callback=None):
            if progress_callback:
                progress_callback(1, len(imdb_ids))
            return [{"imdb_id": "tt0133093", "title": "The Matrix", "imdb_rating": 8.7}]

        async def close(self):
            pass

    class FakeNumbersClient:
        async def close(self):
            pass

    db.execute(
        """
        INSERT INTO movies (tmdb_id, imdb_id, title, release_date)
        VALUES (?, ?, ?, ?)
        """,
        [603, "tt0133093", "The Matrix", datetime.now(UTC) - timedelta(days=10)],
    )
    events = []
    orchestrator = DataCollectionOrchestrator(
        db,
        tmdb_client=cast(TMDBClient, FakeTmdbClient()),
        omdb_client=cast(OMDBClient, FakeOmdbClient()),
        numbers_client=cast(TheNumbersClient, FakeNumbersClient()),
    )

    async def run_refresh():
        await orchestrator.refresh_movie_data(
            db.query("SELECT * FROM movies"),
            progress_callback=lambda stage, completed, total: events.append(
                (stage, completed, total)
            ),
        )
        await orchestrator.close()

    asyncio.run(run_refresh())

    stages = [event[0] for event in events]
    assert stages[0] == "Planning refresh"
    assert "Refreshing TMDB" in stages
    assert "Refreshing OMDB" in stages
    assert stages[-1] == "OMDB refresh complete"
    assert ("Refreshing TMDB", 1, 1) in events
    assert ("Refreshing OMDB", 1, 1) in events


def test_tmdb_only_refresh_does_not_check_or_call_omdb(db, monkeypatch):
    class FakeTmdbClient:
        async def get_batch_movie_details(
            self, tmdb_ids, allowed_statuses=None, progress_callback=None
        ):
            return [{"tmdb_id": 603, "title": "The Matrix", "vote_average": 8.0}]

        async def close(self):
            pass

    class FailingOmdbClient:
        async def get_batch_movies(self, imdb_ids, progress_callback=None):
            raise AssertionError("TMDB-only refresh called OMDB")

        async def close(self):
            pass

    def fail_if_quota_is_checked(*args, **kwargs):
        raise AssertionError("TMDB-only refresh checked OMDB quota")

    monkeypatch.setattr(
        "ayne.data_collection.orchestrator.get_remaining_quota", fail_if_quota_is_checked
    )
    db.execute(
        "INSERT INTO movies (tmdb_id, title, release_date) VALUES (?, ?, ?)",
        [603, "The Matrix", datetime.now(UTC) - timedelta(days=10)],
    )
    orchestrator = DataCollectionOrchestrator(
        db,
        tmdb_client=cast(TMDBClient, FakeTmdbClient()),
        omdb_client=cast(OMDBClient, FailingOmdbClient()),
    )

    async def run_refresh():
        result = await orchestrator.refresh_movie_data(
            db.query("SELECT * FROM movies"), fetch_tmdb=True, fetch_omdb=False
        )
        await orchestrator.close()
        return result

    assert asyncio.run(run_refresh())[:2] == (1, 0)


def test_tmdb_enrichment_does_not_call_omdb(db):
    class FakeTmdbClient:
        async def get_batch_movie_details(
            self, tmdb_ids, allowed_statuses=None, progress_callback=None
        ):
            return [{"tmdb_id": 603, "title": "The Matrix", "vote_average": 8.0}]

        async def close(self):
            pass

    class FailingOmdbClient:
        async def get_batch_movies(self, imdb_ids, progress_callback=None):
            raise AssertionError("TMDB enrichment called OMDB")

        async def close(self):
            pass

    db.execute(
        "INSERT INTO movies (tmdb_id, title, release_date) VALUES (?, ?, ?)",
        [603, "The Matrix", datetime.now(UTC) - timedelta(days=10)],
    )
    orchestrator = DataCollectionOrchestrator(
        db,
        tmdb_client=cast(TMDBClient, FakeTmdbClient()),
        omdb_client=cast(OMDBClient, FailingOmdbClient()),
    )

    async def run_enrichment():
        result = await orchestrator.enrich_tmdb_details()
        await orchestrator.close()
        return result

    assert asyncio.run(run_enrichment()) == 1


def test_refresh_queries_only_select_movies_a_provider_can_process(db):
    db.execute(
        """
        INSERT INTO movies (tmdb_id, imdb_id, title, release_date)
        VALUES (?, ?, ?, ?), (?, ?, ?, ?)
        """,
        [
            None,
            "tt0000001",
            "IMDb-only movie",
            datetime.now(UTC) - timedelta(days=400),
            603,
            None,
            "TMDB-only movie",
            datetime.now(UTC) - timedelta(days=400),
        ],
    )

    omdb_rows = db.query(get_movies_due_for_refresh_query(data_source="omdb"))
    combined_rows = db.query(get_movies_due_for_refresh_query())

    assert omdb_rows["title"].tolist() == ["IMDb-only movie"]
    assert combined_rows["title"].tolist() == ["TMDB-only movie"]


def test_refresh_query_preserves_explicit_zero_limit(db):
    query = get_movies_due_for_refresh_query(limit=0, data_source="tmdb")

    assert "LIMIT 0" in query
    assert db.query(query).empty


def test_empty_database_passes_contract_validation(db):
    report = validate_database(db._conn)

    assert report.passed
    assert report.errors == []
    assert report.warnings == []


def test_validator_reports_missing_title_and_stale_data(db):
    old_timestamp = datetime.now(UTC) - timedelta(days=100)
    db.execute(
        """
        INSERT INTO movies (tmdb_id, title, last_tmdb_update)
        VALUES (?, ?, ?)
        """,
        [603, None, old_timestamp],
    )

    report = validate_database(db._conn)

    assert any(issue.code == "MOVIE_TITLE" for issue in report.errors)
    assert any(issue.code == "STALE_TMDB" for issue in report.warnings)


def test_demo_fixture_is_valid_and_manifest_is_registered(db, tmp_path: Path):
    fixture_path = Path("data/fixtures/demo.sql")
    db.execute(fixture_path.read_text(encoding="utf-8"))
    input_root = tmp_path / "raw"
    input_root.mkdir()
    (input_root / "source.json").write_text('{"source": "test"}\n', encoding="utf-8")

    report = validate_database(db._conn)
    manifest_path, document = create_dataset_manifest(
        db._conn,
        db.db_path,
        output_dir=tmp_path / "manifests",
        input_root=input_root,
        project_root=Path.cwd(),
    )

    assert report.passed
    assert manifest_path.exists()
    assert json.loads(manifest_path.read_text(encoding="utf-8")) == document
    assert document["schema_version"] == 4
    assert document["row_counts"]["movies"] == 3
    assert document["input_hashes"]["source.json"]
    assert db.query("SELECT COUNT(*) AS count FROM dataset_manifests").iloc[0]["count"] == 1

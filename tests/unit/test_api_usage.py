"""Unit tests for the persistent daily API usage ledger, using a throwaway DuckDB file."""

from datetime import date, timedelta

import pytest

from ayne.data_collection.api_usage import (
    get_remaining_quota,
    get_usage_today,
    record_api_usage,
)
from ayne.database.duckdb_client import DuckDBClient


@pytest.fixture
def db(tmp_path):
    client = DuckDBClient(db_path=tmp_path / "test_usage.duckdb")
    yield client
    client.close()


def test_usage_starts_at_zero(db):
    assert get_usage_today(db, "omdb") == 0


def test_record_usage_accumulates_same_day(db):
    record_api_usage(db, "omdb", 10)
    record_api_usage(db, "omdb", 5)
    assert get_usage_today(db, "omdb") == 15


def test_record_usage_is_per_provider(db):
    record_api_usage(db, "omdb", 10)
    record_api_usage(db, "tmdb", 3)
    assert get_usage_today(db, "omdb") == 10
    assert get_usage_today(db, "tmdb") == 3


def test_record_usage_ignores_non_positive_counts(db):
    record_api_usage(db, "omdb", 0)
    record_api_usage(db, "omdb", -5)
    assert get_usage_today(db, "omdb") == 0


def test_record_usage_on_specific_date_does_not_affect_today(db):
    yesterday = date.today() - timedelta(days=1)
    record_api_usage(db, "omdb", 50, on=yesterday)
    assert get_usage_today(db, "omdb") == 0


def test_get_remaining_quota(db):
    record_api_usage(db, "omdb", 400)
    assert get_remaining_quota(db, "omdb", daily_limit=1000) == 600


def test_get_remaining_quota_never_negative(db):
    record_api_usage(db, "omdb", 1500)
    assert get_remaining_quota(db, "omdb", daily_limit=1000) == 0

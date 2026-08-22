"""Unit tests for local database backup naming and preservation."""

from datetime import UTC, datetime

import pytest

from ayne.database.backup import create_database_backup


def test_database_backup_uses_utc_timestamp_and_preserves_source(tmp_path):
    source = tmp_path / "movies.duckdb"
    source.write_bytes(b"duckdb test content")
    timestamp = datetime(2026, 8, 22, 17, 19, 8, tzinfo=UTC)

    backup = create_database_backup(source, timestamp=timestamp)

    assert backup == tmp_path / "archive" / "movies-20260822T171908Z.duckdb"
    assert source.read_bytes() == b"duckdb test content"
    assert backup.read_bytes() == source.read_bytes()


def test_database_backup_does_not_overwrite_existing_backup(tmp_path):
    source = tmp_path / "movies.duckdb"
    source.write_bytes(b"duckdb test content")
    output = tmp_path / "archive" / "manual-backup.duckdb"
    output.parent.mkdir()
    output.write_bytes(b"existing backup")

    with pytest.raises(FileExistsError):
        create_database_backup(source, output_path=output)

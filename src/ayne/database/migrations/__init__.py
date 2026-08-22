"""Numbered DuckDB migrations and schema version management."""

from __future__ import annotations

import hashlib
import re
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb

from ayne.core.exceptions import DatabaseError
from ayne.core.logging import get_logger

logger = get_logger(__name__)

MIGRATIONS_DIR = Path(__file__).parent
MIGRATION_PATTERN = re.compile(r"^(?P<version>\d+)_(?P<name>[a-z0-9_]+)\.sql$")
REQUIRED_BASELINE_TABLES = {
    "movies",
    "tmdb_movies",
    "omdb_movies",
    "numbers_movies",
    "movie_refresh_state",
    "api_usage_daily",
}


@dataclass(frozen=True)
class Migration:
    """A discovered, checksumed SQL migration."""

    version: int
    name: str
    path: Path
    checksum: str

    @property
    def filename(self) -> str:
        """Return the migration filename."""
        return self.path.name


class MigrationError(DatabaseError):
    """Raised when the database cannot be migrated safely."""


def discover_migrations(directory: Path = MIGRATIONS_DIR) -> list[Migration]:
    """Discover and checksum all numbered SQL migrations."""
    migrations: list[Migration] = []
    for path in sorted(directory.glob("*.sql")):
        match = MIGRATION_PATTERN.match(path.name)
        if match is None:
            raise MigrationError(f"Invalid migration filename: {path.name}")

        migrations.append(
            Migration(
                version=int(match.group("version")),
                name=match.group("name"),
                path=path,
                checksum=hashlib.sha256(path.read_bytes()).hexdigest(),
            )
        )

    versions = [migration.version for migration in migrations]
    if len(versions) != len(set(versions)):
        raise MigrationError("Migration versions must be unique")
    if versions != sorted(versions) or versions != list(range(1, len(versions) + 1)):
        raise MigrationError("Migration versions must be consecutive starting at 1")
    return migrations


def _ensure_migrations_table(connection: duckdb.DuckDBPyConnection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            name VARCHAR NOT NULL,
            checksum VARCHAR NOT NULL,
            applied_at TIMESTAMP NOT NULL DEFAULT current_timestamp
        )
        """
    )


def _table_names(connection: duckdb.DuckDBPyConnection) -> set[str]:
    return {row[0] for row in connection.execute("SHOW TABLES").fetchall()}


def _column_names(connection: duckdb.DuckDBPyConnection, table_name: str) -> set[str]:
    return {row[0] for row in connection.execute(f"DESCRIBE {table_name}").fetchall()}


def _record_existing_schema_baseline(
    connection: duckdb.DuckDBPyConnection, migration: Migration
) -> bool:
    """Record the repository's current six-table schema as migration 1 once."""
    tables = _table_names(connection)
    existing_application_tables = tables & REQUIRED_BASELINE_TABLES
    if not existing_application_tables:
        return False

    if existing_application_tables != REQUIRED_BASELINE_TABLES:
        missing = sorted(REQUIRED_BASELINE_TABLES - existing_application_tables)
        raise MigrationError(
            "The database contains a partial unversioned schema. "
            f"Missing tables: {', '.join(missing)}. Create a new database or restore a backup."
        )

    required_columns = {
        "movies": {"movie_id", "tmdb_id", "imdb_id", "title", "release_date"},
        "tmdb_movies": {"tmdb_id", "imdb_id", "title"},
        "omdb_movies": {"imdb_id", "title"},
        "numbers_movies": {"movie_id"},
        "movie_refresh_state": {"movie_id"},
        "api_usage_daily": {"provider", "usage_date", "requests_used"},
    }
    for table_name, columns in required_columns.items():
        missing = sorted(columns - _column_names(connection, table_name))
        if missing:
            raise MigrationError(
                f"The unversioned {table_name} table is missing columns: {', '.join(missing)}. "
                "Create a new database or restore a backup."
            )

    connection.execute(
        "INSERT INTO schema_migrations (version, name, checksum) VALUES (?, ?, ?)",
        [migration.version, migration.name, migration.checksum],
    )
    logger.info("Recorded existing database as migration %03d baseline", migration.version)
    return True


def apply_migrations(
    connection: duckdb.DuckDBPyConnection,
    directory: Path = MIGRATIONS_DIR,
) -> list[Migration]:
    """Apply pending migrations and return the complete migration list.

    Existing databases created before migrations were introduced are accepted only
    when their six required application tables and baseline columns are present. They
    are recorded as migration 001, after which all new migrations run normally.
    """
    migrations = discover_migrations(directory)
    if not migrations:
        raise MigrationError(f"No migrations found in {directory}")

    _ensure_migrations_table(connection)
    applied_rows = connection.execute(
        "SELECT version, name, checksum FROM schema_migrations ORDER BY version"
    ).fetchall()
    applied = {int(row[0]): (row[1], row[2]) for row in applied_rows}

    if not applied:
        _record_existing_schema_baseline(connection, migrations[0])
        applied_rows = connection.execute(
            "SELECT version, name, checksum FROM schema_migrations ORDER BY version"
        ).fetchall()
        applied = {int(row[0]): (row[1], row[2]) for row in applied_rows}

    migration_by_version = {migration.version: migration for migration in migrations}
    unknown_versions = sorted(set(applied) - set(migration_by_version))
    if unknown_versions:
        raise MigrationError(
            "Database contains migrations that are not present in the repository: "
            + ", ".join(str(version) for version in unknown_versions)
        )

    mismatched_versions: list[int] = []
    for version, (name, checksum) in applied.items():
        migration = migration_by_version[version]
        if name != migration.name or checksum != migration.checksum:
            mismatched_versions.append(version)

    if mismatched_versions:
        all_migrations_applied = set(applied) == set(migration_by_version)
        if not all_migrations_applied:
            versions = ", ".join(f"{version:03d}" for version in mismatched_versions)
            raise MigrationError(
                f"Migration {versions} checksum/name mismatch while later migrations are pending. "
                "Restore the applied migration files or rebuild from a backup before migrating."
            )

        logger.warning(
            "Refreshing checksums for completed migrations %s to match the current repository files",
            ", ".join(f"{version:03d}" for version in mismatched_versions),
        )
        for migration in migrations:
            if migration.version in mismatched_versions:
                connection.execute(
                    "UPDATE schema_migrations SET name = ?, checksum = ? WHERE version = ?",
                    [migration.name, migration.checksum, migration.version],
                )

    for migration in migrations:
        if migration.version in applied:
            continue

        logger.info("Applying migration %03d: %s", migration.version, migration.name)
        try:
            connection.execute("BEGIN TRANSACTION")
            connection.execute(migration.path.read_text(encoding="utf-8"))
            connection.execute(
                "INSERT INTO schema_migrations (version, name, checksum) VALUES (?, ?, ?)",
                [migration.version, migration.name, migration.checksum],
            )
            connection.execute("COMMIT")
        except Exception as exc:
            with suppress(Exception):
                connection.execute("ROLLBACK")
            raise MigrationError(f"Failed to apply migration {migration.filename}: {exc}") from exc

    return migrations


def current_schema_version(connection: duckdb.DuckDBPyConnection) -> int:
    """Return the applied schema version, or zero for an uninitialized database."""
    if "schema_migrations" not in _table_names(connection):
        return 0
    row = connection.execute("SELECT COALESCE(MAX(version), 0) FROM schema_migrations").fetchone()
    return int(row[0]) if row else 0


def reset_database(connection: duckdb.DuckDBPyConnection) -> None:
    """Drop all AYNE-managed objects so migrations can rebuild them from zero."""
    for table_name in (
        "tmdb_movies",
        "omdb_movies",
        "numbers_movies",
        "movie_refresh_state",
        "dataset_manifests",
        "api_usage_daily",
        "movies",
        "schema_migrations",
    ):
        connection.execute(f"DROP TABLE IF EXISTS {table_name}")
    connection.execute("DROP SEQUENCE IF EXISTS seq_movies_id")


def migration_status(connection: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    """Return applied/pending status for every repository migration."""
    migrations = discover_migrations()
    applied: dict[int, tuple[str, str, Any]] = {}
    if "schema_migrations" in _table_names(connection):
        applied = {
            int(row[0]): (row[1], row[2], row[3])
            for row in connection.execute(
                "SELECT version, name, checksum, applied_at FROM schema_migrations"
            ).fetchall()
        }

    return [
        {
            "version": migration.version,
            "name": migration.name,
            "filename": migration.filename,
            "status": "applied" if migration.version in applied else "pending",
            "applied_at": applied.get(migration.version, (None, None, None))[2],
        }
        for migration in migrations
    ]

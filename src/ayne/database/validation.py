"""Database contract, integrity, domain, and freshness validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import duckdb

from ayne.database.migrations import current_schema_version, discover_migrations

ValidationSeverity = Literal["error", "warning"]


@dataclass(frozen=True)
class ValidationIssue:
    """One database validation finding."""

    code: str
    severity: ValidationSeverity
    message: str
    count: int = 0


@dataclass
class ValidationReport:
    """Collected database validation findings."""

    schema_version: int
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[ValidationIssue]:
        """Return blocking findings."""
        return [issue for issue in self.issues if issue.severity == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        """Return non-blocking findings."""
        return [issue for issue in self.issues if issue.severity == "warning"]

    @property
    def passed(self) -> bool:
        """Return whether no blocking findings were found."""
        return not self.errors


@dataclass(frozen=True)
class ColumnContract:
    """Expected type and nullability for one column."""

    data_type: str
    nullable: bool


TABLE_CONTRACTS: dict[str, dict[str, ColumnContract]] = {
    "movies": {
        "movie_id": ColumnContract("INTEGER", False),
        "tmdb_id": ColumnContract("INTEGER", True),
        "imdb_id": ColumnContract("VARCHAR", True),
        "title": ColumnContract("VARCHAR", True),
        "release_date": ColumnContract("DATE", True),
        "created_at": ColumnContract("TIMESTAMP", False),
        "last_full_refresh": ColumnContract("TIMESTAMP", True),
        "last_tmdb_update": ColumnContract("TIMESTAMP", True),
        "last_omdb_update": ColumnContract("TIMESTAMP", True),
        "last_numbers_update": ColumnContract("TIMESTAMP", True),
        "data_frozen": ColumnContract("BOOLEAN", False),
        "consecutive_unchanged_refreshes": ColumnContract("INTEGER", False),
    },
    "tmdb_movies": {
        "tmdb_id": ColumnContract("INTEGER", False),
        "imdb_id": ColumnContract("VARCHAR", True),
        "title": ColumnContract("VARCHAR", True),
        "release_date": ColumnContract("DATE", True),
        "status": ColumnContract("VARCHAR", True),
        "budget": ColumnContract("BIGINT", True),
        "revenue": ColumnContract("BIGINT", True),
        "runtime": ColumnContract("INTEGER", True),
        "vote_count": ColumnContract("INTEGER", True),
        "vote_average": ColumnContract("DOUBLE", True),
        "popularity": ColumnContract("DOUBLE", True),
        "genres": ColumnContract("VARCHAR", True),
        "production_companies": ColumnContract("VARCHAR", True),
        "production_countries": ColumnContract("VARCHAR", True),
        "spoken_languages": ColumnContract("VARCHAR", True),
        "overview": ColumnContract("VARCHAR", True),
        "last_updated_utc": ColumnContract("TIMESTAMP", True),
    },
    "omdb_movies": {
        "imdb_id": ColumnContract("VARCHAR", False),
        "title": ColumnContract("VARCHAR", True),
        "year": ColumnContract("INTEGER", True),
        "genre": ColumnContract("VARCHAR", True),
        "director": ColumnContract("VARCHAR", True),
        "writer": ColumnContract("VARCHAR", True),
        "actors": ColumnContract("VARCHAR", True),
        "imdb_rating": ColumnContract("DOUBLE", True),
        "imdb_votes": ColumnContract("INTEGER", True),
        "metascore": ColumnContract("INTEGER", True),
        "box_office": ColumnContract("BIGINT", True),
        "released": ColumnContract("VARCHAR", True),
        "runtime": ColumnContract("INTEGER", True),
        "language": ColumnContract("VARCHAR", True),
        "country": ColumnContract("VARCHAR", True),
        "rated": ColumnContract("VARCHAR", True),
        "awards": ColumnContract("VARCHAR", True),
        "rotten_tomatoes_rating": ColumnContract("INTEGER", True),
        "meta_critic_rating": ColumnContract("INTEGER", True),
        "last_updated_utc": ColumnContract("TIMESTAMP", True),
    },
    "numbers_movies": {
        "movie_id": ColumnContract("INTEGER", False),
        "domestic_box_office": ColumnContract("BIGINT", True),
        "international_box_office": ColumnContract("BIGINT", True),
        "worldwide_box_office": ColumnContract("BIGINT", True),
        "release_year": ColumnContract("INTEGER", True),
        "production_budget": ColumnContract("BIGINT", True),
        "opening_weekend_box_office": ColumnContract("BIGINT", True),
        "source_url": ColumnContract("VARCHAR", True),
        "last_updated_utc": ColumnContract("TIMESTAMP", True),
    },
    "movie_refresh_state": {
        "movie_id": ColumnContract("INTEGER", False),
        "refresh_interval_days": ColumnContract("INTEGER", False),
        "next_refresh_due": ColumnContract("TIMESTAMP", True),
        "freeze_after_days": ColumnContract("INTEGER", False),
        "frozen": ColumnContract("BOOLEAN", False),
        "last_checked": ColumnContract("TIMESTAMP", True),
    },
    "api_usage_daily": {
        "provider": ColumnContract("VARCHAR", False),
        "usage_date": ColumnContract("DATE", False),
        "requests_used": ColumnContract("INTEGER", False),
    },
}


def _table_names(connection: duckdb.DuckDBPyConnection) -> set[str]:
    return {row[0] for row in connection.execute("SHOW TABLES").fetchall()}


def _count(connection: duckdb.DuckDBPyConnection, query: str) -> int:
    row = connection.execute(query).fetchone()
    return int(row[0]) if row and row[0] is not None else 0


def _add_count_issue(
    report: ValidationReport,
    connection: duckdb.DuckDBPyConnection,
    code: str,
    severity: ValidationSeverity,
    message: str,
    query: str,
) -> None:
    count = _count(connection, query)
    if count:
        report.issues.append(ValidationIssue(code, severity, message, count))


def _validate_structure(
    connection: duckdb.DuckDBPyConnection, report: ValidationReport, tables: set[str]
) -> None:
    migrations = discover_migrations()
    latest_version = migrations[-1].version
    if report.schema_version != latest_version:
        report.issues.append(
            ValidationIssue(
                "SCHEMA_VERSION",
                "error",
                f"Database schema is version {report.schema_version}; expected {latest_version}",
            )
        )

    required_tables = set(TABLE_CONTRACTS) | {"schema_migrations", "dataset_manifests"}
    for table_name in sorted(required_tables - tables):
        report.issues.append(
            ValidationIssue("MISSING_TABLE", "error", f"Required table is missing: {table_name}")
        )

    for table_name, columns in TABLE_CONTRACTS.items():
        if table_name not in tables:
            continue
        actual = {
            row[0]: (str(row[1]).upper(), str(row[2]).upper() == "YES")
            for row in connection.execute(f"DESCRIBE {table_name}").fetchall()
        }
        for column_name, contract in columns.items():
            if column_name not in actual:
                report.issues.append(
                    ValidationIssue(
                        "MISSING_COLUMN",
                        "error",
                        f"{table_name}.{column_name} is missing",
                    )
                )
                continue
            actual_type, actual_nullable = actual[column_name]
            if actual_type != contract.data_type:
                report.issues.append(
                    ValidationIssue(
                        "COLUMN_TYPE",
                        "error",
                        f"{table_name}.{column_name} is {actual_type}; expected {contract.data_type}",
                    )
                )
            if contract.nullable is False and actual_nullable is True:
                report.issues.append(
                    ValidationIssue(
                        "COLUMN_NULLABILITY",
                        "warning",
                        f"{table_name}.{column_name} allows NULL; the canonical contract requires NOT NULL",
                    )
                )


def _validate_relationships(
    connection: duckdb.DuckDBPyConnection, report: ValidationReport
) -> None:
    relationship_checks = [
        (
            "ORPHAN_TMDB",
            "tmdb_movies rows without a matching movies.tmdb_id",
            """
            SELECT COUNT(*)
            FROM tmdb_movies AS t
            LEFT JOIN movies AS m ON m.tmdb_id = t.tmdb_id
            WHERE m.movie_id IS NULL
            """,
        ),
        (
            "ORPHAN_OMDB",
            "omdb_movies rows without a matching movies.imdb_id",
            """
            SELECT COUNT(*)
            FROM omdb_movies AS o
            LEFT JOIN movies AS m ON m.imdb_id = o.imdb_id
            WHERE m.movie_id IS NULL
            """,
        ),
        (
            "ORPHAN_NUMBERS",
            "numbers_movies rows without a matching movies.movie_id",
            """
            SELECT COUNT(*)
            FROM numbers_movies AS n
            LEFT JOIN movies AS m ON m.movie_id = n.movie_id
            WHERE m.movie_id IS NULL
            """,
        ),
        (
            "ORPHAN_REFRESH",
            "movie_refresh_state rows without a matching movies.movie_id",
            """
            SELECT COUNT(*)
            FROM movie_refresh_state AS r
            LEFT JOIN movies AS m ON m.movie_id = r.movie_id
            WHERE m.movie_id IS NULL
            """,
        ),
    ]
    for code, message, query in relationship_checks:
        _add_count_issue(report, connection, code, "error", message, query)


def _validate_domain(connection: duckdb.DuckDBPyConnection, report: ValidationReport) -> None:
    domain_checks = [
        (
            "MOVIE_IDENTITY",
            "Movies without a TMDB or IMDb identifier",
            "SELECT COUNT(*) FROM movies WHERE tmdb_id IS NULL AND imdb_id IS NULL",
        ),
        (
            "MOVIE_TITLE",
            "Movies with a missing or blank title",
            "SELECT COUNT(*) FROM movies WHERE title IS NULL OR length(trim(title)) = 0",
        ),
        (
            "TMDB_NUMERIC_RANGE",
            "TMDB numeric values outside their allowed ranges",
            """
            SELECT COUNT(*)
            FROM tmdb_movies
            WHERE (budget IS NOT NULL AND budget < 0)
               OR (revenue IS NOT NULL AND revenue < 0)
               OR (runtime IS NOT NULL AND runtime < 0)
               OR (vote_count IS NOT NULL AND vote_count < 0)
               OR (vote_average IS NOT NULL AND (vote_average < 0 OR vote_average > 10))
               OR (popularity IS NOT NULL AND popularity < 0)
            """,
        ),
        (
            "OMDB_NUMERIC_RANGE",
            "OMDB numeric values outside their allowed ranges",
            """
            SELECT COUNT(*)
            FROM omdb_movies
            WHERE (year IS NOT NULL AND year < 1888)
               OR (imdb_rating IS NOT NULL AND (imdb_rating < 0 OR imdb_rating > 10))
               OR (imdb_votes IS NOT NULL AND imdb_votes < 0)
               OR (metascore IS NOT NULL AND (metascore < 0 OR metascore > 100))
               OR (box_office IS NOT NULL AND box_office < 0)
               OR (runtime IS NOT NULL AND runtime < 0)
               OR (rotten_tomatoes_rating IS NOT NULL
                   AND (rotten_tomatoes_rating < 0 OR rotten_tomatoes_rating > 100))
               OR (meta_critic_rating IS NOT NULL
                   AND (meta_critic_rating < 0 OR meta_critic_rating > 100))
            """,
        ),
        (
            "NUMBERS_NUMERIC_RANGE",
            "The Numbers financial values outside their allowed ranges",
            """
            SELECT COUNT(*)
            FROM numbers_movies
            WHERE (domestic_box_office IS NOT NULL AND domestic_box_office < 0)
               OR (international_box_office IS NOT NULL AND international_box_office < 0)
               OR (worldwide_box_office IS NOT NULL AND worldwide_box_office < 0)
               OR (release_year IS NOT NULL AND release_year < 1888)
               OR (production_budget IS NOT NULL AND production_budget < 0)
               OR (opening_weekend_box_office IS NOT NULL AND opening_weekend_box_office < 0)
            """,
        ),
        (
            "REFRESH_STATE",
            "Refresh rows with non-positive intervals or counters",
            """
            SELECT COUNT(*)
            FROM movie_refresh_state
            WHERE refresh_interval_days <= 0
               OR freeze_after_days <= 0
            """,
        ),
        (
            "API_USAGE",
            "API usage rows with blank providers or negative request counts",
            """
            SELECT COUNT(*)
            FROM api_usage_daily
            WHERE length(trim(provider)) = 0 OR requests_used < 0
            """,
        ),
        (
            "FULL_REFRESH_TIMESTAMP",
            "Movies marked fully refreshed without both source timestamps",
            """
            SELECT COUNT(*)
            FROM movies
            WHERE last_full_refresh IS NOT NULL
              AND (last_tmdb_update IS NULL OR last_omdb_update IS NULL)
            """,
        ),
    ]
    for code, message, query in domain_checks:
        _add_count_issue(report, connection, code, "error", message, query)


def _validate_freshness(connection: duckdb.DuckDBPyConnection, report: ValidationReport) -> None:
    freshness_checks = [
        (
            "STALE_TMDB",
            "TMDB data has not been updated in more than 90 days",
            """
            SELECT COUNT(*)
            FROM movies
            WHERE last_tmdb_update IS NOT NULL
              AND last_tmdb_update < current_timestamp - INTERVAL '90 days'
              AND (data_frozen IS NULL OR data_frozen = FALSE)
            """,
        ),
        (
            "STALE_OMDB",
            "OMDB data has not been updated in more than 180 days",
            """
            SELECT COUNT(*)
            FROM movies
            WHERE last_omdb_update IS NOT NULL
              AND last_omdb_update < current_timestamp - INTERVAL '180 days'
              AND (data_frozen IS NULL OR data_frozen = FALSE)
            """,
        ),
        (
            "FUTURE_UPDATE_TIMESTAMP",
            "Source update timestamps are in the future",
            """
            SELECT COUNT(*)
            FROM movies
            WHERE last_tmdb_update > current_timestamp
               OR last_omdb_update > current_timestamp
               OR last_numbers_update > current_timestamp
            """,
        ),
    ]
    for code, message, query in freshness_checks:
        _add_count_issue(report, connection, code, "warning", message, query)


def validate_database(connection: duckdb.DuckDBPyConnection) -> ValidationReport:
    """Validate the database against the canonical data foundation contract."""
    schema_version = current_schema_version(connection)
    report = ValidationReport(schema_version=schema_version)
    tables = _table_names(connection)

    _validate_structure(connection, report, tables)
    if not set(TABLE_CONTRACTS).issubset(tables):
        return report

    _validate_relationships(connection, report)
    _validate_domain(connection, report)
    _validate_freshness(connection, report)
    return report

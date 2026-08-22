"""Reproducible dataset manifest generation."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb

from ayne.core.config.config_loader import settings
from ayne.database.migrations import current_schema_version

MANIFEST_VERSION = 1
MANIFEST_TABLES = (
    "movies",
    "tmdb_movies",
    "omdb_movies",
    "numbers_movies",
    "movie_refresh_state",
    "api_usage_daily",
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _input_hashes(input_root: Path) -> dict[str, str]:
    if not input_root.exists():
        return {}

    return {
        path.relative_to(input_root).as_posix(): _sha256_file(path)
        for path in sorted(input_root.rglob("*"))
        if path.is_file() and path.name != ".gitkeep"
    }


def _source_commit(project_root: Path) -> str:
    for variable in ("GITHUB_SHA", "CI_COMMIT_SHA"):
        value = os.getenv(variable)
        if value:
            return value

    git_dir = project_root / ".git"
    try:
        head = (git_dir / "HEAD").read_text(encoding="utf-8").strip()
        if head.startswith("ref: "):
            ref_path = git_dir / head.removeprefix("ref: ")
            return ref_path.read_text(encoding="utf-8").strip() or "unknown"
        return head or "unknown"
    except OSError:
        return "unknown"


def _display_path(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _row_counts(connection: duckdb.DuckDBPyConnection) -> dict[str, int]:
    row_counts: dict[str, int] = {}
    for table_name in MANIFEST_TABLES:
        row = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        if row is None:
            raise RuntimeError(f"Could not count rows in table {table_name}")
        row_counts[table_name] = int(row[0])
    return row_counts


def create_dataset_manifest(
    connection: duckdb.DuckDBPyConnection,
    database_path: Path,
    output_dir: Path | None = None,
    input_root: Path | None = None,
    project_root: Path | None = None,
) -> tuple[Path, dict[str, Any]]:
    """Create, persist, and register a dataset manifest.

    The manifest hashes every file under the immutable input directory and records
    the database row counts, schema version, source commit, and generation time.
    """
    project_root = project_root or settings.project_root
    data_dir = settings.data_dir or project_root / "data"
    output_dir = output_dir or data_dir / "manifests"
    input_root = input_root or settings.data_raw_dir or data_dir / "raw"
    generated_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    manifest_id = uuid.uuid4().hex

    payload: dict[str, Any] = {
        "manifest_version": MANIFEST_VERSION,
        "manifest_id": manifest_id,
        "schema_version": current_schema_version(connection),
        "source_commit": _source_commit(project_root),
        "generated_at": generated_at,
        "database_path": _display_path(database_path, project_root),
        "row_counts": _row_counts(connection),
        "input_hashes": _input_hashes(input_root),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    manifest_sha256 = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    document = {**payload, "manifest_sha256": manifest_sha256}

    output_dir.mkdir(parents=True, exist_ok=True)
    filename_timestamp = generated_at.replace("-", "").replace(":", "").replace("T", "-")
    manifest_path = output_dir / f"dataset-{filename_timestamp}-{manifest_id[:8]}.json"
    temporary_path = manifest_path.with_suffix(".json.tmp")
    temporary_path.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary_path.replace(manifest_path)

    connection.execute(
        """
        INSERT INTO dataset_manifests (
            manifest_id,
            schema_version,
            source_commit,
            generated_at,
            database_path,
            row_counts,
            input_hashes,
            manifest_sha256
        )
        VALUES (?, ?, ?, CAST(? AS TIMESTAMP), ?, CAST(? AS JSON), CAST(? AS JSON), ?)
        """,
        [
            manifest_id,
            payload["schema_version"],
            payload["source_commit"],
            generated_at,
            payload["database_path"],
            json.dumps(payload["row_counts"], sort_keys=True),
            json.dumps(payload["input_hashes"], sort_keys=True),
            manifest_sha256,
        ],
    )
    return manifest_path, document

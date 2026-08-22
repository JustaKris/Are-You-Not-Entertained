"""Safe local backups for the AYNE DuckDB database."""

from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path


def create_database_backup(
    database_path: str | Path,
    output_path: str | Path | None = None,
    timestamp: datetime | None = None,
) -> Path:
    """Copy a database to a timestamped archive path without overwriting it."""
    source = Path(database_path)
    if not source.is_file():
        raise FileNotFoundError(source)

    if output_path is None:
        archive_dir = source.parent / "archive"
        timestamp = timestamp or datetime.now(UTC)
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=UTC)
        timestamp = timestamp.astimezone(UTC)
        destination = archive_dir / (
            f"{source.stem}-{timestamp.strftime('%Y%m%dT%H%M%SZ')}{source.suffix}"
        )
    else:
        destination = Path(output_path)

    if source.resolve() == destination.resolve():
        raise ValueError("Backup destination must differ from the source database")
    if destination.exists():
        raise FileExistsError(destination)

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return destination

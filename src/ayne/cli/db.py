"""Database migrations, manifests, diagnostics, and statistics CLI commands."""

from pathlib import Path
from typing import Any, cast

import typer
from rich.console import Console
from rich.table import Table

from ayne.core.config import Settings
from ayne.core.config import settings as _settings
from ayne.core.exceptions import DatabaseLockedError
from ayne.core.logging import configure_logging, get_logger
from ayne.database.backup import create_database_backup
from ayne.database.duckdb_client import DuckDBClient
from ayne.database.manifest import create_dataset_manifest
from ayne.database.migrations import (
    apply_migrations,
    discover_migrations,
    migration_status,
    reset_database,
)
from ayne.database.validation import ValidationReport, validate_database

app = typer.Typer(help="Database management, migrations, manifests, and diagnostics")
console = Console()

settings = cast(Settings, _settings)
configure_logging(level=settings.log_level, use_json=settings.use_json_logging)  # type: ignore
logger = get_logger(__name__)

DATABASE_TABLES = (
    "movies",
    "tmdb_movies",
    "omdb_movies",
    "numbers_movies",
    "movie_refresh_state",
    "api_usage_daily",
    "dataset_manifests",
)


def _print_validation_summary(report: ValidationReport) -> None:
    """Print validation findings in a compact, actionable table."""
    table = Table(title="Database Contract", show_header=True)
    table.add_column("Severity")
    table.add_column("Code")
    table.add_column("Finding")
    table.add_column("Rows", justify="right")

    if not report.issues:
        table.add_row("[green]PASS[/green]", "-", "No findings", "0")
    else:
        for issue in report.issues:
            severity = "[red]ERROR[/red]" if issue.severity == "error" else "[yellow]WARN[/yellow]"
            table.add_row(severity, issue.code, issue.message, f"{issue.count:,}")
    console.print(table)


def _print_migration_status(statuses: list[dict[str, Any]]) -> None:
    """Print migration state."""
    table = Table(title="Schema Migrations", show_header=True)
    table.add_column("Version", justify="right")
    table.add_column("Migration")
    table.add_column("Status")
    table.add_column("Applied At")
    for status in statuses:
        applied = status["status"] == "applied"
        table.add_row(
            f"{status['version']:03d}",
            str(status["name"]),
            "[green]applied[/green]" if applied else "[yellow]pending[/yellow]",
            str(status["applied_at"] or "-"),
        )
    console.print(table)


@app.command("init")
def init_database(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Drop the configured database and rebuild it from migrations",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show pending migrations without making changes",
    ),
) -> None:
    """Initialize or rebuild the configured database through migrations."""
    console.print("[bold cyan]Database Initialization[/bold cyan]\n")
    console.print(f"Database path: [blue]{settings.duckdb_path}[/blue]")

    if dry_run:
        console.print("\n[yellow]DRY RUN - migrations that define the database:[/yellow]")
        for migration in discover_migrations():
            console.print(f"  [cyan]{migration.version:03d}[/cyan] {migration.name}")
        console.print("\n[green]No changes made[/green]")
        return

    try:
        with DuckDBClient(auto_migrate=not force) as db:
            if force:
                console.print("[yellow]Rebuilding database from migrations...[/yellow]")
                reset_database(db._conn)
                apply_migrations(db._conn)

            _print_migration_status(migration_status(db._conn))
            table = Table(title="Required Tables", show_header=True)
            table.add_column("Table")
            table.add_column("Status")
            for table_name in DATABASE_TABLES:
                exists = db.table_exists(table_name)
                table.add_row(
                    table_name, "[green]present[/green]" if exists else "[red]missing[/red]"
                )
            console.print(table)

            report = validate_database(db._conn)
            _print_validation_summary(report)
            if not report.passed:
                raise typer.Exit(code=1)

        console.print("\n[green]Database is ready[/green]")
    except DatabaseLockedError as exc:
        console.print(f"[red]Database is locked:[/red] {exc}")
        logger.error("Database initialization failed: %s", exc)
        raise typer.Exit(code=1) from exc
    except typer.Exit:
        raise
    except Exception as exc:
        console.print(f"[red]Database initialization failed:[/red] {exc}")
        logger.error("Database initialization failed", exc_info=True)
        raise typer.Exit(code=1) from exc


@app.command("migrate")
def migrate_database() -> None:
    """Apply pending numbered migrations to the configured database."""
    try:
        with DuckDBClient() as db:
            _print_migration_status(migration_status(db._conn))
    except Exception as exc:
        console.print(f"[red]Migration failed:[/red] {exc}")
        logger.error("Database migration failed", exc_info=True)
        raise typer.Exit(code=1) from exc


@app.command("test")
def test_database(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed test output"),
) -> None:
    """Run connectivity, migration, contract, and CRUD checks."""
    console.print("[bold cyan]Database Test Suite[/bold cyan]\n")
    try:
        with DuckDBClient() as db:
            console.print(f"Database: [blue]{db.db_path}[/blue]")
            report = validate_database(db._conn)
            if not report.passed:
                _print_validation_summary(report)
                raise typer.Exit(code=1)

            db.execute("DELETE FROM movies WHERE tmdb_id = ?", [99999])
            db.upsert_records(
                "movies",
                [{"tmdb_id": 99999, "title": "CLI Test Movie", "release_date": "2024-01-01"}],
                key_columns=["tmdb_id"],
            )
            result = db.query("SELECT title FROM movies WHERE tmdb_id = ?", [99999])
            if result.empty or result["title"].iloc[0] != "CLI Test Movie":
                raise RuntimeError("insert/query check failed")

            db.upsert_records(
                "movies",
                [
                    {
                        "tmdb_id": 99999,
                        "title": "CLI Test Movie UPDATED",
                        "release_date": "2024-01-01",
                    }
                ],
                key_columns=["tmdb_id"],
            )
            result = db.query("SELECT title FROM movies WHERE tmdb_id = ?", [99999])
            if result["title"].iloc[0] != "CLI Test Movie UPDATED":
                raise RuntimeError("upsert check failed")
            db.execute("DELETE FROM movies WHERE tmdb_id = ?", [99999])

            if verbose:
                console.print(db.get_collection_stats().to_string(index=False))
        console.print("[green]✓ Database checks passed[/green]")
    except typer.Exit:
        raise
    except Exception as exc:
        console.print(f"[red]Database test failed:[/red] {exc}")
        logger.error("Database test failed", exc_info=True)
        raise typer.Exit(code=1) from exc


@app.command("manifest")
def create_manifest(
    output: Path | None = typer.Option(None, "--output", "-o", help="Manifest output directory"),
    input_root: Path | None = typer.Option(
        None,
        "--input-root",
        help="Immutable input directory to hash (defaults to data/raw)",
    ),
) -> None:
    """Record row counts, schema version, source commit, and input hashes."""
    try:
        with DuckDBClient() as db:
            manifest_path, document = create_dataset_manifest(
                db._conn,
                db.db_path,
                output_dir=output,
                input_root=input_root,
            )
        console.print(f"[green]✓ Manifest written:[/green] {manifest_path}")
        console.print(f"Schema version: {document['schema_version']}")
        console.print(f"Source commit: {document['source_commit']}")
        console.print(f"Input files hashed: {len(document['input_hashes'])}")
    except Exception as exc:
        console.print(f"[red]Manifest generation failed:[/red] {exc}")
        logger.error("Manifest generation failed", exc_info=True)
        raise typer.Exit(code=1) from exc


@app.command("backup")
def backup_database(
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Backup file path (defaults to data/db/archive with a UTC timestamp)",
    ),
) -> None:
    """Create a timestamped local backup of the configured database."""
    try:
        with DuckDBClient(auto_migrate=False) as db:
            database_path = db.db_path
            db.execute("CHECKPOINT")

        backup_path = create_database_backup(database_path, output_path=output)
        console.print(f"[green]✓ Database backup written:[/green] {backup_path}")
    except DatabaseLockedError as exc:
        console.print(f"[red]Database is locked:[/red] {exc}")
        logger.error("Database backup failed: %s", exc)
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        console.print(f"[red]Database backup failed:[/red] {exc}")
        logger.error("Database backup failed", exc_info=True)
        raise typer.Exit(code=1) from exc


@app.command("seed-demo")
def seed_demo(
    output: Path = typer.Option(
        Path("data/db/demo.duckdb"),
        "--output",
        "-o",
        help="Demo database path",
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Replace an existing demo database"),
) -> None:
    """Create a small sanitized database for demos, notebooks, and tests."""
    fixture_path = settings.project_root / "data" / "fixtures" / "demo.sql"
    if not fixture_path.exists():
        console.print(f"[red]Demo fixture is missing:[/red] {fixture_path}")
        raise typer.Exit(code=1)
    if output.exists() and not force:
        console.print(
            f"[yellow]Database already exists:[/yellow] {output}; use --force to replace it"
        )
        raise typer.Exit(code=1)

    try:
        with DuckDBClient(db_path=output) as db:
            if force:
                reset_database(db._conn)
                apply_migrations(db._conn)
            db.execute(fixture_path.read_text(encoding="utf-8"))
            report = validate_database(db._conn)
            _print_validation_summary(report)
            if not report.passed:
                raise typer.Exit(code=1)
        console.print(f"[green]✓ Demo database ready:[/green] {output}")
    except typer.Exit:
        raise
    except Exception as exc:
        console.print(f"[red]Demo database creation failed:[/red] {exc}")
        logger.error("Demo database creation failed", exc_info=True)
        raise typer.Exit(code=1) from exc


@app.command("stats")
def show_stats() -> None:
    """Show database statistics and collection status."""
    console.print("[bold cyan]Database Statistics[/bold cyan]\n")
    try:
        with DuckDBClient() as db:
            stats = db.get_collection_stats()
            if stats.empty:
                console.print("[yellow]No data in database yet[/yellow]")
                return

            row = stats.iloc[0]
            main_table = Table(title="Collection Overview", show_header=True)
            main_table.add_column("Metric", style="cyan")
            main_table.add_column("Count", justify="right", style="green")
            main_table.add_row("Total Movies", f"{row['total_movies']:,}")
            main_table.add_row("With TMDB ID", f"{row['with_tmdb_basic']:,}")
            main_table.add_row("With TMDB Details", f"{row['with_tmdb_details']:,}")
            main_table.add_row("With OMDB Data", f"{row['with_omdb']:,}")
            main_table.add_row("Fully Refreshed", f"{row['fully_refreshed']:,}")
            main_table.add_row("Frozen (Stable)", f"{row['frozen']:,}")
            console.print(main_table)

            age_table = Table(title="Movies by Age", show_header=True)
            age_table.add_column("Category", style="cyan")
            age_table.add_column("Count", justify="right", style="green")
            age_table.add_row("Recent (0-60 days)", f"{row['recent_movies']:,}")
            age_table.add_row("Established (60-180 days)", f"{row['established_movies']:,}")
            age_table.add_row("Mature (180-365 days)", f"{row['mature_movies']:,}")
            age_table.add_row("Archived (>365 days)", f"{row['archived_movies']:,}")
            console.print(age_table)
    except DatabaseLockedError as exc:
        console.print(f"[red]Database is locked:[/red] {exc}")
        logger.error("Failed to get database stats: %s", exc)
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        console.print(f"[red]Failed to get database stats:[/red] {exc}")
        logger.error("Failed to get database stats", exc_info=True)
        raise typer.Exit(code=1) from exc

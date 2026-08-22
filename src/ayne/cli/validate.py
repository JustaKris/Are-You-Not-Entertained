"""Data validation CLI commands."""

import typer
from rich.console import Console
from rich.table import Table

from ayne.core.logging import get_logger
from ayne.database.duckdb_client import DuckDBClient
from ayne.database.validation import ValidationReport, validate_database

app = typer.Typer(help="Data validation and quality checks")
console = Console()

logger = get_logger(__name__)

FRESHNESS_WARNING_CODES = {
    "STALE_TMDB",
    "STALE_OMDB",
    "FUTURE_UPDATE_TIMESTAMP",
}


def _percentage(part: int, total: int) -> float:
    """Return a safe percentage for empty datasets."""
    return 100.0 * part / total if total else 0.0


def _print_database_report(report: ValidationReport) -> None:
    """Print database validation findings."""
    table = Table(title=f"Database Contract (schema v{report.schema_version})", show_header=True)
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


@app.command("tmdb")
def validate_tmdb(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed validation results",
    ),
):
    """Validate TMDB data quality and completeness.

    Checks for:
    - Missing required fields
    - Data consistency
    - Outliers and anomalies
    """
    console.print("[bold cyan]TMDB Data Validation[/bold cyan]\n")

    db = DuckDBClient()
    try:
        # Basic counts
        total = db.query("SELECT COUNT(*) as count FROM movies").iloc[0]["count"]
        with_tmdb = db.query(
            "SELECT COUNT(*) as count FROM movies WHERE last_tmdb_update IS NOT NULL"
        ).iloc[0]["count"]

        console.print(f"Total movies: {total:,}")
        console.print(f"With TMDB data: {with_tmdb:,} ({_percentage(with_tmdb, total):.1f}%)\n")

        # Validation checks
        checks = []

        # Check 1: Missing titles
        missing_titles = db.query(
            "SELECT COUNT(*) as count FROM movies WHERE title IS NULL OR title = ''"
        ).iloc[0]["count"]
        checks.append(("Missing titles", missing_titles, missing_titles == 0))

        # Check 2: Missing release dates
        missing_dates = db.query(
            "SELECT COUNT(*) as count FROM movies WHERE release_date IS NULL"
        ).iloc[0]["count"]
        checks.append(("Missing release dates", missing_dates, missing_dates == 0))

        # Check 3: Invalid popularity
        invalid_popularity = db.query(
            "SELECT COUNT(*) as count FROM tmdb_movies WHERE popularity < 0 OR popularity IS NULL"
        ).iloc[0]["count"]
        checks.append(("Invalid popularity", invalid_popularity, invalid_popularity == 0))

        # Check 4: Invalid vote counts
        invalid_votes = db.query(
            "SELECT COUNT(*) as count FROM tmdb_movies WHERE vote_count < 0 OR vote_count IS NULL"
        ).iloc[0]["count"]
        checks.append(("Invalid vote counts", invalid_votes, invalid_votes == 0))

        # Check 5: Stale data (not updated in 90+ days)
        stale_data = db.query(
            """
            SELECT COUNT(*) as count FROM movies
            WHERE last_tmdb_update IS NOT NULL
              AND DATEDIFF('day', last_tmdb_update, CURRENT_DATE) > 90
        """
        ).iloc[0]["count"]
        checks.append(("Stale data (>90 days)", stale_data, total == 0 or stale_data < total * 0.1))

        # Display results
        results_table = Table(title="Validation Results", show_header=True)
        results_table.add_column("Check", style="cyan")
        results_table.add_column("Issues", justify="right")
        results_table.add_column("Status")

        all_passed = True
        for check_name, issue_count, passed in checks:
            status = "[green]✓ Pass[/green]" if passed else "[red]✗ Fail[/red]"
            results_table.add_row(check_name, f"{issue_count:,}", status)
            if not passed:
                all_passed = False

        console.print(results_table)

        if all_passed:
            console.print("\n[green]✓ All TMDB validation checks passed![/green]")
        else:
            console.print("\n[yellow]⚠ Some validation checks failed[/yellow]")

        if verbose and missing_titles > 0:
            # Show sample of issues
            console.print("\n[yellow]Sample movies with missing titles:[/yellow]")
            sample = db.query(
                "SELECT tmdb_id, release_date FROM movies WHERE title IS NULL OR title = '' LIMIT 5"
            )
            console.print(sample.to_string(index=False))

    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        logger.error(f"TMDB validation failed: {e}", exc_info=True)
        raise typer.Exit(code=1)
    finally:
        db.close()


@app.command("imdb")
def validate_imdb(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed validation results",
    ),
):
    """Validate OMDB/IMDb data quality and completeness.

    Checks for:
    - Missing IMDb IDs
    - Invalid ratings
    - Missing enrichment data
    """
    console.print("[bold cyan]OMDB/IMDb Data Validation[/bold cyan]\n")

    db = DuckDBClient()
    try:
        # Basic counts
        total = db.query("SELECT COUNT(*) as count FROM movies").iloc[0]["count"]
        with_imdb_id = db.query(
            "SELECT COUNT(*) as count FROM movies WHERE imdb_id IS NOT NULL"
        ).iloc[0]["count"]
        with_omdb = db.query(
            "SELECT COUNT(*) as count FROM movies WHERE last_omdb_update IS NOT NULL"
        ).iloc[0]["count"]

        console.print(f"Total movies: {total:,}")
        console.print(f"With IMDb ID: {with_imdb_id:,} ({_percentage(with_imdb_id, total):.1f}%)")
        console.print(f"With OMDB data: {with_omdb:,} ({_percentage(with_omdb, total):.1f}%)\n")

        # Validation checks
        checks = []

        # Check 1: Missing IMDb IDs
        missing_imdb = db.query("SELECT COUNT(*) as count FROM movies WHERE imdb_id IS NULL").iloc[
            0
        ]["count"]
        checks.append(("Missing IMDb IDs", missing_imdb, total == 0 or missing_imdb < total * 0.1))

        # Check 2: Invalid IMDb ratings
        invalid_rating = db.query(
            """
            SELECT COUNT(*) as count FROM omdb_movies
            WHERE imdb_rating IS NOT NULL
              AND (imdb_rating < 0 OR imdb_rating > 10)
        """
        ).iloc[0]["count"]
        checks.append(("Invalid IMDb ratings", invalid_rating, invalid_rating == 0))

        # Check 3: Invalid Metascores
        invalid_metascore = db.query(
            """
            SELECT COUNT(*) as count FROM omdb_movies
            WHERE metascore IS NOT NULL
              AND (metascore < 0 OR metascore > 100)
        """
        ).iloc[0]["count"]
        checks.append(("Invalid Metascores", invalid_metascore, invalid_metascore == 0))

        # Check 4: Movies with IMDb ID but no OMDB data
        unprocessed = db.query(
            """
            SELECT COUNT(*) as count FROM movies
            WHERE imdb_id IS NOT NULL
              AND last_omdb_update IS NULL
        """
        ).iloc[0]["count"]
        checks.append(
            (
                "Unprocessed (have ID, no data)",
                unprocessed,
                with_imdb_id == 0 or unprocessed < with_imdb_id * 0.1,
            )
        )

        # Check 5: Stale OMDB data (>180 days)
        stale_data = db.query(
            """
            SELECT COUNT(*) as count FROM movies
            WHERE last_omdb_update IS NOT NULL
              AND DATEDIFF('day', last_omdb_update, CURRENT_DATE) > 180
        """
        ).iloc[0]["count"]
        checks.append(
            ("Stale data (>180 days)", stale_data, with_omdb == 0 or stale_data < with_omdb * 0.2)
        )

        # Display results
        results_table = Table(title="Validation Results", show_header=True)
        results_table.add_column("Check", style="cyan")
        results_table.add_column("Issues", justify="right")
        results_table.add_column("Status")

        all_passed = True
        for check_name, issue_count, passed in checks:
            status = "[green]✓ Pass[/green]" if passed else "[red]✗ Fail[/red]"
            results_table.add_row(check_name, f"{issue_count:,}", status)
            if not passed:
                all_passed = False

        console.print(results_table)

        if all_passed:
            console.print("\n[green]✓ All OMDB validation checks passed![/green]")
        else:
            console.print("\n[yellow]⚠ Some validation checks failed[/yellow]")

        if verbose and unprocessed > 0:
            console.print(
                "\n[yellow]Sample unprocessed movies (have IMDb ID, no OMDB data):[/yellow]"
            )
            sample = db.query(
                """
                SELECT title, imdb_id, release_date
                FROM movies
                WHERE imdb_id IS NOT NULL AND last_omdb_update IS NULL
                LIMIT 5
            """
            )
            console.print(sample.to_string(index=False))

    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        logger.error(f"OMDB validation failed: {e}", exc_info=True)
        raise typer.Exit(code=1)
    finally:
        db.close()


@app.command("all")
def validate_all(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed validation results",
    ),
):
    """Run all validation checks (TMDB + OMDB).

    Comprehensive validation of entire dataset.
    """
    console.print("[bold cyan]Comprehensive Data Validation[/bold cyan]\n")

    console.print("[bold]Database Contract Validation:[/bold]")
    validate_database_quality(strict_freshness=False)

    # Run TMDB validation
    console.print("[bold]TMDB Validation:[/bold]")
    validate_tmdb(verbose=verbose)

    console.print("\n" + "=" * 60 + "\n")

    # Run OMDB validation
    console.print("[bold]OMDB Validation:[/bold]")
    validate_imdb(verbose=verbose)

    console.print("\n[green]✓ All validation checks complete[/green]")


@app.command("database")
def validate_database_quality(
    strict_freshness: bool = typer.Option(
        False,
        "--strict-freshness",
        help="Treat stale-data warnings as blocking failures",
    ),
) -> None:
    """Validate schema, contracts, relationships, domain ranges, and freshness."""
    db = DuckDBClient()
    try:
        report = validate_database(db._conn)
        _print_database_report(report)
        freshness_warnings = [
            issue for issue in report.warnings if issue.code in FRESHNESS_WARNING_CODES
        ]
        if report.errors:
            console.print(f"[red]✗ Database validation failed: {len(report.errors)} error(s)[/red]")
            raise typer.Exit(code=1)
        if strict_freshness and freshness_warnings:
            console.print(
                "[red]✗ Strict freshness validation failed: "
                f"{len(freshness_warnings)} stale-data finding(s)[/red]"
            )
            raise typer.Exit(code=1)
        console.print("[green]✓ Database validation passed[/green]")
    except typer.Exit:
        raise
    except Exception as exc:
        console.print(f"[red]Database validation failed:[/red] {exc}")
        logger.error("Database validation failed", exc_info=True)
        raise typer.Exit(code=1) from exc
    finally:
        db.close()

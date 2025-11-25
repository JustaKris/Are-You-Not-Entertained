"""OMDB data enrichment CLI commands - Restructured."""

import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ayne.core.config import settings
from ayne.core.exceptions import APIRateLimitExceeded
from ayne.core.logging import configure_logging, get_logger
from ayne.data_collection.orchestrator import DataCollectionOrchestrator
from ayne.database.duckdb_client import DuckDBClient

app = typer.Typer(help="OMDB data enrichment")
console = Console()

configure_logging(level=settings.log_level, use_json=settings.use_json_logging)  # type: ignore
logger = get_logger(__name__)


@app.command("enrich")
def enrich_omdb(
    max_movies: Optional[int] = typer.Option(
        None,
        "--max-movies",
        help="Maximum number of movies to enrich (uses config default)",
    ),
    min_year: Optional[int] = typer.Option(
        None,
        "--min-year",
        help="Minimum release year",
    ),
    max_year: Optional[int] = typer.Option(
        None,
        "--max-year",
        help="Maximum release year",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be done without making changes",
    ),
):
    """Enrich movies with OMDB data (ratings, box office, awards, etc.).

    This command fetches OMDB data for movies that have IMDb IDs but no OMDB
    enrichment yet. Movies must have TMDB details (with IMDb IDs) first.

    OMDB has daily API limits, so use max-movies to control quota usage.

    Examples:
        ayne omdb enrich --max-movies 1000
        ayne omdb enrich --min-year 2023 --max-movies 500
        ayne omdb enrich --dry-run
    """
    console.print("[bold cyan]OMDB Enrichment[/bold cyan]\n")

    if dry_run:
        console.print("[yellow]DRY RUN MODE - No changes will be made[/yellow]\n")

    max_movies = max_movies or settings.omdb_max_movies

    # Use settings defaults for year filters if not provided
    min_year = min_year or getattr(settings, "omdb_min_release_year", None)
    max_year = max_year or getattr(settings, "omdb_max_release_year", None)

    console.print("[bold]Configuration:[/bold]")
    console.print(f"  Max Movies: {max_movies:,}")
    console.print(f"  Min Year: {min_year or 'No limit'}")
    console.print(f"  Max Year: {max_year or 'No limit'}")
    console.print()

    logger.info(
        f"OMDB enrich: max_movies={max_movies}, min_year={min_year}, max_year={max_year}, dry_run={dry_run}"
    )

    if dry_run:
        # Show what would be enriched
        db = DuckDBClient()
        try:
            query = """
                SELECT m.title, m.release_date, m.imdb_id
                FROM movies m
                LEFT JOIN omdb_movies o ON m.imdb_id = o.imdb_id
                WHERE m.imdb_id IS NOT NULL
                  AND m.imdb_id != ''
                  AND o.imdb_id IS NULL
            """

            if min_year:
                query += f" AND m.release_date >= '{min_year}-01-01'"
            if max_year:
                query += f" AND m.release_date <= '{max_year}-12-31'"

            query += f" ORDER BY m.release_date DESC LIMIT {max_movies}"

            candidates = db.query(query)

            if candidates.empty:
                console.print("[yellow]No movies need OMDB enrichment[/yellow]")
                console.print("\n[blue]ℹ Tip:[/blue] Movies need TMDB details with IMDb IDs first.")
                console.print("  Run: ayne tmdb enrich")
            else:
                console.print(f"Would enrich {len(candidates)} movies:")
                console.print(candidates[["title", "release_date"]].head(10).to_string(index=False))
                if len(candidates) > 10:
                    console.print(f"... and {len(candidates) - 10} more")

            console.print("\n[green]✓[/green] Dry run complete")
        finally:
            db.close()
        return

    async def _run_enrichment():
        db = DuckDBClient()
        orchestrator = DataCollectionOrchestrator(db)

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(f"Enriching up to {max_movies:,} movies...", total=None)

                enriched = await orchestrator.enrich_omdb_data(
                    limit=max_movies,
                    min_release_year=min_year,
                    max_release_year=max_year,
                )

                progress.update(task, completed=True)

            console.print(f"\n[green]✓[/green] Enriched {enriched:,} movies with OMDB data")

            # Show sample
            if enriched > 0:
                sample = db.query(
                    """
                    SELECT m.title, o.imdb_rating, o.metascore, o.box_office
                    FROM omdb_movies o
                    JOIN movies m ON o.imdb_id = m.imdb_id
                    ORDER BY m.last_omdb_update DESC
                    LIMIT 5
                    """
                )
                console.print("\n[bold]Recently enriched:[/bold]")
                console.print(sample.to_string(index=False))

        except APIRateLimitExceeded as e:
            # OMDB daily quota hit - this is expected, not an error
            progress.update(task, completed=True)

            console.print("\n[yellow]⚠ OMDB Daily Limit Reached[/yellow]\n")
            console.print(
                f"[cyan]Progress:[/cyan] {e.items_processed:,}/{e.total_requested:,} movies successfully enriched"
            )
            console.print("\n[bold]What happened:[/bold]")
            console.print("  OMDB free tier has a 1,000 request/day limit")
            console.print("  Your data has been saved successfully\n")
            console.print("[bold]Next steps:[/bold]")
            console.print("  • Wait 24 hours for quota to reset")
            console.print("  • Run the same command tomorrow to continue")
            console.print("  • Or upgrade to OMDB paid plan for higher limits\n")

            # Show what was enriched
            if e.items_processed > 0:
                sample = db.query(
                    """
                    SELECT m.title, o.imdb_rating, o.metascore, o.box_office
                    FROM omdb_movies o
                    JOIN movies m ON o.imdb_id = m.imdb_id
                    ORDER BY m.last_omdb_update DESC
                    LIMIT 5
                    """
                )
                if not sample.empty:
                    console.print("[bold]Recently enriched (sample):[/bold]")
                    console.print(sample.to_string(index=False))

            logger.info(f"OMDB quota exceeded after {e.items_processed} successful requests")
            # Exit with 0 since this is expected behavior, not an error

        except Exception as e:
            console.print(f"[red]✗ Error:[/red] {e}")
            logger.error(f"OMDB enrichment failed: {e}", exc_info=True)
            raise typer.Exit(code=1)
        finally:
            await orchestrator.close()
            db.close()

    asyncio.run(_run_enrichment())


@app.command("refresh")
def refresh_omdb(
    limit: int = typer.Option(
        100,
        "--limit",
        "-n",
        help="Maximum number of movies to refresh",
    ),
    min_year: Optional[int] = typer.Option(
        None,
        "--min-year",
        help="Minimum release year",
    ),
    max_year: Optional[int] = typer.Option(
        None,
        "--max-year",
        help="Maximum release year",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be done without making changes",
    ),
):
    """Refresh existing OMDB data for movies that need updates.

    This command only updates movies that already have OMDB data and are
    due for a refresh. Use this for periodic updates of ratings, reviews, etc.

    Examples:
        ayne omdb refresh --limit 100
        ayne omdb refresh --min-year 2024 --limit 50
        ayne omdb refresh --dry-run
    """
    console.print("[bold cyan]OMDB Data Refresh[/bold cyan]\n")

    if dry_run:
        console.print("[yellow]DRY RUN MODE - No changes will be made[/yellow]\n")

    # Use settings defaults for year filters if not provided
    min_year = min_year or getattr(settings, "omdb_min_release_year", None)
    max_year = max_year or getattr(settings, "omdb_max_release_year", None)

    console.print("[bold]Configuration:[/bold]")
    console.print(f"  Refresh Limit: {limit:,} movies")
    console.print(f"  Min Year: {min_year or 'No limit'}")
    console.print(f"  Max Year: {max_year or 'No limit'}")
    console.print()

    logger.info(
        f"OMDB refresh: limit={limit}, min_year={min_year}, max_year={max_year}, dry_run={dry_run}"
    )

    logger.info(
        f"OMDB refresh: limit={limit}, min_year={min_year}, max_year={max_year}, dry_run={dry_run}"
    )

    if dry_run:
        db = DuckDBClient()
        try:
            query = """
                SELECT m.title, m.release_date, m.last_omdb_update
                FROM movies m
                JOIN omdb_movies o ON m.imdb_id = o.imdb_id
                WHERE m.imdb_id IS NOT NULL
            """

            if min_year:
                query += f" AND m.release_date >= '{min_year}-01-01'"
            if max_year:
                query += f" AND m.release_date <= '{max_year}-12-31'"

            query += f" ORDER BY m.last_omdb_update ASC NULLS FIRST LIMIT {limit}"

            candidates = db.query(query)

            if candidates.empty:
                console.print("[yellow]No movies have OMDB data to refresh[/yellow]")
            else:
                console.print(f"Would refresh {len(candidates)} movies:")
                console.print(candidates[["title", "release_date"]].head(10).to_string(index=False))
                if len(candidates) > 10:
                    console.print(f"... and {len(candidates) - 10} more")

            console.print("\n[green]✓[/green] Dry run complete")
        finally:
            db.close()
        return

    async def _run_refresh():
        db = DuckDBClient()
        orchestrator = DataCollectionOrchestrator(db)

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(f"Refreshing up to {limit:,} movies...", total=None)

                # Get movies that have OMDB data and filter by year
                query = """
                    SELECT m.*
                    FROM movies m
                    JOIN omdb_movies o ON m.imdb_id = o.imdb_id
                    WHERE m.imdb_id IS NOT NULL
                """

                if min_year:
                    query += f" AND m.release_date >= '{min_year}-01-01'"
                if max_year:
                    query += f" AND m.release_date <= '{max_year}-12-31'"

                query += f" ORDER BY m.last_omdb_update ASC NULLS FIRST LIMIT {limit}"

                movies_to_refresh = db.query(query)

                if movies_to_refresh.empty:
                    progress.update(task, completed=True)
                    console.print("\n[yellow]No movies need OMDB refresh[/yellow]")
                    return

                tmdb_updated, omdb_updated, frozen = await orchestrator.refresh_movie_data(
                    movies_to_refresh,
                    fetch_tmdb=False,  # OMDB only
                    fetch_omdb=True,
                    omdb_max_movies=limit,
                )

                progress.update(task, completed=True)

            console.print(f"\n[green]✓[/green] Refreshed {omdb_updated:,} movies")

        except Exception as e:
            console.print(f"[red]✗ Error:[/red] {e}")
            logger.error(f"OMDB refresh failed: {e}", exc_info=True)
            raise typer.Exit(code=1)
        finally:
            await orchestrator.close()
            db.close()

    asyncio.run(_run_refresh())

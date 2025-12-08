"""OMDB data enrichment CLI commands."""

import asyncio

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ayne.core.config import settings
from ayne.core.logging import configure_logging, get_logger
from ayne.data_collection.orchestrator import DataCollectionOrchestrator
from ayne.database.duckdb_client import DuckDBClient

app = typer.Typer(help="OMDB data enrichment")
console = Console()

configure_logging(level=settings.log_level, use_json=settings.use_json_logging)  # type: ignore
logger = get_logger(__name__)


@app.command("update")
def update_omdb(
    max_movies: int | None = typer.Option(
        None,
        "--max-movies",
        help="Maximum number of movies to enrich (uses config default)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be done without making changes",
    ),
):
    """Enrich movies with OMDB data (ratings, box office, etc.).

    OMDB has daily API limits, so use max-movies to control quota usage.

    Examples:
        ayne omdb update --max-movies 1000
        ayne omdb update --dry-run
    """
    console.print("[bold cyan]OMDB Data Enrichment[/bold cyan]\n")

    if dry_run:
        console.print("[yellow]DRY RUN MODE - No changes will be made[/yellow]\n")

    max_movies = max_movies or settings.omdb_max_movies

    console.print("[bold]Configuration:[/bold]")
    console.print(f"  Max Movies: {max_movies:,}")
    console.print()

    if dry_run:
        # Show what would be enriched
        db = DuckDBClient()
        try:
            query = """
                SELECT m.title, m.release_date, m.imdb_id
                FROM movies m
                LEFT JOIN tmdb_movies t ON m.tmdb_id = t.tmdb_id
                WHERE m.imdb_id IS NOT NULL
                  AND m.last_omdb_update IS NULL
                ORDER BY t.popularity DESC NULLS LAST
                LIMIT ?
            """
            candidates = db.query(query, params=(max_movies,))

            if candidates.empty:
                console.print("[yellow]No movies need OMDB enrichment[/yellow]")
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

                # Get movies that need OMDB data
                query = """
                    SELECT m.*
                    FROM movies m
                    LEFT JOIN tmdb_movies t ON m.tmdb_id = t.tmdb_id
                    WHERE m.imdb_id IS NOT NULL
                      AND m.last_omdb_update IS NULL
                    ORDER BY t.popularity DESC NULLS LAST
                    LIMIT ?
                """
                movies_to_enrich = db.query(query, params=(max_movies,))

                if movies_to_enrich.empty:
                    progress.update(task, completed=True)
                    console.print("\n[yellow]No movies need OMDB enrichment[/yellow]")
                    return

                _tmdb_updated, omdb_updated, _frozen = await orchestrator.refresh_movie_data(
                    movies_to_enrich,
                    fetch_tmdb=False,  # OMDB only
                    fetch_omdb=True,
                    omdb_max_movies=max_movies,
                )

                progress.update(task, completed=True)

            console.print(f"\n[green]✓[/green] Enriched {omdb_updated:,} movies with OMDB data")

            # Show sample
            if omdb_updated > 0:
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
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be done without making changes",
    ),
):
    """Refresh existing OMDB data for movies that need updates.

    Uses age-based refresh strategy to prioritize recent movies.
    """
    console.print("[bold cyan]OMDB Data Refresh[/bold cyan]\n")

    if dry_run:
        console.print("[yellow]DRY RUN MODE - No changes will be made[/yellow]\n")

    console.print("[bold]Configuration:[/bold]")
    console.print(f"  Refresh Limit: {limit:,} movies")
    console.print()

    if dry_run:
        db = DuckDBClient()
        try:
            query = """
                SELECT m.title, m.release_date, m.last_omdb_update
                FROM movies m
                WHERE m.imdb_id IS NOT NULL
                  AND m.last_omdb_update IS NOT NULL
                ORDER BY m.last_omdb_update ASC NULLS FIRST
                LIMIT ?
            """
            candidates = db.query(query, params=(limit,))

            if candidates.empty:
                console.print("[yellow]No movies due for OMDB refresh[/yellow]")
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

                # Get movies that need OMDB refresh (oldest updates first)
                query = """
                    SELECT m.*
                    FROM movies m
                    WHERE m.imdb_id IS NOT NULL
                      AND m.last_omdb_update IS NOT NULL
                    ORDER BY m.last_omdb_update ASC NULLS FIRST
                    LIMIT ?
                """
                movies_to_refresh = db.query(query, params=(limit,))

                if movies_to_refresh.empty:
                    progress.update(task, completed=True)
                    console.print("\n[yellow]No movies need OMDB refresh[/yellow]")
                    return

                _tmdb_updated, omdb_updated, _frozen = await orchestrator.refresh_movie_data(
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

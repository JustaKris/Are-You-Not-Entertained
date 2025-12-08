"""TMDB data collection CLI commands."""

import asyncio

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ayne.core.config import settings
from ayne.core.logging import configure_logging, get_logger
from ayne.data_collection.orchestrator import DataCollectionOrchestrator
from ayne.database.duckdb_client import DuckDBClient

app = typer.Typer(help="TMDB data collection and updates")
console = Console()

configure_logging(level=settings.log_level, use_json=settings.use_json_logging)  # type: ignore
logger = get_logger(__name__)


@app.command("update")
def update_tmdb(
    full: bool = typer.Option(
        False,
        "--full",
        help="Pull unlimited movies (ignores max-movies limit)",
    ),
    max_movies: int | None = typer.Option(
        None,
        "--max-movies",
        help="Maximum number of movies to discover (uses config default)",
    ),
    min_popularity: float | None = typer.Option(
        None,
        "--min-popularity",
        help="Minimum popularity score (uses config default)",
    ),
    min_votes: int | None = typer.Option(
        None,
        "--min-votes",
        help="Minimum vote count (uses config default)",
    ),
    min_year: int | None = typer.Option(
        None,
        "--min-year",
        help="Minimum release year (uses config default)",
    ),
    max_pages: int | None = typer.Option(
        None,
        "--max-pages",
        help="Maximum pages to fetch",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be done without making changes",
    ),
):
    """Discover and update movies from TMDB.

    Examples:
        ayne tmdb update --full
        ayne tmdb update --max-movies 1000 --min-year 2020
        ayne tmdb update --min-popularity 20 --dry-run
    """
    console.print("[bold cyan]TMDB Data Collection[/bold cyan]\n")

    if dry_run:
        console.print("[yellow]DRY RUN MODE - No changes will be made[/yellow]\n")

    # Full mode overrides max_movies
    if full:
        max_movies = None
        console.print("[yellow]Full mode:[/yellow] Unlimited movies\n")

    # Show configuration
    console.print("[bold]Configuration:[/bold]")
    if max_movies is not None:
        console.print(f"  Max Movies: {max_movies}")
    elif settings.tmdb_max_movies is not None:
        console.print(f"  Max Movies: {settings.tmdb_max_movies}")
    else:
        console.print("  Max Movies: Unlimited")
    console.print(f"  Min Popularity: {min_popularity or settings.tmdb_min_popularity}")
    console.print(f"  Min Votes: {min_votes or settings.tmdb_min_vote_count}")
    console.print(f"  Min Year: {min_year or settings.tmdb_min_release_year}")
    console.print(f"  Max Pages: {max_pages or 'Unlimited'}")
    console.print()

    if dry_run:
        console.print("[green]✓[/green] Dry run complete - would fetch movies with above filters")
        return

    async def _run_collection():
        db = DuckDBClient()
        orchestrator = DataCollectionOrchestrator(db)

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Discovering movies from TMDB...", total=None)

                discovered = await orchestrator.discover_and_store_movies(
                    max_movies=max_movies,
                    min_popularity=min_popularity,
                    min_vote_count=min_votes,
                    min_release_year=min_year,
                    max_pages=max_pages,
                )

                progress.update(task, completed=True)

            console.print(f"\n[green]✓[/green] Discovered and stored {discovered:,} movies")

            # Show sample
            if discovered > 0:
                sample = db.query(
                    """
                    SELECT m.title, m.release_date, t.popularity as tmdb_popularity, t.vote_count as tmdb_vote_count
                    FROM movies m
                    LEFT JOIN tmdb_movies t ON m.tmdb_id = t.tmdb_id
                    ORDER BY m.last_tmdb_update DESC
                    LIMIT 5
                    """
                )
                console.print("\n[bold]Recent additions:[/bold]")
                console.print(sample.to_string(index=False))

        except Exception as e:
            console.print(f"[red]✗ Error:[/red] {e}")
            logger.error(f"TMDB collection failed: {e}", exc_info=True)
            raise typer.Exit(code=1)
        finally:
            await orchestrator.close()
            db.close()

    asyncio.run(_run_collection())


@app.command("refresh")
def refresh_tmdb(
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
    """Refresh existing TMDB data based on age-based strategy.

    Prioritizes movies that need updates according to refresh intervals.
    """
    console.print("[bold cyan]TMDB Data Refresh[/bold cyan]\n")

    if dry_run:
        console.print("[yellow]DRY RUN MODE - No changes will be made[/yellow]\n")

    console.print("[bold]Configuration:[/bold]")
    console.print(f"  Refresh Limit: {limit:,} movies")
    console.print()

    if dry_run:
        # Show what would be refreshed
        db = DuckDBClient()
        try:
            from ayne.data_collection.refresh_strategy import get_movies_due_for_refresh_query

            query = get_movies_due_for_refresh_query(limit=limit)
            candidates = db.query(query)

            if candidates.empty:
                console.print("[yellow]No movies due for refresh[/yellow]")
            else:
                console.print(f"Would refresh {len(candidates)} movies:")
                console.print(
                    candidates[["title", "release_date", "days_old"]].to_string(index=False)
                )

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

                # Get movies that need refresh
                movies_to_refresh = orchestrator.get_movies_for_refresh(limit=limit)

                if movies_to_refresh.empty:
                    progress.update(task, completed=True)
                    console.print("\n[yellow]No movies need refresh[/yellow]")
                    return

                tmdb_updated, _omdb_updated, frozen = await orchestrator.refresh_movie_data(
                    movies_to_refresh,
                    fetch_tmdb=True,
                    fetch_omdb=False,  # TMDB only
                )

                progress.update(task, completed=True)

            console.print(f"\n[green]✓[/green] Refreshed {tmdb_updated:,} movies")
            console.print(f"[blue]ℹ[/blue] Frozen: {frozen:,} movies")

        except Exception as e:
            console.print(f"[red]✗ Error:[/red] {e}")
            logger.error(f"TMDB refresh failed: {e}", exc_info=True)
            raise typer.Exit(code=1)
        finally:
            await orchestrator.close()
            db.close()

    asyncio.run(_run_refresh())

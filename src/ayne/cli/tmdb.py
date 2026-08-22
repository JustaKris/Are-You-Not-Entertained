"""TMDB data collection CLI commands - Restructured."""

import asyncio

import typer
from rich.console import Console
from rich.progress import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TextColumn

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
    max_year: int | None = typer.Option(
        None,
        "--max-year",
        help="Maximum release year (no upper limit by default)",
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
    """Discover new movies from TMDB (basic info only).

    This command fetches basic movie information using the TMDB discover endpoint.
    Use 'ayne tmdb enrich' to fetch detailed information for discovered movies.

    Examples:
        ayne tmdb update --full
        ayne tmdb update --max-movies 1000 --min-year 2020 --max-year 2023
        ayne tmdb update --min-popularity 20 --dry-run
    """
    console.print("[bold cyan]TMDB Discovery[/bold cyan]\n")

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
    elif getattr(settings, "tmdb_max_movies", None) is not None:
        console.print(f"  Max Movies: {getattr(settings, 'tmdb_max_movies', None)}")
    else:
        console.print("  Max Movies: Unlimited")
    console.print(
        f"  Min Popularity: {min_popularity or getattr(settings, 'tmdb_min_popularity', None)}"
    )
    console.print(f"  Min Votes: {min_votes or getattr(settings, 'tmdb_min_vote_count', None)}")
    console.print(f"  Min Year: {min_year or getattr(settings, 'tmdb_min_release_year', None)}")
    console.print(
        f"  Max Year: {max_year or getattr(settings, 'tmdb_max_release_year', None) or 'Current year'}"
    )
    console.print(f"  Max Pages: {max_pages or 'Unlimited (auto-splits if >500)'}")
    console.print()

    logger.info(
        f"TMDB update: max_movies={max_movies}, min_year={min_year or getattr(settings, 'tmdb_min_release_year', None)}, "
        f"max_year={max_year or 'None'}, min_popularity={min_popularity or getattr(settings, 'tmdb_min_popularity', None)}, "
        f"dry_run={dry_run}"
    )

    if dry_run:
        console.print("[green]✓[/green] Dry run complete - would fetch movies with above filters")
        logger.debug("TMDB update dry run completed")
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
                    max_release_year=max_year or getattr(settings, "tmdb_max_release_year", None),
                    max_pages=max_pages,
                )

                progress.update(task, completed=True)

            console.print(f"\n[green]✓[/green] Discovered and stored {discovered:,} movies")

            # Show sample
            if discovered > 0:
                sample = db.query(
                    """
                    SELECT m.title, m.release_date
                    FROM movies m
                    ORDER BY m.last_tmdb_update DESC
                    LIMIT 5
                    """
                )
                console.print("\n[bold]Recent discoveries:[/bold]")
                console.print(sample.to_string(index=False))

                console.print(
                    "\n[blue]ℹ Tip:[/blue] Use 'ayne tmdb enrich' to fetch detailed data for these movies"
                )

        except Exception as e:
            console.print(f"[red]✗ Error:[/red] {e}")
            logger.error(f"TMDB discovery failed: {e}", exc_info=True)
            raise typer.Exit(code=1)
        finally:
            await orchestrator.close()
            db.close()

    try:
        asyncio.run(_run_collection())
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Operation Cancelled[/yellow]\n")
        console.print("[bold]Your progress has been saved[/bold]")
        console.print("Run the same command again to continue\n")


@app.command("enrich")
def enrich_tmdb(
    max_movies: int | None = typer.Option(
        None,
        "--max-movies",
        help="Maximum number of movies to enrich (uses --limit if not specified)",
    ),
    limit: int | None = typer.Option(
        None,
        "--limit",
        "-n",
        help="Maximum number of movies to enrich (default: 100, same as --max-movies)",
    ),
    min_year: int | None = typer.Option(
        None,
        "--min-year",
        help="Minimum release year",
    ),
    max_year: int | None = typer.Option(
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
    """Fetch detailed TMDB data for movies that only have basic info.

    This command enriches movies discovered via 'ayne tmdb update' with
    complete information including budget, revenue, genres, cast, etc.

    Examples:
        ayne tmdb enrich --max-movies 500
        ayne tmdb enrich --min-year 2023 --max-movies 100
        ayne tmdb enrich --dry-run
    """
    # Resolve max_movies (prefer max_movies, fallback to limit, then config setting)
    enrich_limit = max_movies or limit or getattr(settings, "tmdb_max_movies", None)

    # Use settings defaults for year filters if not provided
    min_year = min_year or getattr(settings, "tmdb_min_release_year", None)
    max_year = max_year or getattr(settings, "tmdb_max_release_year", None)

    console.print("[bold cyan]TMDB Enrichment[/bold cyan]\n")

    if dry_run:
        console.print("[yellow]DRY RUN MODE - No changes will be made[/yellow]\n")

    console.print("[bold]Configuration:[/bold]")
    if enrich_limit is not None:
        console.print(f"  Max Movies: {enrich_limit:,} (cap - fewer will run if fewer need it)")
    else:
        console.print("  Max Movies: No limit (all matching movies)")
    console.print(f"  Min Year: {min_year or 'No limit'}")
    console.print(f"  Max Year: {max_year or 'No limit'}")
    console.print()

    logger.info(
        f"TMDB enrich: limit={enrich_limit}, min_year={min_year}, max_year={max_year}, dry_run={dry_run}"
    )

    if dry_run:
        # Show what would be enriched
        db = DuckDBClient()
        try:
            query = """
                SELECT m.title, m.release_date
                FROM movies m
                LEFT JOIN tmdb_movies t ON m.tmdb_id = t.tmdb_id
                WHERE m.tmdb_id IS NOT NULL
                  AND t.tmdb_id IS NULL
            """

            if min_year:
                query += f" AND m.release_date >= '{min_year}-01-01'"
            if max_year:
                query += f" AND m.release_date <= '{max_year}-12-31'"

            if enrich_limit is not None:
                query += f" ORDER BY m.last_tmdb_update DESC LIMIT {enrich_limit}"
            else:
                query += " ORDER BY m.last_tmdb_update DESC"

            candidates = db.query(query)

            logger.debug(f"Dry run found {len(candidates)} candidates for enrichment")

            if candidates.empty:
                console.print("[yellow]No movies need TMDB enrichment[/yellow]")
            else:
                console.print(f"Would enrich {len(candidates)} movies:")
                console.print(candidates.head(10).to_string(index=False))
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
                BarColumn(),
                MofNCompleteColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("Enriching movies...", total=None)

                def _on_progress(completed: int, total: int) -> None:
                    progress.update(task, total=total, completed=completed)

                enriched = await orchestrator.enrich_tmdb_details(
                    limit=enrich_limit,
                    min_release_year=min_year,
                    max_release_year=max_year,
                    progress_callback=_on_progress,
                )

                progress.update(task, completed=True)

            console.print(f"\n[green]✓[/green] Enriched {enriched:,} movies with TMDB details")

            # Show sample
            if enriched > 0:
                sample = db.query(
                    """
                    SELECT m.title, t.budget, t.revenue, t.vote_average
                    FROM movies m
                    JOIN tmdb_movies t ON m.tmdb_id = t.tmdb_id
                    ORDER BY m.last_tmdb_update DESC
                    LIMIT 5
                    """
                )
                console.print("\n[bold]Recently enriched:[/bold]")
                console.print(sample.to_string(index=False))

        except Exception as e:
            console.print(f"[red]✗ Error:[/red] {e}")
            logger.error(f"TMDB enrichment failed: {e}", exc_info=True)
            raise typer.Exit(code=1)
        finally:
            await orchestrator.close()
            db.close()

    try:
        asyncio.run(_run_enrichment())
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Operation Cancelled[/yellow]\n")
        console.print("[bold]Your progress has been saved[/bold]")
        console.print("Run the same command again to continue\n")


@app.command("refresh")
def refresh_tmdb(
    limit: int | None = typer.Option(
        None,
        "--limit",
        "-n",
        help="Maximum number of movies to refresh (uses config default if not specified)",
    ),
    min_year: int | None = typer.Option(
        None,
        "--min-year",
        help="Minimum release year",
    ),
    max_year: int | None = typer.Option(
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
    """Refresh existing TMDB data for movies that need updates.

    This command only updates movies that already have TMDB details and are
    due for a refresh based on age-based refresh intervals (5-180 days).

    Use this for daily/weekly updates to keep recent movie data current.

    Examples:
        ayne tmdb refresh --limit 100
        ayne tmdb refresh --min-year 2024 --limit 50  # Recent releases only
        ayne tmdb refresh --dry-run
    """
    console.print("[bold cyan]TMDB Data Refresh[/bold cyan]\n")

    if dry_run:
        console.print("[yellow]DRY RUN MODE - No changes will be made[/yellow]\n")

    # Use settings defaults for filters if not provided
    limit = limit if limit is not None else getattr(settings, "tmdb_max_movies", None)
    min_year = min_year or getattr(settings, "tmdb_min_release_year", None)
    max_year = max_year or getattr(settings, "tmdb_max_release_year", None)

    console.print("[bold]Configuration:[/bold]")
    console.print(f"  Refresh Limit: {f'{limit:,} movies' if limit else 'Unlimited'}")
    console.print(f"  Min Year: {min_year or 'No limit'}")
    console.print(f"  Max Year: {max_year or 'No limit'}")
    console.print()

    logger.info(
        f"TMDB refresh: limit={limit}, min_year={min_year}, max_year={max_year}, dry_run={dry_run}"
    )

    if dry_run:
        # Show what would be refreshed
        db = DuckDBClient()
        try:
            orchestrator = DataCollectionOrchestrator(db)
            candidates = orchestrator.get_movies_for_refresh(
                limit=limit,
                min_release_year=min_year,
                max_release_year=max_year,
                data_source="tmdb",  # Only TMDB refresh candidates
            )

            if candidates.empty:
                console.print("[yellow]No movies due for refresh[/yellow]")
            else:
                console.print(f"Would refresh {len(candidates)} movies:")
                display_df = candidates[["title", "release_date"]].copy()
                if "days_old" in candidates.columns:
                    display_df["days_old"] = candidates["days_old"]
                console.print(display_df.head(10).to_string(index=False))
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
                if limit is not None:
                    task = progress.add_task(f"Refreshing up to {limit:,} movies...", total=None)
                else:
                    task = progress.add_task("Refreshing movies (no limit)...", total=None)

                # Get movies that need TMDB refresh specifically
                movies_to_refresh = orchestrator.get_movies_for_refresh(
                    limit=limit,
                    min_release_year=min_year,
                    max_release_year=max_year,
                    data_source="tmdb",  # Only get movies needing TMDB refresh
                )

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
            if frozen > 0:
                console.print(f"[blue]ℹ[/blue] Frozen: {frozen:,} stable movies")

        except Exception as e:
            console.print(f"[red]✗ Error:[/red] {e}")
            logger.error(f"TMDB refresh failed: {e}", exc_info=True)
            raise typer.Exit(code=1)
        finally:
            await orchestrator.close()
            db.close()

    try:
        asyncio.run(_run_refresh())
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Operation Cancelled[/yellow]\n")
        console.print("[bold]Your progress has been saved[/bold]")
        console.print("Run the same command again to continue\n")

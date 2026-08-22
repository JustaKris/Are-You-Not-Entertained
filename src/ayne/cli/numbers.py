"""The Numbers (box office) data enrichment CLI commands."""

import asyncio
from typing import cast

import typer
from rich.progress import Progress, SpinnerColumn, TextColumn

from ayne.cli.progress import DeterminateBarColumn, DeterminateMofNCompleteColumn
from ayne.core.config import Settings
from ayne.core.config import settings as _settings
from ayne.core.logging import configure_logging, get_logger, logging_console
from ayne.data_collection.orchestrator import DataCollectionOrchestrator
from ayne.database.duckdb_client import DuckDBClient

app = typer.Typer(help="The Numbers (box office) data enrichment")
console = logging_console

settings = cast(Settings, _settings)
configure_logging(level=settings.log_level, use_json=settings.use_json_logging)  # type: ignore
logger = get_logger(__name__)


@app.command("enrich")
def enrich_numbers(
    max_movies: int | None = typer.Option(
        None,
        "--max-movies",
        help="Maximum number of movies to enrich (uses config default, kept small and polite by design)",
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
    """Enrich movies with box office/budget data scraped from The Numbers.

    The Numbers has no public API, so this fetches the same public movie
    pages a browser would, at a deliberately slow, polite rate configured by
    settings.numbers_requests_per_second
    to avoid being rate limited or banned.

    Examples:
        ayne numbers enrich --max-movies 50
        ayne numbers enrich --min-year 2023 --max-movies 20
        ayne numbers enrich --dry-run
    """
    console.print("[bold]====================================[/bold]")
    console.print("[bold cyan]The Numbers Enrichment[/bold cyan]\n")

    if dry_run:
        console.print("[yellow]DRY RUN MODE - No changes will be made[/yellow]\n")

    max_movies = max_movies if max_movies is not None else settings.numbers_max_movies

    console.print("[bold]Configuration:[/bold]")
    console.print(f"  Max Movies: {max_movies:,} (cap - fewer will run if fewer need it)")
    request_interval = 1 / settings.numbers_requests_per_second
    console.print(
        f"  Rate Limit: {settings.numbers_requests_per_second:g} req/sec "
        f"(~{request_interval:.1f}s between requests)"
    )
    console.print(f"  Min Year: {min_year or 'No limit'}")
    console.print(f"  Max Year: {max_year or 'No limit'}")
    console.print("[bold]====================================[/bold]")
    console.print()

    logger.info(
        f"Numbers enrich: max_movies={max_movies}, min_year={min_year}, "
        f"max_year={max_year}, dry_run={dry_run}"
    )

    if dry_run:
        db = DuckDBClient()
        try:
            query = """
                SELECT m.title, m.release_date
                FROM movies m
                LEFT JOIN numbers_movies n ON m.movie_id = n.movie_id
                WHERE n.movie_id IS NULL
                  AND m.release_date IS NOT NULL
            """

            if min_year:
                query += f" AND m.release_date >= '{min_year}-01-01'"
            if max_year:
                query += f" AND m.release_date <= '{max_year}-12-31'"

            query += f" ORDER BY m.release_date DESC LIMIT {max_movies}"

            candidates = db.query(query)

            if candidates.empty:
                console.print("[yellow]No movies need The Numbers enrichment[/yellow]")
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
                DeterminateBarColumn(),
                DeterminateMofNCompleteColumn(),
                console=console,
            ) as progress:
                task = progress.add_task(
                    f"Scraping from The Numbers (~{settings.numbers_requests_per_second:g} req/sec, "
                    "this can take a while)...",
                    total=None,
                )

                def _on_progress(completed: int, total: int) -> None:
                    progress.update(task, total=total, completed=completed)

                enriched = await orchestrator.enrich_numbers_data(
                    limit=max_movies,
                    min_release_year=min_year,
                    max_release_year=max_year,
                    progress_callback=_on_progress,
                )

            console.print(f"\n[green]✓[/green] Enriched {enriched:,} movies with The Numbers data")

            if enriched > 0:
                sample = db.query(
                    """
                    SELECT m.title, n.domestic_box_office, n.worldwide_box_office, n.production_budget
                    FROM numbers_movies n
                    JOIN movies m ON n.movie_id = m.movie_id
                    ORDER BY m.last_numbers_update DESC
                    LIMIT 5
                    """
                )
                console.print("\n[bold]Recently enriched:[/bold]")
                console.print(sample.to_string(index=False))

        except Exception as e:
            console.print(f"[red]✗ Error:[/red] {e}")
            logger.error(f"The Numbers enrichment failed: {e}", exc_info=True)
            raise typer.Exit(code=1)
        finally:
            await orchestrator.close()
            db.close()

    try:
        asyncio.run(_run_enrichment())
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Operation Cancelled[/yellow]\n")
        console.print("[bold]Any movies already scraped this run have been saved[/bold]")
        console.print("Run the same command again to continue\n")

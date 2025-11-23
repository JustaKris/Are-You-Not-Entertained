"""Combined data collection workflows CLI commands."""

import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ayne.core.config import settings
from ayne.core.logging import configure_logging, get_logger
from ayne.data_collection.orchestrator import DataCollectionOrchestrator
from ayne.database.duckdb_client import DuckDBClient

app = typer.Typer(help="Combined data collection workflows")
console = Console()

configure_logging(level=settings.log_level, use_json=settings.use_json_logging)  # type: ignore
logger = get_logger(__name__)


@app.command("daily")
def daily_refresh(
    tmdb_refresh: int = typer.Option(
        100,
        "--tmdb-refresh",
        help="Number of TMDB records to refresh",
    ),
    omdb_limit: Optional[int] = typer.Option(
        None,
        "--omdb-limit",
        help="Maximum OMDB enrichments (uses config default)",
    ),
    discover: bool = typer.Option(
        False,
        "--discover",
        help="Also discover new movies from TMDB",
    ),
    discover_limit: Optional[int] = typer.Option(
        None,
        "--discover-limit",
        help="Limit for new movie discovery",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be done without making changes",
    ),
):
    """Run daily data refresh workflow.

    Refreshes existing data and optionally discovers new movies.
    Suitable for scheduled daily runs.

    Examples:
        ayne collect daily
        ayne collect daily --discover --discover-limit 500
        ayne collect daily --tmdb-refresh 200 --omdb-limit 500
    """
    console.print("[bold cyan]Daily Data Refresh Workflow[/bold cyan]\n")

    if dry_run:
        console.print("[yellow]DRY RUN MODE - No changes will be made[/yellow]\n")

    omdb_limit = omdb_limit or settings.omdb_max_movies

    # Show configuration
    config_table = Table(title="Workflow Configuration", show_header=True)
    config_table.add_column("Task", style="cyan")
    config_table.add_column("Setting", style="green")

    config_table.add_row("TMDB Refresh", f"{tmdb_refresh:,} movies")
    config_table.add_row("OMDB Enrichment", f"{omdb_limit:,} movies")
    if discover:
        config_table.add_row("Discovery", f"Enabled ({discover_limit or 'unlimited'} movies)")
    else:
        config_table.add_row("Discovery", "Disabled")

    console.print(config_table)
    console.print()

    if dry_run:
        console.print("[green]✓[/green] Dry run complete - would execute above workflow")
        return

    async def _run_workflow():
        db = DuckDBClient()
        orchestrator = DataCollectionOrchestrator(db)

        try:
            stats = await orchestrator.run_full_collection(
                discover_movies=discover,
                max_discover_movies=discover_limit,
                refresh_limit=tmdb_refresh,
                omdb_max_movies=omdb_limit,
            )

            # Display summary
            console.print("\n[bold green]✓ Workflow Complete[/bold green]\n")

            summary = Table(title="Collection Summary", show_header=True)
            summary.add_column("Metric", style="cyan")
            summary.add_column("Count", justify="right", style="green")

            summary.add_row("Movies Discovered", f"{stats['discovered']:,}")
            summary.add_row("TMDB Updates", f"{stats['tmdb_updated']:,}")
            summary.add_row("OMDB Updates", f"{stats['omdb_updated']:,}")
            summary.add_row("Movies Frozen", f"{stats['frozen']:,}")

            console.print(summary)

        except Exception as e:
            console.print(f"[red]✗ Error:[/red] {e}")
            logger.error(f"Daily workflow failed: {e}", exc_info=True)
            raise typer.Exit(code=1)
        finally:
            await orchestrator.close()
            db.close()

    asyncio.run(_run_workflow())


@app.command("full")
def full_collection(
    max_tmdb: Optional[int] = typer.Option(
        None,
        "--max-tmdb",
        help="Maximum TMDB movies to discover (None = unlimited)",
    ),
    max_omdb: Optional[int] = typer.Option(
        None,
        "--max-omdb",
        help="Maximum OMDB enrichments (uses config default)",
    ),
    min_popularity: Optional[float] = typer.Option(
        None,
        "--min-popularity",
        help="Minimum popularity filter (uses config default)",
    ),
    min_year: Optional[int] = typer.Option(
        None,
        "--min-year",
        help="Minimum release year (uses config default)",
    ),
    refresh_limit: int = typer.Option(
        100,
        "--refresh-limit",
        help="Maximum movies to refresh",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be done without making changes",
    ),
):
    """Run full data collection workflow.

    Discovers new movies, refreshes existing data, and enriches with OMDB.
    Use for initial data population or comprehensive updates.

    Examples:
        ayne collect full --max-tmdb 5000 --max-omdb 1000
        ayne collect full --min-year 2020 --min-popularity 20
    """
    console.print("[bold cyan]Full Data Collection Workflow[/bold cyan]\n")

    if dry_run:
        console.print("[yellow]DRY RUN MODE - No changes will be made[/yellow]\n")

    max_omdb = max_omdb or settings.omdb_max_movies

    # Show configuration
    config_table = Table(title="Workflow Configuration", show_header=True)
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="green")

    config_table.add_row("Max TMDB Discovery", f"{max_tmdb:,}" if max_tmdb else "Unlimited")
    config_table.add_row("Max OMDB Enrichment", f"{max_omdb:,}")
    config_table.add_row("Refresh Limit", f"{refresh_limit:,}")
    config_table.add_row(
        "Min Popularity",
        f"{min_popularity}" if min_popularity else f"{settings.tmdb_min_popularity} (default)",
    )
    config_table.add_row(
        "Min Year",
        f"{min_year}" if min_year else f"{settings.tmdb_min_release_year} (default)",
    )

    console.print(config_table)
    console.print()

    if dry_run:
        console.print("[green]✓[/green] Dry run complete - would execute above workflow")
        return

    async def _run_workflow():
        db = DuckDBClient()
        orchestrator = DataCollectionOrchestrator(db)

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Running full collection workflow...", total=None)

                stats = await orchestrator.run_full_collection(
                    discover_movies=True,
                    max_discover_movies=max_tmdb,
                    refresh_limit=refresh_limit,
                    min_popularity=min_popularity,
                    min_release_year=min_year,
                    omdb_max_movies=max_omdb,
                )

                progress.update(task, completed=True)

            # Display comprehensive summary
            console.print("\n[bold green]✓ Full Collection Complete[/bold green]\n")

            summary = Table(title="Collection Summary", show_header=True)
            summary.add_column("Metric", style="cyan")
            summary.add_column("Count", justify="right", style="green")

            summary.add_row("Movies Discovered", f"{stats['discovered']:,}")
            summary.add_row("TMDB Updates", f"{stats['tmdb_updated']:,}")
            summary.add_row("OMDB Updates", f"{stats['omdb_updated']:,}")
            summary.add_row("Movies Frozen", f"{stats['frozen']:,}")

            console.print(summary)

            # Show database stats
            db_stats = db.get_collection_stats()
            if not db_stats.empty:
                row = db_stats.iloc[0]

                stats_table = Table(title="\nDatabase Status", show_header=True)
                stats_table.add_column("Metric", style="cyan")
                stats_table.add_column("Count", justify="right", style="green")

                stats_table.add_row("Total Movies", f"{row['total_movies']:,}")
                stats_table.add_row("With TMDB Data", f"{row['with_tmdb']:,}")
                stats_table.add_row("With OMDB Data", f"{row['with_omdb']:,}")
                stats_table.add_row("Fully Refreshed", f"{row['fully_refreshed']:,}")

                console.print(stats_table)

        except Exception as e:
            console.print(f"[red]✗ Error:[/red] {e}")
            logger.error(f"Full collection failed: {e}", exc_info=True)
            raise typer.Exit(code=1)
        finally:
            await orchestrator.close()
            db.close()

    asyncio.run(_run_workflow())

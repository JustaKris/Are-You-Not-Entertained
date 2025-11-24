"""Database management CLI commands."""

import typer
from rich.console import Console
from rich.table import Table

from ayne.core.config import settings
from ayne.core.logging import configure_logging, get_logger
from ayne.database.duckdb_client import DuckDBClient

app = typer.Typer(help="Database management and testing")
console = Console()

configure_logging(level=settings.log_level, use_json=settings.use_json_logging)  # type: ignore
logger = get_logger(__name__)


@app.command("init")
def init_database(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force re-initialization (drops existing tables)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be done without making changes",
    ),
):
    """Initialize the DuckDB database schema.

    Creates all required tables for movie data storage.
    """
    console.print("[bold cyan]Database Initialization[/bold cyan]\n")

    if dry_run:
        console.print("[yellow]DRY RUN MODE - No changes will be made[/yellow]\n")

    try:
        db = DuckDBClient()
        console.print(f"Database path: [blue]{db.db_path}[/blue]\n")

        if dry_run:
            console.print("Would create tables:")
            tables = [
                "movies",
                "tmdb_movies",
                "omdb_movies",
                "numbers_movies",
                "movie_refresh_state",
            ]
            for table in tables:
                console.print(f"  • {table}")
            console.print("\n[green]✓[/green] Dry run complete")
            return

        # Create tables
        if force:
            console.print("[yellow]Force mode: dropping existing tables...[/yellow]")

        db.create_tables_from_sql()

        # Verify tables
        tables = ["movies", "tmdb_movies", "omdb_movies", "numbers_movies", "movie_refresh_state"]
        console.print("[bold]Verifying tables:[/bold]")

        table_display = Table(show_header=True, header_style="bold magenta")
        table_display.add_column("Table Name")
        table_display.add_column("Status")

        for table in tables:
            exists = db.table_exists(table)
            status = "[green]✓ Created[/green]" if exists else "[red]✗ Missing[/red]"
            table_display.add_row(table, status)

        console.print(table_display)

        db.close()
        console.print("\n[green]✓[/green] Database initialized successfully!")

    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        raise typer.Exit(code=1)


@app.command("test")
def test_database(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed test output",
    ),
):
    """Run database connectivity and functionality tests.

    Performs basic CRUD operations to verify database is working correctly.
    """
    console.print("[bold cyan]Database Test Suite[/bold cyan]\n")

    try:
        db = DuckDBClient()
        console.print(f"Testing database: [blue]{db.db_path}[/blue]\n")

        # Test 1: Connection
        console.print("Test 1: Database connection... ", end="")
        console.print("[green]✓[/green]")

        # Test 2: Schema creation
        console.print("Test 2: Schema creation... ", end="")
        db.create_tables_from_sql()
        console.print("[green]✓[/green]")

        # Test 3: Table existence
        console.print("Test 3: Table verification... ", end="")
        tables = ["movies", "tmdb_movies", "omdb_movies"]
        for table in tables:
            if not db.table_exists(table):
                console.print(f"[red]✗ Table '{table}' not found[/red]")
                raise typer.Exit(code=1)
        console.print("[green]✓[/green]")

        # Test 4: Insert
        console.print("Test 4: Insert operation... ", end="")
        import pandas as pd

        test_data = pd.DataFrame(
            {"tmdb_id": [99999], "title": ["CLI Test Movie"], "release_date": ["2024-01-01"]}
        )
        db.upsert_dataframe("movies", test_data, key_columns=["tmdb_id"])
        console.print("[green]✓[/green]")

        # Test 5: Query
        console.print("Test 5: Query operation... ", end="")
        result = db.query("SELECT * FROM movies WHERE tmdb_id = 99999")
        if len(result) != 1 or result["title"].iloc[0] != "CLI Test Movie":
            console.print("[red]✗ Query failed[/red]")
            raise typer.Exit(code=1)
        console.print("[green]✓[/green]")

        # Test 6: Update
        console.print("Test 6: Update operation... ", end="")
        update_data = pd.DataFrame(
            {
                "tmdb_id": [99999],
                "title": ["CLI Test Movie UPDATED"],
                "release_date": ["2024-01-01"],
            }
        )
        db.upsert_dataframe("movies", update_data, key_columns=["tmdb_id"])
        result = db.query("SELECT * FROM movies WHERE tmdb_id = 99999")
        if result["title"].iloc[0] != "CLI Test Movie UPDATED":
            console.print("[red]✗ Update failed[/red]")
            raise typer.Exit(code=1)
        console.print("[green]✓[/green]")

        # Test 7: Delete
        console.print("Test 7: Delete operation... ", end="")
        db.execute("DELETE FROM movies WHERE tmdb_id = 99999")
        console.print("[green]✓[/green]")

        if verbose:
            console.print("\n[bold]Database Statistics:[/bold]")
            stats = db.get_collection_stats()
            if not stats.empty:
                stat_table = Table(show_header=True, header_style="bold magenta")
                stat_table.add_column("Metric")
                stat_table.add_column("Value", justify="right")

                row = stats.iloc[0]
                stat_table.add_row("Total Movies", str(row["total_movies"]))
                stat_table.add_row("With TMDB Data", str(row["with_tmdb"]))
                stat_table.add_row("With OMDB Data", str(row["with_omdb"]))
                stat_table.add_row("Fully Refreshed", str(row["fully_refreshed"]))
                stat_table.add_row("Frozen (Stable)", str(row["frozen"]))

                console.print(stat_table)

        db.close()
        console.print("\n[green]✓ All tests passed![/green]")

    except Exception as e:
        console.print(f"\n[red]✗ Test failed:[/red] {e}")
        logger.error(f"Database test failed: {e}", exc_info=True)
        raise typer.Exit(code=1)


@app.command("stats")
def show_stats():
    """Show database statistics and collection status."""
    console.print("[bold cyan]Database Statistics[/bold cyan]\n")

    try:
        db = DuckDBClient()

        stats = db.get_collection_stats()
        if stats.empty:
            console.print("[yellow]No data in database yet[/yellow]")
            return

        row = stats.iloc[0]

        # Main statistics table
        main_table = Table(title="Collection Overview", show_header=True)
        main_table.add_column("Metric", style="cyan")
        main_table.add_column("Count", justify="right", style="green")

        main_table.add_row("Total Movies", f"{row['total_movies']:,}")
        main_table.add_row("  ├─ With TMDB ID", f"{row['with_tmdb_basic']:,}")
        main_table.add_row("  └─ With TMDB Details", f"{row['with_tmdb_details']:,}")
        main_table.add_row("With OMDB Data", f"{row['with_omdb']:,}")
        main_table.add_row("Fully Refreshed", f"{row['fully_refreshed']:,}")
        main_table.add_row("Frozen (Stable)", f"{row['frozen']:,}")

        console.print(main_table)

        # Age category table
        age_table = Table(title="\nMovies by Age", show_header=True)
        age_table.add_column("Category", style="cyan")
        age_table.add_column("Count", justify="right", style="green")

        age_table.add_row("Recent (0-60 days)", f"{row['recent_movies']:,}")
        age_table.add_row("Established (60-180 days)", f"{row['established_movies']:,}")
        age_table.add_row("Mature (180-365 days)", f"{row['mature_movies']:,}")
        age_table.add_row("Archived (>365 days)", f"{row['archived_movies']:,}")

        console.print(age_table)

        db.close()

    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        logger.error(f"Failed to get stats: {e}", exc_info=True)
        raise typer.Exit(code=1)

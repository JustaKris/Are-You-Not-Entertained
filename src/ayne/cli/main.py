"""Main CLI entry point for AYNE (Are You Not Entertained).

Modern CLI built with Typer for data collection, validation, and database management.
"""

import typer
from rich.console import Console

from ayne.cli import collect, db, omdb, tmdb, validate
from ayne.core.config import settings

app = typer.Typer(
    name="ayne",
    help="Are You Not Entertained - Movie Data Collection & ML Pipeline",
    no_args_is_help=True,
    pretty_exceptions_enable=True,
)

console = Console()

# Register subcommands
app.add_typer(db.app, name="db", help="Database management commands")
app.add_typer(tmdb.app, name="tmdb", help="TMDB data collection commands")
app.add_typer(omdb.app, name="omdb", help="OMDB data enrichment commands")
app.add_typer(collect.app, name="collect", help="Combined data collection workflows")
app.add_typer(validate.app, name="validate", help="Data validation commands")


@app.callback()
def main_callback():
    """AYNE CLI - Movie data collection and ML pipeline."""
    pass


@app.command()
def version():
    """Show version and configuration information."""
    from ayne import __version__

    console.print(f"[bold cyan]AYNE[/bold cyan] version [yellow]{__version__}[/yellow]")
    console.print(f"Environment: [green]{settings.environment}[/green]")
    console.print(f"Database: [blue]{settings.duckdb_path}[/blue]")


@app.command()
def config():
    """Show current configuration settings."""
    console.print("\n[bold cyan]Current Configuration[/bold cyan]\n")

    console.print("[yellow]Environment:[/yellow]")
    console.print(f"  Environment: {settings.environment}")
    console.print(f"  Log Level: {settings.log_level}")
    console.print(f"  Use JSON Logging: {settings.use_json_logging}")

    console.print("\n[yellow]Database:[/yellow]")
    console.print(f"  DuckDB Path: {settings.duckdb_path}")

    console.print("\n[yellow]TMDB API:[/yellow]")
    console.print(f"  Base URL: {settings.tmdb_base_url}")
    console.print(f"  Rate Limit: {settings.tmdb_rate_limit_per_second} req/sec")
    console.print(f"  Min Popularity: {settings.tmdb_min_popularity}")
    console.print(f"  Min Vote Count: {settings.tmdb_min_vote_count}")
    console.print(f"  Min Release Year: {settings.tmdb_min_release_year}")
    console.print(f"  Max Movies Per Run: {settings.tmdb_max_movies or 'Unlimited'}")
    console.print(f"  Allowed Statuses: {', '.join(settings.tmdb_allowed_release_statuses)}")

    console.print("\n[yellow]OMDB API:[/yellow]")
    console.print(f"  Base URL: {settings.omdb_base_url}")
    console.print(f"  Rate Limit: {settings.omdb_rate_limit_per_second} req/sec")
    console.print(f"  Max Movies Per Run: {settings.omdb_max_movies}")


if __name__ == "__main__":
    app()

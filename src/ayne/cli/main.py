"""Main CLI entry point for AYNE (Are You Not Entertained).

Modern CLI built with Typer for data collection, validation, and database management.
"""

import typer
from rich.console import Console

from ayne.cli import collect, db, numbers, omdb, tmdb, validate
from ayne.core.config.config_loader import settings

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
app.add_typer(numbers.app, name="numbers", help="The Numbers (box office) data enrichment commands")
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

    console.print("\n[yellow]API Rate Limiting (shared):[/yellow]")
    console.print(f"  Rate Limit: {settings.api_rate_limit} req/sec")
    console.print(f"  Timeout: {settings.api_timeout}s")

    console.print("\n[yellow]TMDB API:[/yellow]")
    console.print(f"  Base URL: {settings.tmdb_api_base_url}")
    console.print(f"  Min Popularity: {settings.tmdb_min_popularity}")
    console.print(f"  Min Vote Count: {settings.tmdb_min_vote_count}")
    console.print(f"  Min Release Year: {settings.tmdb_min_release_year}")
    console.print(f"  Max Release Year: {settings.tmdb_max_release_year or 'Current year'}")
    console.print(f"  Max Movies Per Run: {settings.tmdb_max_movies or 'Unlimited'}")
    console.print(f"  Allowed Statuses: {', '.join(settings.tmdb_allowed_release_statuses)}")

    console.print("\n[yellow]OMDB API:[/yellow]")
    console.print(f"  Base URL: {settings.omdb_api_base_url}")
    console.print(f"  Max Movies Per Run: {settings.omdb_max_movies}")
    console.print(f"  Daily Request Limit: {settings.omdb_daily_request_limit}")
    console.print(f"  Min Release Year: {settings.omdb_min_release_year or 'No limit'}")
    console.print(f"  Max Release Year: {settings.omdb_max_release_year or 'No limit'}")

    console.print("\n[yellow]The Numbers (box office):[/yellow]")
    console.print(f"  Max Movies Per Run: {settings.numbers_max_movies}")
    numbers_interval = 1 / settings.numbers_requests_per_second
    console.print(
        f"  Rate Limit: {settings.numbers_requests_per_second:g} req/sec "
        f"(~{numbers_interval:.1f}s between requests)"
    )


if __name__ == "__main__":
    app()

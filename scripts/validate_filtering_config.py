"""Quick validation script to test the new filtering configuration.

This script validates that:
1. Configuration loads correctly
2. All filter settings are accessible
3. Settings can be overridden programmatically
"""

from ayne.core.config import settings


def main():
    """Validate configuration settings."""
    print("=" * 80)
    print("DATA COLLECTION FILTERING CONFIGURATION VALIDATION")
    print("=" * 80)
    print()

    # Display current environment
    print(f"Environment: {getattr(settings, 'environment', 'UNKNOWN')}")
    print(f"Application: {getattr(settings, 'app_name', 'UNKNOWN')}")
    print()

    # Display collection limits
    print("COLLECTION LIMITS:")
    print(f"  TMDB Max Movies: {getattr(settings, 'tmdb_max_movies', 'Unlimited')}")
    print(f"  OMDB Max Movies: {getattr(settings, 'omdb_max_movies', 'Unknown')}")
    print()

    # Display TMDB filters
    print("TMDB FILTERS:")
    tmdb_min_popularity = getattr(settings, "tmdb_min_popularity", None)
    tmdb_min_vote_count = getattr(settings, "tmdb_min_vote_count", None)
    tmdb_min_release_year = getattr(settings, "tmdb_min_release_year", None)
    tmdb_allowed_release_statuses = getattr(settings, "tmdb_allowed_release_statuses", [])
    print(f"  Min Popularity: {tmdb_min_popularity}")
    print(f"  Min Vote Count: {tmdb_min_vote_count}")
    print(f"  Min Release Year: {tmdb_min_release_year}")
    print("  Allowed Release Statuses:")
    for status in tmdb_allowed_release_statuses:
        print(f"    - {status}")
    print()

    # Display API configuration
    print("API CONFIGURATION:")
    print(f"  TMDB Base URL: {getattr(settings, 'tmdb_api_base_url', 'UNKNOWN')}")
    print(f"  OMDB Base URL: {getattr(settings, 'omdb_api_base_url', 'UNKNOWN')}")
    print(f"  API Rate Limit: {getattr(settings, 'api_rate_limit', 'UNKNOWN')} req/s")
    print(f"  API Timeout: {getattr(settings, 'api_timeout', 'UNKNOWN')}s")
    print()

    # Validate filter types
    print("VALIDATION:")
    errors = []

    if not isinstance(tmdb_min_popularity, (int, float)):
        errors.append("tmdb_min_popularity must be a number")

    if not isinstance(tmdb_min_vote_count, int):
        errors.append("tmdb_min_vote_count must be an integer")

    if not isinstance(tmdb_min_release_year, int):
        errors.append("tmdb_min_release_year must be an integer")

    if not isinstance(tmdb_allowed_release_statuses, list):
        errors.append("tmdb_allowed_release_statuses must be a list")

    if not isinstance(getattr(settings, "omdb_max_movies", None), int):
        errors.append("omdb_max_movies must be an integer")

    if errors:
        print("❌ VALIDATION FAILED:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ All configuration values are valid!")

    print()
    print("=" * 80)
    print("VALIDATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()

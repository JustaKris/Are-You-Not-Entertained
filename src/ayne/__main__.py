"""Entry point for running ayne as a module: python -m ayne

This allows the package to be executed directly.
"""

import sys


def main():
    """Main entry point for the ayne package."""
    print("AYNE - Are You Not Entertained?")
    print("=" * 60)
    print()
    print("This is a movie box office analysis and prediction toolkit.")
    print()
    print("Available commands:")
    print("  python -m ayne.scripts.init_database     # Initialize database")
    print("  python -m ayne.scripts.collect_optimized # Collect movie data")
    print()
    print("For more information, see the documentation:")
    print("  docs/README.md")
    print()
    print("Package structure:")
    print("  - ayne.core: Configuration and logging")
    print("  - ayne.data_collection: API clients")
    print("  - ayne.database: DuckDB client")
    print("  - ayne.utils: Data utilities")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())

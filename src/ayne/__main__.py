"""Entry point for running ayne as a module: python -m ayne

This allows the package to be executed directly.
"""

from ayne.cli.main import app

if __name__ == "__main__":
    app()

"""Quick validation that notebook imports work correctly."""

import os

from pyprojroot import here

# Test imports
from ayne.core.config import settings
from ayne.utils.query_utils import load_full_dataset

os.chdir(here())

print("Testing notebook imports...")
print("=" * 60)

print("✅ All imports successful!")
db_path = settings.duckdb_path  # type: ignore
print(f"✅ Database location: {db_path}")
print(f"✅ Database exists: {db_path.exists()}")

# Test loading
print("\nTesting data loading...")
df = load_full_dataset(include_nulls=True)
print(f"✅ Loaded {len(df)} movies with {len(df.columns)} columns")

print("\n" + "=" * 60)
print("✅ Notebook setup validated - ready to use!")
print("=" * 60)

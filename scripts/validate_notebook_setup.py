"""Quick validation that notebook imports work correctly."""

import os

from pyprojroot import here

# Test imports
from src.core.config import settings
from src.data.query_utils import load_full_dataset

os.chdir(here())

print("Testing notebook imports...")
print("=" * 60)

print("✅ All imports successful!")
print(f"✅ Database location: {settings.duckdb_path}")
print(f"✅ Database exists: {settings.duckdb_path.exists()}")

# Test loading
print("\nTesting data loading...")
df = load_full_dataset(include_nulls=True)
print(f"✅ Loaded {len(df)} movies with {len(df.columns)} columns")

print("\n" + "=" * 60)
print("✅ Notebook setup validated - ready to use!")
print("=" * 60)

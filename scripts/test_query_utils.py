"""Test script for new data query utilities."""

import pandas as pd

from ayne.utils.query_utils import (
    get_movies_with_financials,
    get_table_info,
    load_full_dataset,
    save_processed_data,
)

print("=" * 60)
print("Testing Data Query Utilities")
print("=" * 60)

# Test 1: Load full dataset
print("\n1. Testing load_full_dataset()...")
df = load_full_dataset()
print(f"   ✅ Loaded {len(df)} movies with {len(df.columns)} columns")
print(f"   First 5 columns: {list(df.columns[:5])}")

# Test 2: Get movies with financials
print("\n2. Testing get_movies_with_financials()...")
df_fin = get_movies_with_financials(min_budget=1_000_000)
print(f"   ✅ Found {len(df_fin)} movies with budget >= $1M")
print(f"   Average budget: ${df_fin['budget'].mean():,.0f}")
print(f"   Average revenue: ${df_fin['revenue'].mean():,.0f}")

# Test 3: Get table info
print("\n3. Testing get_table_info()...")
info = get_table_info("movies")
print(f"   ✅ Table 'movies' has {len(info)} columns")
print("   First 5 columns:")
for _, row in info.head().iterrows():
    print(f"      - {row['column_name']}: {row['column_type']}")

# Test 4: Save processed data
print("\n4. Testing save_processed_data()...")
df_sample = df.head(100)
path = save_processed_data(df_sample, "test_sample", format="parquet")
print(f"   ✅ Saved test data to {path}")

# Verify saved data
df_loaded = pd.read_parquet(path)
print(f"   ✅ Verified: loaded {len(df_loaded)} rows")

print("\n" + "=" * 60)
print("✅ All tests passed!")
print("=" * 60)

"""Test script for modern utilities."""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

from ayne.ml.models.serialize import load_model, save_model
from ayne.utils.io import load_dataframe, save_dataframe


def test_io_utilities():
    """Test I/O utilities for DataFrames."""
    print("Testing I/O utilities...")

    # Create test data
    df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6], "c": [7, 8, 9]})

    # Test Parquet
    path = save_dataframe(df, "test_io_parquet", directory="data/processed", format="parquet")
    print(f"✅ Saved Parquet to: {path}")

    df_loaded = load_dataframe(path)
    assert len(df_loaded) == 3, "Failed to load correct number of rows"
    assert list(df_loaded.columns) == ["a", "b", "c"], "Failed to preserve columns"
    print(f"✅ Loaded Parquet: {len(df_loaded)} rows × {len(df_loaded.columns)} columns")

    # Test CSV
    path_csv = save_dataframe(df, "test_io_csv", directory="data/processed", format="csv")
    print(f"✅ Saved CSV to: {path_csv}")

    df_csv = load_dataframe(path_csv)
    assert len(df_csv) == 3, "Failed to load CSV"
    print(f"✅ Loaded CSV: {len(df_csv)} rows")

    print("✅ All I/O tests passed!\n")


def test_model_serialization():
    """Test model serialization utilities."""
    print("Testing model serialization...")

    # Create and train a simple model
    X = np.random.rand(50, 5)
    y = np.random.rand(50)
    model = RandomForestRegressor(n_estimators=10, random_state=42, max_depth=3)
    model.fit(X, y)

    # Test save with metadata
    metadata = {
        "test_run": True,
        "n_features": 5,
        "model_params": {"n_estimators": 10, "max_depth": 3},
    }

    path = save_model(model, "test_rf_model", metadata=metadata)
    print(f"✅ Saved model to: {path}")

    # Test load without metadata
    loaded_model = load_model(path)
    assert isinstance(
        loaded_model, RandomForestRegressor
    ), f"Expected RandomForestRegressor, got {type(loaded_model)}"
    print(f"✅ Loaded model type: {type(loaded_model).__name__}")

    # Test load with metadata
    loaded_model2, loaded_metadata = load_model(path, load_metadata=True)
    assert loaded_metadata.get("test_run") is True, "Metadata not loaded correctly"
    assert loaded_metadata.get("n_features") == 5, "Metadata values incorrect"
    print(f"✅ Loaded metadata: {loaded_metadata.get('model_class')}")

    # Test predictions work
    predictions = loaded_model.predict(X[:5])
    assert len(predictions) == 5, "Failed to make predictions"
    print(f"✅ Model predictions work: {len(predictions)} predictions")

    print("✅ All model serialization tests passed!\n")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Modern Utilities")
    print("=" * 60 + "\n")

    test_io_utilities()
    test_model_serialization()

    print("=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)

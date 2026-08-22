# Modern Utilities Guide

This guide covers the utility modules for data I/O and model serialization in the AYNE project.

## Overview

- **`ayne.utils.io`**: Data I/O operations (CSV, Parquet, Feather)
- **`ayne.ml.models.serialize`**: Model serialization with joblib
- **`ayne.utils.query_utils`**: Database query helpers (see [database.md](../reference/database.md))

## Data I/O (`ayne.utils.io`)

### Philosophy

Parquet is preferred over CSV because it's faster (columnar storage optimized for analytics),
smaller (built-in compression, typically 5-10x smaller than CSV), type-safe (preserves data
types, no string-to-number conversion issues), and stores column types/schema as metadata.

### Core Functions

#### Save DataFrames

```python
from ayne.utils.io import save_dataframe, save_processed_data, save_artifacts

# General-purpose save (specify directory)
save_dataframe(df, "my_data", directory="data/raw", format="parquet")

# Save to processed directory (data/processed/)
save_processed_data(df, "cleaned_movies", format="parquet")

# Save to artifacts directory (data/artifacts/)
save_artifacts(X_train, "X_train", format="parquet")
```

**Supported formats**: `parquet` (default), `csv`, `feather`

#### Load DataFrames

```python
from ayne.utils.io import load_dataframe, load_processed_data, load_artifacts

# General-purpose load (auto-detects format from extension)
df = load_dataframe("data/raw/my_data.parquet")

# Load from processed directory
df = load_processed_data("cleaned_movies.parquet")

# Load from artifacts directory
X_train = load_artifacts("X_train.parquet")
```

### Example: Notebook Workflow

```python
# At the start of your notebook
from ayne.utils.io import (
    load_processed_data,
    save_processed_data,
    load_artifacts,
    save_artifacts,
)

# Load preprocessed data
df = load_processed_data("imputed_data_full.parquet")

# ... perform analysis ...

# Save intermediate results
save_processed_data(df_transformed, "movies_encoded", format="parquet")

# Save train/test splits
save_artifacts(X_train, "X_train", format="parquet")
save_artifacts(y_train, "y_train", format="parquet")
```

## Model Serialization (`ayne.ml.models.serialize`)

### Philosophy

Joblib is used instead of raw pickle for scikit-learn models: it's optimized for numpy
arrays and large models, more stable across Python versions, and supports built-in
compression for faster, smaller save/load than pickle.

### Core Functions

#### Save Models

```python
from ayne.ml.models.serialize import save_model, save_pipeline
from sklearn.ensemble import RandomForestRegressor

model = RandomForestRegressor(n_estimators=100)
model.fit(X_train, y_train)

metadata = {
    "model_type": "RandomForestRegressor",
    "n_features": X_train.shape[1],
    "feature_names": X_train.columns.tolist(),
    "train_score": 0.95,
    "test_score": 0.87,
    "notes": "Best model from grid search",
}

# Saves to data/artifacts/models/
path = save_model(model, "rf_revenue_predictor", metadata=metadata)
# Creates: rf_revenue_predictor.joblib (model)
#          rf_revenue_predictor.json (metadata)
```

**Compression levels**: 0 (none) to 9 (max), default is 3 (good balance).

#### Load Models

```python
from ayne.ml.models.serialize import load_model

# Load model only
model = load_model("data/artifacts/models/rf_revenue_predictor.joblib")

# Load model with metadata
model, metadata = load_model(
    "data/artifacts/models/rf_revenue_predictor.joblib",
    load_metadata=True,
)

print(f"Model type: {metadata['model_class']}")
print(f"Test score: {metadata['test_score']}")
print(f"Features: {metadata['n_features']}")
```

#### Pipelines

```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import GradientBoostingRegressor
from ayne.ml.models.serialize import save_pipeline, load_pipeline

pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("model", GradientBoostingRegressor()),
])
pipe.fit(X_train, y_train)

save_pipeline(pipe, "full_pipeline", metadata={"version": "1.0"})

pipe = load_pipeline("data/artifacts/models/full_pipeline.joblib")
predictions = pipe.predict(X_test)
```

### Utility Functions

```python
from ayne.ml.models.serialize import list_saved_models, get_model_info

# List all saved models
models = list_saved_models()
for model_path in models:
    print(model_path.name)

# Get model information without loading
info = get_model_info("data/artifacts/models/rf_revenue_predictor.joblib")
print(f"File size: {info['file_size_mb']:.2f} MB")
print(f"Modified: {info['modified_at']}")
```

## Best Practices

### File formats

- Parquet for all data storage (processed, features, predictions)
- CSV only when needed for Excel/external tools
- Joblib for all models and pipelines

### Directory structure

```text
data/
├── raw/              # Original data (rarely modified)
├── processed/        # Cleaned, transformed data
├── artifacts/        # Model outputs (features, predictions)
│   └── models/       # Saved models (.joblib + .json)
└── db/               # Database files
```

### Naming conventions

```python
# Data files: descriptive names with version/date
save_processed_data(df, "movies_imputed_v2", format="parquet")

# Model files: model_type + purpose + version/date
save_model(model, "rf_revenue_v1")

# Artifacts: clear names indicating content
save_artifacts(X_train, "X_train_scaled")
```

### Metadata

Always include metadata when saving models:

```python
metadata = {
    "model_type": type(model).__name__,
    "n_features": X_train.shape[1],
    "feature_names": list(X_train.columns),
    "train_score": float(train_score),
    "test_score": float(test_score),
    "best_params": best_params,
    "training_date": datetime.now().isoformat(),
    "notes": "Trained on imputed dataset with pre-split imputation",
}
```

## See Also

- [Database reference](../reference/database.md) — query utilities and schema
- [Data collection workflow](data-collection-workflow.md)

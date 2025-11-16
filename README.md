# 🎬 Are You Not Entertained?

> A comprehensive machine learning pipeline for predicting movie box office success, analyzing audience preferences, and identifying performance trends.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Active%20Development-yellow.svg)

## Overview

**Are You Not Entertained?** is a production-grade machine learning project designed to predict movie box office performance and analyze entertainment data. This project serves as a comprehensive portfolio demonstration of modern ML workflows, data engineering best practices, and production-ready architecture.

### 🎯 Project Goals

- **Predictive Modeling**: Build accurate models to forecast box office success using historical movie data
- **Performance Analysis**: Analyze trends in audience preferences, genre performance, and temporal patterns
- **ML Best Practices**: Implement model versioning, experiment tracking, and performance monitoring
- **Data Quality**: Monitor data drift and ensure robustness of data pipelines
- **Deployment**: Create a web application to visualize predictions and analysis results

## 🚀 Key Features

### Data Pipeline
- **Multi-source Integration**: Fetch data from OMDB, TMDb, and The Numbers
- **Web Scraping**: Collect movie metadata from multiple entertainment databases
- **Data Validation**: Comprehensive data quality checks and imputation strategies
- **Feature Engineering**: Domain-expert feature creation for improved model performance

### Machine Learning
- **XGBoost & Scikit-learn**: State-of-the-art gradient boosting and classical ML models
- **Model Versioning**: MLflow integration for experiment tracking and model registry
- **Performance Monitoring**: Track metrics across model iterations
- **Data Drift Detection**: Identify distribution shifts in production data

### Visualization & Analysis
- **EDA Notebooks**: Exploratory data analysis with Jupyter notebooks
- **Interactive Dashboards**: Matplotlib, Seaborn, and Plotly visualizations
- **Web Interface**: Flask-based web app for model predictions and insights

## 🛠️ Getting Started

### Prerequisites
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- PostgreSQL (for database features)
- API keys for OMDB and TMDb (optional, for data collection)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/JustaKris/Are-You-Not-Entertained.git
   cd Are-You-Not-Entertained
   ```

2. **Create virtual environment and install dependencies with uv**
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e ".[dev,notebooks]"
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and database credentials
   ```

4. **Initialize database**
   ```bash
   python scripts/update_db.py
   ```

### Quick Start

#### Run the data pipeline
```bash
python src/pipeline/pipeline.py
```

#### Train a model
```bash
python src/model/train.py
```

#### Make predictions
```bash
python src/model/predict.py --data data/processed/X_test.csv
```

#### Launch Jupyter Lab
```bash
jupyter lab notebooks/
```

#### Start the web app
```bash
python main.py
```

## 📈 Project Workflow

### 1. Data Collection
- Integrate with OMDB, TMDb, and The Numbers APIs
- Fetch movie metadata, box office data, and audience ratings
- Store raw data in `data/raw/`

### 2. Data Preprocessing
- Handle missing values using advanced imputation strategies
- Remove duplicates and outliers
- Normalize and scale features
- Save processed data in `data/processed/`

### 3. Exploratory Data Analysis
- Analyze trends across genres, ratings, release dates
- Identify feature correlations and distributions
- Generate insights in `notebooks/02_movies_EDA.ipynb`

### 4. Feature Engineering
- Create derived features (e.g., director popularity, actor prestige)
- Temporal features (season, day of week, holiday proximity)
- Interaction features for improved model performance

### 5. Model Development
- Train multiple models (XGBoost, Random Forest, etc.)
- Hyperparameter tuning with cross-validation
- Track experiments with MLflow
- Evaluate on holdout test set

### 6. Model Deployment
- Version final model with MLflow Model Registry
- Deploy via Flask web application
- Monitor predictions and data drift in production

### 7. Monitoring & Maintenance
- Track key performance metrics over time
- Detect data drift and model degradation
- Retrain models as needed with new data

## 🔄 ML Best Practices Implemented

✅ **Experiment Tracking**: MLflow for reproducible experiments  
✅ **Model Versioning**: Serialization and registry management  
✅ **Data Drift Monitoring**: Detect distribution shifts in production  
✅ **Cross-validation**: Robust model evaluation  
✅ **Train/Test Split**: Proper data separation  
✅ **Hyperparameter Tuning**: Grid search and optimization  
✅ **Feature Scaling**: Normalized inputs for ML models  
✅ **Code Quality**: Black, isort, flake8 compliance  

## 📦 Dependency Groups

Install specific feature sets with uv:

```bash
# Development tools
uv pip install -e ".[dev]"

# Jupyter notebooks
uv pip install -e ".[notebooks]"

# Documentation generation
uv pip install -e ".[docs]"

# Web app deployment
uv pip install -e ".[web]"

# All groups
uv pip install -e ".[dev,notebooks,docs,web]"
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_pipeline.py

# Run tests matching pattern
pytest -k "preprocessing"
```

## 📚 Documentation

Generate documentation with MkDocs:
```bash
mkdocs serve
```

Explore detailed analysis in Jupyter notebooks:
- `notebooks/01_movies_data_full_imputation.ipynb` - Data cleaning
- `notebooks/02_movies_EDA.ipynb` - Exploratory analysis
- `notebooks/03_movies_data_modeling_prep.ipynb` - Feature engineering
- `notebooks/04_movies_predictive_modeling.ipynb` - Model training & evaluation

## 🌐 Web Application

The Flask web app provides:
- **Real-time Predictions**: Input movie features and get box office forecast
- **Performance Dashboard**: Visualize historical predictions vs actual results
- **Data Insights**: Interactive exploration of movie trends and patterns
- **Model Comparison**: Side-by-side analysis of different model versions

```bash
python main.py
# Navigate to http://localhost:5000
```

## 📊 Performance Metrics

Monitor the following KPIs:
- **RMSE**: Root Mean Squared Error for predictions
- **MAE**: Mean Absolute Error
- **R² Score**: Model explanation ratio
- **Data Drift**: Statistical tests for distribution changes
- **Model Latency**: Inference time in production

## 🔑 API Keys Required

To use all features, obtain free API keys from:
- [OMDB](https://www.omdbapi.com/) - Movie database API
- [TMDb](https://www.themoviedb.org/settings/api) - The Movie Database API

## 🤝 Contributing

This is a personal portfolio project. Feel free to fork and adapt for your own learning!

## 📝 License

MIT License - see `LICENSE` file for details

## 🎓 Learning Outcomes

This project demonstrates proficiency in:
- ✨ End-to-end machine learning pipeline development
- ✨ Production-grade Python code and best practices
- ✨ Data engineering and API integration
- ✨ Model versioning and experiment tracking
- ✨ Web application development with Flask
- ✨ Data quality and monitoring
- ✨ Collaborative development workflows (Git, documentation)

## 📞 Contact

Questions or suggestions? Open an issue or reach out!

---

**Last Updated**: November 2025 | **Status**: 🚀 Active Development

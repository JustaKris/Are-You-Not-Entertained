import pandas as pd
from verstack import NaNImputer


# Define a function to add missing indicators for certain columns.
def impute_data(df: pd.DataFrame, colums_to_exclude: list = None) -> pd.DataFrame:
    if colums_to_exclude:
        df = df.drop(columns=colums_to_exclude).copy()
    else:
        df.copy()
    imputer = NaNImputer()
    return imputer.impute(df)


# Some columns need to get converted to numeric
def convert_to_numeric(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.columns:
        # Convert to string, remove commas, then convert to numeric
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
    return df


# Define a function to add missing indicators for certain columns.
def add_missing_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.columns:
        df[col + "_missing"] = df[col].isnull().astype(int)
    return df


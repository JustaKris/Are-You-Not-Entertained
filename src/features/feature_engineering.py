import re
import pandas as pd


def extract_awards_info(awards_str):
    """
    Extracts numerical awards information from a text string.

    Parameters
    ----------
    awards_str : str
        The awards description string.

    Returns
    -------
    pd.Series
        A Series with the following index:
        ["total_wins", "total_noms", "oscar_wins", "oscar_noms", "bafta_wins", "bafta_noms"]
    """
    # Handle missing or "N/A" values.
    if pd.isna(awards_str) or awards_str.strip() in ["N/A", ""]:
        return pd.Series([0, 0, 0, 0, 0, 0],
                         index=["total_wins", "total_noms", "oscar_wins", "oscar_noms", "bafta_wins", "bafta_noms"])
    
    # Extract overall totals.
    # Look for a pattern like "56 wins" (we use negative lookahead to avoid picking up Oscar wins)
    total_wins_match = re.search(r'(\d+)\s+wins?(?!.*Oscars)', awards_str, flags=re.IGNORECASE)
    total_noms_match = re.search(r'(\d+)\s+nominations', awards_str, flags=re.IGNORECASE)
    total_wins = int(total_wins_match.group(1)) if total_wins_match else 0
    total_noms = int(total_noms_match.group(1)) if total_noms_match else 0

    # Oscar-specific extraction:
    oscar_noms_match = re.search(r'Nominated for\s+(\d+)\s+Oscars?', awards_str, flags=re.IGNORECASE)
    oscar_noms = int(oscar_noms_match.group(1)) if oscar_noms_match else 0
    # Look for something like "Oscars. 56 wins" or "Oscars 56 wins" (using non-digit separator)
    oscar_wins_match = re.search(r'Oscars?[\W_]+(\d+)\s+wins?', awards_str, flags=re.IGNORECASE)
    oscar_wins = int(oscar_wins_match.group(1)) if oscar_wins_match else 0

    # BAFTA-specific extraction:
    # For nominations, sometimes the text might run together (e.g. "BAFTA Award28 nominations total")
    bafta_noms_match = re.search(r'Nominated for\s+(\d+)\s*BAFTA', awards_str, flags=re.IGNORECASE)
    bafta_noms = int(bafta_noms_match.group(1)) if bafta_noms_match else 0
    # For wins, allow an optional "Award" word after BAFTA.
    bafta_wins_match = re.search(r'BAFTA(?:\s+Award)?[\D_]+(\d+)\s+wins?', awards_str, flags=re.IGNORECASE)
    bafta_wins = int(bafta_wins_match.group(1)) if bafta_wins_match else 0

    return pd.Series([total_wins, total_noms, oscar_wins, oscar_noms, bafta_wins, bafta_noms],
                     index=["total_wins", "total_noms", "oscar_wins", "oscar_noms", "bafta_wins", "bafta_noms"])


def transform_awards(X):
    """
    Expects X to be a DataFrame with a single column (e.g., 'awards').
    Applies extract_awards_info row-wise and returns a DataFrame.
    """
    # Apply the function to the first (and only) column
    return X.iloc[:, 0].apply(extract_awards_info)


def transform_top_categories(X, column, top_n, delimiter=",", others_label="Others"):
    """
    Transforms a multi-label column by keeping only the top_n categories (based on frequency)
    and replacing all other categories with a generic label.
    
    Parameters:
        X (pd.DataFrame): Input DataFrame.
        column (str): The name of the multi-label column to process.
        top_n (int): Number of top categories to keep.
        delimiter (str): Delimiter separating the values.
        others_label (str): Label to assign to categories not among the top_n.
    
    Returns:
        pd.DataFrame: A DataFrame with one column (the processed column).
    """
    X = X.copy()
    # Split the column values, explode, and count frequencies.
    exploded = X[column].dropna().str.split(rf"{delimiter}\s*").explode().str.strip()
    counts = exploded.value_counts()
    top_categories = counts.head(top_n).index.tolist()
    
    def map_categories(cell):
        if pd.isna(cell):
            return cell
        # Split and strip each value.
        cats = [cat.strip() for cat in cell.split(delimiter)]
        # Replace values not in top_categories with others_label.
        new_cats = [cat if cat in top_categories else others_label for cat in cats]
        # Remove duplicates while preserving order.
        seen = set()
        new_cats = [x for x in new_cats if x not in seen and not seen.add(x)]
        return delimiter.join(new_cats)
    
    X[column] = X[column].apply(map_categories)
    # Return a DataFrame with just the transformed column.
    return X[[column]]

# Now, to create a FunctionTransformer for, say, the 'production_country_name' column with top_n=5:
transformer_prod_country = FunctionTransformer(
    func=partial(transform_top_categories, column="production_country_name", top_n=5, delimiter=",", others_label="Others"),
    validate=False
)

# Similarly, for 'spoken_languages' column with top_n=5:
transformer_spoken_lang = FunctionTransformer(
    func=partial(transform_top_categories, column="spoken_languages", top_n=5, delimiter=",", others_label="Others"),
    validate=False
)


def add_date_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['release_date'] = pd.to_datetime(df['release_date'])
    df['release_year'] = df['release_date'].dt.year
    df['release_month'] = df['release_date'].dt.month
    df['release_day'] = df['release_date'].dt.day
    df['is_weekend'] = (df['release_date'].dt.weekday >= 4).astype(int)
    df['is_holiday_season'] = df['release_month'].isin([6, 7, 11, 12]).astype(int)
    df['movie_age'] = 2025 - df['release_year']
    return df


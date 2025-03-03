import os
import dill
import pandas as pd
from typing import Optional, List, Dict, Union


# Function to save data to CSV
def save_to_csv(data, filename, directory=".\data"):
    """
    Saves data to a CSV file.
    
    Args:
        data (List[dict]): The data to save.
        filename (str): The name of the CSV file.
        directory (str, optional): The directory to save the file in. Defaults to "./data".
    """
    # Ensure directory exists
    os.makedirs(directory, exist_ok=True)
    
    # Construct full file path
    file_path = os.path.join(directory, filename)

    # If data is a dict (i.e., not a list), wrap it in a list
    if not isinstance(data, list):
        data = [data]
    
    # Convert to DataFrame and save
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False, sep=";")
    print(f"Data saved to {file_path}")


# New helper function: append_to_csv
def store_to_csv(data: Union[List[Dict], Dict], filename: str, directory: str, key_column: str = "IMDBID") -> None:
    """
    Creates a CSV file if it does not exist, or appends new rows to it.
    If the file exists, only rows whose value in key_column is not already present are added.
    
    Args:
        data (Union[List[Dict], Dict]): Data to save.
        filename (str): Name of the CSV file.
        directory (str): Directory where the CSV file is stored.
        key_column (str): The column name used to check for duplicates.
    
    Returns:
        None
    """
    os.makedirs(directory, exist_ok=True)
    file_path = os.path.join(directory, filename)
    
    # Ensure data is a list of dictionaries.
    if not isinstance(data, list):
        data = [data]
    new_df = pd.DataFrame(data)
    
    # If file exists, load existing IDs and filter out rows with duplicate key values.
    if os.path.exists(file_path):
        try:
            existing_df = pd.read_csv(file_path, usecols=[key_column])
            existing_ids = set(existing_df[key_column].dropna().astype(str).tolist())
        except Exception as e:
            print(f"Warning: Could not read existing file columns: {e}")
            existing_ids = set()
        new_df = new_df[~new_df[key_column].astype(str).isin(existing_ids)]
    
    # If there's no new data to append, exit early.
    if new_df.empty:
        print("No new data to append.")
        return
    
    # Append (or create) the CSV file.
    if os.path.exists(file_path):
        new_df.to_csv(file_path, mode='a', header=False, index=False, sep=";")
    else:
        new_df.to_csv(file_path, index=False, sep=";")
    print(f"Appended {len(new_df)} new rows to {file_path}")


# Load data from csv
def load_csv(filename, directory="./data/tmdb"):
    """
    Loads data from a CSV file with a semicolon separator.
    
    Args:
        filename (str): The name of the CSV file.
        directory (str, optional): The directory where the CSV file is located.
                                   Defaults to "./data".
    
    Returns:
        pd.DataFrame: The loaded data as a pandas DataFrame, or None if an error occurs.
    """
    file_path = os.path.join(directory, filename)
    
    try:
        df = pd.read_csv(file_path, sep=';')
        print(f"Data loaded successfully from {file_path}")
        return df
    except Exception as e:
        print(f"Error loading data from {file_path}: {e}")
        return None
    

def save_dataframe(df, filename="file.csv", directory="./data", sep=",", index=False):
    """
    Saves a Pandas dataframe to a CSV file.

    Parameters:
    df (pd.DataFrame): Dataset to save.
    filename (str): The name of the output CSV file (default: 'file.csv').
    directory (str): The folder where the file should be saved (default: '../data').
    sep (str): The separator for the CSV file (default: ',').
    index (bool): Whether to include the index in the saved file (default: False).
    
    Returns:
    None
    """
    try:
        # Ensure the directory exists
        os.makedirs(directory, exist_ok=True)

        # Full file path
        filepath = os.path.join(directory, filename)

        # Save DataFrame
        df.to_csv(filepath, sep=sep, index=index)
        print(f"✅ Data successfully saved to {filepath} with separator '{sep}'")
    
    except Exception as e:
        print(f"❌ Error saving file: {e}")


def save_model(model, file_name):
    """
    Save .pkl file
    """
    dir = '..\models'
    path = os.path.join(dir, file_name)
    os.makedirs(dir, exist_ok=True)

    with open(path, "wb") as file_obj:
        dill.dump(model, file_obj)
        
    print(f'File "{file_name}" saved to <./{dir}>')


def load_model(file_name):
    """
    Load .pkl file
    """
    dir = '..\models'
    path = os.path.join(dir, file_name)
    with open(path, 'rb') as file:
        model = dill.load(file)
        
    print(f'File "{file_name}" loaded')
    
    return model
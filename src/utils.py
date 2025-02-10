import os
import pandas as pd


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
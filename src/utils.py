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
    
    # Convert to DataFrame and save
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)
    print(f"Data saved to {file_path}")
import yaml
import os

def load_config(var: str, config_file: str='config/config.yaml', default=None):
    """
    Load a specified variable from a YAML configuration file.
    
    :param var: The configuration key to fetch.
    :param config_file: Path to the YAML configuration file.
    :param default: The default value to return if the key is not found. Defaults to None.
    :return: The value associated with `var` or `default` if not found.
    """
    # Check if the config file exists
    if not os.path.exists(config_file):
        print(f"Error: {config_file} not found.")
        return default

    try:
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
            if config is None:
                print("Error: Config file is empty.")
                return default
            return config.get(var, default)

    except yaml.YAMLError as e:
        print(f"Error loading YAML file: {e}")
        return default


# Testing functionality
if __name__ == "__main__":
    tmdb_api_key = load_config("TMDB_API_KEY")
    print(tmdb_api_key)

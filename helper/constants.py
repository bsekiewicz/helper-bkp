import importlib.resources
import json
import os


def load_cs(dir_path):
    """
    Loads all JSON and TXT files from a given directory and returns a mapping of file names to their paths.

    This function scans the specified directory for files with .json or .txt extensions,
    creates a dictionary where the keys are the uppercase file names (without extensions),
    and the values are the full file paths.

    Parameters:
    dir_path (str): Path to the directory containing configuration files.
                    If empty or non-existent, an empty dictionary will be returned.

    Returns:
    dict: A dictionary mapping file names (without extensions, in uppercase) to their full paths.
          For example: {'CONFIG': '/path/to/config.json', 'DATA': '/path/to/data.txt'}
          Returns an empty dictionary if the directory is empty or doesn't exist.
    """
    cs_dict = {}
    if dir_path and os.path.exists(dir_path):
        for file in os.listdir(dir_path):
            if file.endswith((".json", ".txt")):
                key_name = file.rsplit(".", 1)[0].upper()
                cs_dict[key_name] = os.path.join(dir_path, file)
    return cs_dict


CS = load_cs(os.getenv("PATH_KEYS_CONNECTIONS_STRINGS", ""))


def load_mapping(filename):
    """
    Load a JSON mapping file from the data/mappings directory inside the package.

    This function attempts to open and read a JSON file from the specified location
    within the package. If the file is found, it is parsed and returned as a dictionary.
    If the file is not found, a warning is printed and an empty dictionary is returned.

    Parameters:
    filename (str): The name of the JSON file to be loaded from the data/mappings directory.

    Returns:
    dict: A dictionary containing the mapping data from the JSON file.
          Returns an empty dictionary if the file is not found.

    Raises:
    json.JSONDecodeError: If the file contains invalid JSON data.
    """
    try:
        with importlib.resources.files("helper.data.mappings").joinpath(filename).open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️ Warning: {filename} not found in package data")
        return {}


MAPPING_CURRENCIES = load_mapping("mapping_currencies.json")
MAPPING_LANGUAGES = load_mapping("mapping_languages.json")
MAPPING_COUNTRIES = load_mapping("mapping_countries.json")

MAPPING_CURRENCIES_SYMBOLS = {}
for currency_code, details in MAPPING_CURRENCIES.items():
    for symbol in details.get("symbols", []):
        MAPPING_CURRENCIES_SYMBOLS[symbol] = details["iso3"]

"""
A set of utility functions.

It contains primarily for string manipulation, datetime operations,
and data transformations between different formats and structures.
It includes functions for converting camelCase to snake_case, transforming dictionary keys,
processing lists of dictionaries, and formatting datetime objects for compatibility with
BigQuery and Firestore.

Functions:
    camel_to_snake(name: str) -> str:
        Converts a camelCase string to snake_case.

    transform_keys(obj: Union[dict, list]) -> Union[dict, list]:
        Recursively transforms the keys of dictionaries (and lists of dictionaries) to snake_case.

    process_list_of_dict_keys_to_snake_case(data: list) -> list:
        Processes a list of dictionaries, converting all keys to snake_case.

    get_current_utc_timestamp() -> str:
        Returns the current UTC timestamp as a formatted string.

    prepare_ranked_progression_item(firestore_object: dict) -> dict:
        Extracts specific keys from a Firestore object and prepares it with additional data.

    format_to_bigquery_dt(dt_with_ns: Any) -> str:
        Converts various datetime formats to a string format compatible with BigQuery.

    format_to_firestore_dt(timestamp_input: Any) -> datetime:
        Converts a timestamp (in various formats) to a datetime object suitable for Firestore.

    recursive_fix_time_format(data: dict, mode: str, timestamp_columns: list) -> dict:
        Recursively formats datetime values in a dictionary according to the specified mode
        ('bigquery' or 'firestore') for specified columns.
"""

import re
from datetime import datetime


def camel_to_snake(name):
    """Convert camelCase to snake_case."""
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def transform_keys(obj):
    """Recursively transform dictionary keys."""
    if isinstance(obj, list):
        return [transform_keys(item) for item in obj]
    elif isinstance(obj, dict):
        return {
            camel_to_snake(key): transform_keys(value) for key, value in obj.items()
        }
    return obj


def process_list_of_dict_keys_to_snake_case(data):
    """Process a list of dictionaries and transform all keys to snake_case."""
    return [transform_keys(item) for item in data]


def get_current_utc_timestamp():
    """Get the current UTC timestamp with seconds."""
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")


def prepare_ranked_progression_item(firestore_object):
    """
    Ranked progression item from a given Firestore object is prepared.

    This function extracts specific keys related to ranked progression from a Firestore object,
    adds a current UTC timestamp, and then removes these keys from the original Firestore object.
    The keys extracted include details like queue type, tier, rank, wins, losses, and others.
    The function is designed to handle any exceptions by returning None in case of an error.

    Args:
        firestore_object (dict): A dictionary representing a Firestore object, typically containing
                                 ranked progression information.

    Returns:
        dict: A dictionary with selected ranked progression information and a timestamp.
              If an exception occurs, returns None.

    Note:
        The function modifies the input firestore_object by removing the extracted keys,
        except for 'seasonMeta' and 'regionMeta'.
    """
    try:
        # List of keys to extract
        keys_to_extract = [
            "queueType",
            "tier",
            "rank",
            "losses",
            "wins",
            "leaguePoints",
            "hotStreak",
            "seasonMeta",
            "regionMeta",
            "leagueId",
        ]

        # Use dictionary comprehension to extract items
        ranked_progression_item = {
            key: firestore_object[key] for key in keys_to_extract
        }

        # Rename specific keys if necessary
        ranked_progression_item["progressionTimestamp"] = get_current_utc_timestamp()

        # Delete extracted keys from the original dictionary in bulk
        for key in keys_to_extract:
            if key not in ("seasonMeta", "regionMeta"):
                del firestore_object[key]

        return ranked_progression_item
    except Exception:
        return None


def format_to_bigquery_dt(dt_with_ns):
    """Convert DateTimeWithNanoSeconds from Firestore to formatted string for BigQuery."""
    if hasattr(dt_with_ns, "seconds") and hasattr(dt_with_ns, "nanoseconds"):
        dt_object = datetime.utcfromtimestamp(
            dt_with_ns.seconds + dt_with_ns.nanoseconds / 1e9
        )
        return dt_object.strftime("%Y-%m-%d %H:%M:%S.%f")

    elif isinstance(dt_with_ns, datetime):  # If it's already a datetime object
        return dt_with_ns.strftime("%Y-%m-%d %H:%M:%S.%f")

    elif isinstance(dt_with_ns, int):  # If it's a UNIX timestamp
        if dt_with_ns > 10**12:  # Likely in milliseconds
            dt_with_ns /= 1000
        dt_object = datetime.utcfromtimestamp(dt_with_ns)
        return dt_object.strftime("%Y-%m-%d %H:%M:%S.%f")

    return dt_with_ns  # If it's neither, return it as is


def format_to_firestore_dt(timestamp_input):
    """Convert BigQuery formatted string to datetime for Firestore."""
    # If it's already a datetime object
    if isinstance(timestamp_input, datetime):
        return timestamp_input

    # If it's a string
    elif isinstance(timestamp_input, str):
        return datetime.strptime(timestamp_input, "%Y-%m-%d %H:%M:%S.%f")

    elif isinstance(timestamp_input, int):
        if timestamp_input > 10**12:  # Likely in milliseconds
            timestamp_input /= 1000
        return datetime.utcfromtimestamp(timestamp_input)

    # If it's neither
    return timestamp_input


def recursive_fix_time_format(data, mode, timestamp_columns):
    """
    Recursively formats datetime values in a dictionary according to the specified mode.

    This function traverses through a dictionary, and for each key that matches the provided
    list of timestamp columns, it converts the corresponding value to a datetime format
    suitable for either BigQuery or Firestore, based on the specified mode. The function
    applies these transformations recursively to nested dictionaries.

    Args:
        data (dict): The dictionary containing data with datetime values to be formatted.
        mode (str): The mode of datetime formatting. Accepts 'bigquery' or 'firestore'.
                    'bigquery' mode formats the datetime for BigQuery compatibility,
                    whereas 'firestore' mode formats it for Firestore compatibility.
        timestamp_columns (list): A list of keys in the dictionary whose values are
                                  datetime objects to be formatted.

    Returns:
        dict: The dictionary with datetime values formatted as per the specified mode.

    Note:
        This function modifies the input dictionary 'data' directly. Ensure to pass a
        copy of the dictionary if the original data should not be altered.
    """
    for key, value in data.items():
        if key in timestamp_columns:
            if mode == "bigquery":
                data[key] = format_to_bigquery_dt(value)
            elif mode == "firestore":
                data[key] = format_to_firestore_dt(value)
        elif isinstance(value, dict):
            data[key] = recursive_fix_time_format(value, mode, timestamp_columns)
    return data

import pandas as pd
import numpy as np
import logging
from src.error_handling import handle_error

logger = logging.getLogger(__name__)

def parse_raw_data(raw_data: bytes) -> dict | None:
    """
    Parses raw byte data into a dictionary representing a single data point.
    Assumes raw_data is a comma-separated string of latitude, longitude, Bx, By, Bz.
    Example: b"34.05,-118.25,25000,1000,40000"

    Args:
        raw_data (bytes): Raw byte data received from the sensor.

    Returns:
        dict | None: A dictionary {'latitude', 'longitude', 'Bx', 'By', 'Bz'} if parsing is successful,
                     None otherwise.
    """
    try:
        data_str = raw_data.decode('utf-8').strip()
        parts = data_str.split(',')

        if len(parts) != 5:
            logger.warning(f"Malformed raw data (incorrect number of parts): {data_str}")
            return None

        data_point = {
            'latitude': float(parts[0]),
            'longitude': float(parts[1]),
            'Bx': float(parts[2]),
            'By': float(parts[3]),
            'Bz': float(parts[4])
        }
        return data_point
    except UnicodeDecodeError as e:
        handle_error(e, f"Failed to decode raw data: {raw_data}. Error: {e}")
        return None
    except ValueError as e:
        handle_error(e, f"Failed to convert raw data parts to numeric types: {raw_data}. Error: {e}")
        return None
    except Exception as e:
        handle_error(e, f"An unexpected error occurred during raw data parsing: {raw_data}. Error: {e}")
        return None

def validate_realtime_point(data_point: dict) -> tuple[bool, list[str]]:
    """
    Performs quick validation on a single real-time data point (e.g., numeric types, basic range checks).
    This function provides lightweight, direct validation for dictionary-based single points,
    optimized for real-time performance. While its logic is similar to aspects of `src/data_validation.py`
    (COMP-002), it avoids the overhead of converting single points to pandas DataFrames for validation,
    which would be inefficient for individual real-time data streams.

    Args:
        data_point (dict): A dictionary representing a single data point
                           (e.g., {'latitude': ..., 'longitude': ..., 'Bx': ..., 'By': ..., 'Bz': ...}).

    Returns:
        tuple[bool, list[str]]: A tuple where the first element is True if the
                                 data point is valid, False otherwise. The second
                                 element is a list of error messages.
    """
    errors = []
    is_valid = True

    required_keys = ['latitude', 'longitude', 'Bx', 'By', 'Bz']

    # 1. Check for required keys and numeric types
    for key in required_keys:
        if key not in data_point:
            errors.append(f"Missing required key: '{key}'.")
            is_valid = False
        elif not isinstance(data_point[key], (int, float, np.integer, np.floating)):
            errors.append(f"Key '{key}' is not numeric.")
            is_valid = False

    if not is_valid: # If required keys or types are missing, further checks might fail or be meaningless
        return is_valid, errors

    # 2. Check coordinate bounds
    latitude = data_point['latitude']
    longitude = data_point['longitude']

    if not (-90 <= latitude <= 90):
        errors.append("Latitude value is out of bounds (-90 to 90 degrees).")
        is_valid = False

    if not (-180 <= longitude <= 180):
        errors.append("Longitude value is out of bounds (-180 to 180 degrees).")
        is_valid = False

    # No specific range checks for Bx, By, Bz beyond being numeric, as their ranges can vary widely.

    return is_valid, errors

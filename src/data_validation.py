import pandas as pd
# import numpy as np # CQ-002: Removed unused import

def validate_data(dataframe: pd.DataFrame) -> tuple[bool, list[str]]:
    """
    Validates the input DataFrame for common issues like missing values,
    out-of-bounds coordinates, and required column existence.

    Args:
        dataframe (pandas.DataFrame): The DataFrame to validate.

    Returns:
        tuple[bool, list[str]]: A tuple where the first element is True if the
                                 DataFrame is valid, False otherwise. The second
                                 element is a list of error messages.
    """
    errors = []
    is_valid = True

    required_columns = ['latitude', 'longitude', 'Bx', 'By', 'Bz'] # Assuming these are the critical columns for magnetic field data

    # 1. Check for required columns
    for col in required_columns:
        if col not in dataframe.columns:
            errors.append(f"Missing required column: '{col}'.")
            is_valid = False

    if not is_valid: # If required columns are missing, further checks might fail or be meaningless
        return is_valid, errors

    # 2. Check for missing values in critical columns
    for col in required_columns:
        if dataframe[col].isnull().any():
            errors.append(f"Column '{col}' contains missing values.")
            is_valid = False

    # 3. Check coordinate bounds (assuming 'latitude' and 'longitude' are present and numeric)
    if 'latitude' in dataframe.columns and pd.api.types.is_numeric_dtype(dataframe['latitude']):
        if not ((dataframe['latitude'] >= -90) & (dataframe['latitude'] <= 90)).all():
            errors.append("Latitude values are out of bounds (-90 to 90 degrees).")
            is_valid = False
    elif 'latitude' in dataframe.columns:
        errors.append("Latitude column is not numeric.")
        is_valid = False

    if 'longitude' in dataframe.columns and pd.api.types.is_numeric_dtype(dataframe['longitude']):
        # Normalize longitude from [0, 360] to [-180, 180]
        dataframe['longitude'] = dataframe['longitude'].apply(lambda lon: lon - 360 if lon > 180 else lon)
        if not ((dataframe['longitude'] >= -180) & (dataframe['longitude'] <= 180)).all():
            errors.append("Longitude values are out of bounds (-180 to 180 degrees).")
            is_valid = False
    elif 'longitude' in dataframe.columns:
        errors.append("Longitude column is not numeric.")
        is_valid = False

    # 4. Check if Bx, By, Bz are numeric
    for col in ['Bx', 'By', 'Bz']:
        if col in dataframe.columns and not pd.api.types.is_numeric_dtype(dataframe[col]):
            errors.append(f"Magnetic field component '{col}' is not numeric.")
            is_valid = False

    return is_valid, errors

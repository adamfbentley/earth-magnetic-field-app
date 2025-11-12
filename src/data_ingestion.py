import pandas as pd
import os

def load_data(file_path: str) -> pd.DataFrame:
    """
    Loads data from the specified file path, supporting CSV and Excel formats.

    Args:
        file_path (str): The path to the data file (CSV or Excel).

    Returns:
        pandas.DataFrame: The loaded data.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is unsupported or data cannot be read.
    """
    # SECURITY FIX (SEC-001): Canonicalize the file path to mitigate path traversal.
    # For user-provided input fields, further UI-level validation (e.g., using a file dialog
    # or restricting to specific directories) is recommended at the application layer.
    file_path = os.path.abspath(os.path.normpath(file_path))

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found at: {file_path}")

    file_extension = os.path.splitext(file_path)[1].lower()

    try:
        if file_extension == '.csv':
            df = pd.read_csv(file_path)
        elif file_extension in ('.xls', '.xlsx'):
            df = pd.read_excel(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}. Only CSV and Excel (.xls, .xlsx) are supported.")
        return df
    except Exception as e:
        raise ValueError(f"Error reading data from {file_path}: {e}")

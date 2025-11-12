import pandas as pd
import numpy as np
import os

def export_magnetic_field_data(dataframe: pd.DataFrame, modeled_bx: np.ndarray, modeled_by: np.ndarray, modeled_bz: np.ndarray, output_file_path: str) -> None:
    """
    Exports the raw and modeled magnetic field data to a CSV file.

    Args:
        dataframe (pd.DataFrame): The original input DataFrame containing raw data.
        modeled_bx (np.ndarray): Array of reconstructed Bx (North) components.
        modeled_by (np.ndarray): Array of reconstructed By (East) components.
        modeled_bz (np.ndarray): Array of reconstructed Bz (Down) components.
        output_file_path (str): The full path to the output CSV file.

    Raises:
        ValueError: If input arrays have incompatible dimensions.
        IOError: If there is an error writing the file.
    """
    if not all(len(arr) == len(dataframe) for arr in [modeled_bx, modeled_by, modeled_bz]):
        raise ValueError("Modeled field component arrays must have the same length as the input DataFrame.")

    # Create a copy of the original DataFrame to avoid modifying it directly
    export_df = dataframe.copy()

    # Add modeled components to the DataFrame
    export_df['Bx_modeled'] = modeled_bx
    export_df['By_modeled'] = modeled_by
    export_df['Bz_modeled'] = modeled_bz

    # Rename original components for clarity if they exist
    if 'Bx' in export_df.columns:
        export_df.rename(columns={'Bx': 'Bx_observed'}, inplace=True)
    if 'By' in export_df.columns:
        export_df.rename(columns={'By': 'By_observed'}, inplace=True)
    if 'Bz' in export_df.columns:
        export_df.rename(columns={'Bz': 'Bz_observed'}, inplace=True)

    # Ensure the directory exists
    output_dir = os.path.dirname(output_file_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    try:
        export_df.to_csv(output_file_path, index=False)
    except Exception as e:
        raise IOError(f"Failed to write data to {output_file_path}: {e}") from e

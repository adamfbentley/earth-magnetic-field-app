import pytest
import sys
import os

# Add the parent directory of src to sys.path to allow imports like 'from src.spherical_harmonics import ...'
# This is crucial if tests are run from a different directory (e.g., project root)
# Ensure 'src' is importable as a package
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import modules to be tested
from src.spherical_harmonics import compute_basis_functions, reconstruct_field
from src.gauss_fitter import fit_coefficients
from src.data_validation import validate_data
from src.data_ingestion import load_data

import numpy as np
import pandas as pd

# --- Test Data Setup ---
# A simple, consistent dataset for testing
TEST_LATITUDE = np.array([0.0, 30.0, -45.0])
TEST_LONGITUDE = np.array([0.0, 15.0, 90.0])
TEST_OBSERVED_BX = np.array([20000.0, 18000.0, 22000.0])
TEST_OBSERVED_BY = np.array([0.0, 1000.0, -500.0])
TEST_OBSERVED_BZ = np.array([40000.0, 35000.0, 42000.0])
TEST_OBSERVED_FIELD_COMPONENTS_1D = np.concatenate((TEST_OBSERVED_BX, TEST_OBSERVED_BY, TEST_OBSERVED_BZ))
TEST_OBSERVED_FIELD_COMPONENTS_2D = np.stack((TEST_OBSERVED_BX, TEST_OBSERVED_BY, TEST_OBSERVED_BZ), axis=1)

# A simple DataFrame for data_ingestion/validation
TEST_DF_VALID = pd.DataFrame({
    'latitude': TEST_LATITUDE,
    'longitude': TEST_LONGITUDE,
    'Bx': TEST_OBSERVED_BX,
    'By': TEST_OBSERVED_BY,
    'Bz': TEST_OBSERVED_BZ
})

# --- Unit Tests for Spherical Harmonics Engine (COMP-003) ---

def test_compute_basis_functions_degree_1():
    """Test compute_basis_functions for degree 1."""
    degree = 1
    design_matrix = compute_basis_functions(TEST_LATITUDE, TEST_LONGITUDE, degree)
    # For degree 1, there are 3 coefficients (g_1^0, g_1^1, h_1^1)
    # Number of rows = num_points * 3 (Bx, By, Bz)
    assert design_matrix.shape == (len(TEST_LATITUDE) * 3, 3)
    assert not np.all(design_matrix == 0) # Should not be all zeros

def test_compute_basis_functions_degree_2():
    """Test compute_basis_functions for degree 2."""
    degree = 2
    design_matrix = compute_basis_functions(TEST_LATITUDE, TEST_LONGITUDE, degree)
    # For degree 2, coefficients are:
    # l=1: g_1^0, g_1^1, h_1^1 (3)
    # l=2: g_2^0, g_2^1, h_2^1, g_2^2, h_2^2 (5)
    # Total = 3 + 5 = 8 coefficients
    assert design_matrix.shape == (len(TEST_LATITUDE) * 3, 8)
    assert not np.all(design_matrix == 0)

def test_compute_basis_functions_invalid_degree():
    """Test compute_basis_functions with invalid degree."""
    with pytest.raises(ValueError, match="Spherical harmonic degree must be at least 1"):
        compute_basis_functions(TEST_LATITUDE, TEST_LONGITUDE, 0)

def test_reconstruct_field_basic():
    """Test reconstruct_field with simple coefficients."""
    degree = 1
    # Example coefficients (not physically accurate, just for structural test)
    # g_1^0, g_1^1, h_1^1
    coefficients = np.array([30000.0, 5000.0, 1000.0])
    
    Bx, By, Bz = reconstruct_field(TEST_LATITUDE, TEST_LONGITUDE, coefficients, degree)
    
    assert Bx.shape == TEST_LATITUDE.shape
    assert By.shape == TEST_LATITUDE.shape
    assert Bz.shape == TEST_LATITUDE.shape
    assert not np.all(Bx == 0) # Should produce some field
    assert not np.all(By == 0)
    assert not np.all(Bz == 0)

def test_reconstruct_field_coefficient_mismatch():
    """Test reconstruct_field with incorrect number of coefficients."""
    degree = 1
    coefficients = np.array([1.0, 2.0]) # Expected 3 for degree 1
    with pytest.raises(ValueError, match="Number of provided coefficients"):
        reconstruct_field(TEST_LATITUDE, TEST_LONGITUDE, coefficients, degree)

def test_reconstruct_field_invalid_degree():
    """Test reconstruct_field with invalid degree."""
    coefficients = np.array([]) # Empty for degree 0
    with pytest.raises(ValueError, match="Spherical harmonic degree must be at least 1"):
        reconstruct_field(TEST_LATITUDE, TEST_LONGITUDE, coefficients, 0)

# --- Unit Tests for Gauss Coefficient Fitter (COMP-004) ---

def test_fit_coefficients_simple_linear():
    """Test fit_coefficients with a simple linear regression problem."""
    # y = 2x + 1
    x = np.array([1, 2, 3, 4, 5])
    y = 2 * x + 1 + np.random.normal(0, 0.1, size=x.shape) # Add some noise
    
    design_matrix = np.column_stack([x, np.ones_like(x)]) # [x, 1] for slope and intercept
    
    coeffs, uncertainties = fit_coefficients(design_matrix, y)
    
    assert len(coeffs) == 2
    assert np.isclose(coeffs[0], 2.0, atol=0.1) # Slope
    assert np.isclose(coeffs[1], 1.0, atol=0.1) # Intercept
    assert np.all(uncertainties >= 0) # Uncertainties should be non-negative

def test_fit_coefficients_with_sh_data():
    """Test fit_coefficients with a generated SH design matrix and observed data."""
    degree = 1
    design_matrix = compute_basis_functions(TEST_LATITUDE, TEST_LONGITUDE, degree)
    
    # Use the test observed field components
    coeffs, uncertainties = fit_coefficients(design_matrix, TEST_OBSERVED_FIELD_COMPONENTS_1D)
    
    assert len(coeffs) == 3 # For degree 1
    assert len(uncertainties) == 3
    assert np.all(np.isfinite(coeffs))
    assert np.all(uncertainties >= 0)

def test_fit_coefficients_dimension_mismatch():
    """Test fit_coefficients with dimension mismatch."""
    design_matrix = np.array([[1, 2], [3, 4]])
    observed = np.array([1, 2, 3]) # Mismatch
    with pytest.raises(ValueError, match="Dimension mismatch"):
        fit_coefficients(design_matrix, observed)

def test_fit_coefficients_underdetermined_system():
    """Test fit_coefficients with an underdetermined system."""
    design_matrix = np.array([[1, 2, 3], [4, 5, 6]]) # 2 observations, 3 coefficients
    observed = np.array([1, 2])
    with pytest.raises(ValueError, match="Underdetermined system"):
        fit_coefficients(design_matrix, observed)

def test_fit_coefficients_perfectly_determined_uncertainties():
    """Test uncertainty calculation for a perfectly determined system (DOF=0)."""
    # 3 observations, 3 coefficients (e.g., degree 1 SH for 1 point)
    single_lat = np.array([0.0])
    single_lon = np.array([0.0])
    single_Bx = np.array([1000.0])
    single_By = np.array([0.0])
    single_Bz = np.array([2000.0])
    
    design_matrix = compute_basis_functions(single_lat, single_lon, 1) # Shape (3, 3)
    observed_1d = np.concatenate((single_Bx, single_By, single_Bz)) # Shape (3,)

    coeffs, uncertainties = fit_coefficients(design_matrix, observed_1d)
    
    assert len(coeffs) == 3
    assert len(uncertainties) == 3
    # For a perfectly determined system with no noise, residuals are 0, sigma_squared is 0.
    # Uncertainties should be 0.
    assert np.all(np.isclose(uncertainties, 0.0))

# --- Unit Tests for Data Ingestion Module (COMP-001) ---

def test_load_data_csv_success(tmp_path):
    """Test loading a valid CSV file."""
    csv_content = "latitude,longitude,Bx,By,Bz\n10,20,100,50,200\n"
    csv_file = tmp_path / "test.csv"
    csv_file.write_text(csv_content)
    
    df = load_data(str(csv_file))
    assert not df.empty
    assert 'latitude' in df.columns
    assert df.iloc[0]['latitude'] == 10

def test_load_data_file_not_found():
    """Test loading a non-existent file."""
    with pytest.raises(FileNotFoundError):
        load_data("non_existent_file.csv")

def test_load_data_unsupported_format(tmp_path):
    """Test loading an unsupported file format."""
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("some text")
    with pytest.raises(ValueError, match="Unsupported file format"):
        load_data(str(txt_file))

# --- Unit Tests for Data Validation Module (COMP-002) ---

def test_validate_data_valid():
    """Test validation with valid data."""
    is_valid, errors = validate_data(TEST_DF_VALID)
    assert is_valid is True
    assert len(errors) == 0

def test_validate_data_missing_column():
    """Test validation with a missing required column."""
    df_invalid = TEST_DF_VALID.drop(columns=['Bx'])
    is_valid, errors = validate_data(df_invalid)
    assert is_valid is False
    assert "Missing required column: 'Bx'." in errors

def test_validate_data_missing_values():
    """Test validation with missing values."""
    df_invalid = TEST_DF_VALID.copy()
    df_invalid.loc[0, 'latitude'] = np.nan
    is_valid, errors = validate_data(df_invalid)
    assert is_valid is False
    assert "Column 'latitude' contains missing values." in errors

def test_validate_data_out_of_bounds_latitude():
    """Test validation with out-of-bounds latitude."""
    df_invalid = TEST_DF_VALID.copy()
    df_invalid.loc[0, 'latitude'] = 91.0
    is_valid, errors = validate_data(df_invalid)
    assert is_valid is False
    assert "Latitude values are out of bounds (-90 to 90 degrees)." in errors

def test_validate_data_non_numeric_column():
    """Test validation with non-numeric magnetic field component."""
    df_invalid = TEST_DF_VALID.copy()
    df_invalid.loc[0, 'Bx'] = 'invalid'
    is_valid, errors = validate_data(df_invalid)
    assert is_valid is False
    assert "Magnetic field component 'Bx' is not numeric." in errors

# --- COMP-011 API Contract Implementation ---
def run_all_tests() -> bool:
    """
    Executes all defined unit tests for the application's core components using pytest.

    Returns:
        bool: True if all tests pass, False otherwise.
    """
    # pytest.main() returns an exit code. 0 for success, non-zero for failure.
    # We pass the absolute path to this file to pytest.main to ensure it finds the tests
    # regardless of the current working directory.
    exit_code = pytest.main([os.path.abspath(__file__)])
    return exit_code == 0

# Example of how to run tests if this module is executed directly
if __name__ == '__main__':
    print("Running all core mathematical function tests...")
    if run_all_tests():
        print("All tests passed!")
    else:
        print("Some tests failed.")

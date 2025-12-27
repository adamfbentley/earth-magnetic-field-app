"""
Basic tests for spherical harmonics module.

Tests core mathematical functionality of the magnetic field modeling.
"""

import pytest
import numpy as np
from src.spherical_harmonics import compute_basis_functions, reconstruct_field


class TestSphericalHarmonics:
    """Test suite for spherical harmonic functions."""
    
    def test_basis_functions_shape(self):
        """Test that basis function matrix has correct dimensions."""
        # Create sample coordinates
        lat = np.array([0, 45, 90])
        lon = np.array([0, 90, 180])
        degree = 3
        
        # Compute basis functions
        A = compute_basis_functions(lat, lon, degree)
        
        # For degree 3: coefficients are (g_1^0, g_1^1, h_1^1, g_2^0, ..., g_3^3, h_3^3)
        # Total coefficients = sum(2l+1) for l=1 to 3 = 3 + 5 + 7 = 15
        # 3 points × 3 components (Bx, By, Bz) = 9 rows
        expected_shape = (9, 15)
        
        assert A.shape == expected_shape, f"Expected shape {expected_shape}, got {A.shape}"
    
    def test_basis_functions_degree_1(self):
        """Test basis functions for minimum degree (dipole field)."""
        lat = np.array([0])
        lon = np.array([0])
        degree = 1
        
        A = compute_basis_functions(lat, lon, degree)
        
        # Degree 1: 3 coefficients (g_1^0, g_1^1, h_1^1)
        # 1 point × 3 components = 3 rows
        assert A.shape == (3, 3)
    
    def test_basis_functions_invalid_degree(self):
        """Test that invalid degree raises ValueError."""
        lat = np.array([0])
        lon = np.array([0])
        
        with pytest.raises(ValueError, match="must be at least 1"):
            compute_basis_functions(lat, lon, degree=0)
    
    def test_reconstruct_field_shape(self):
        """Test that field reconstruction returns correct shape."""
        lat = np.array([0, 30, 60])
        lon = np.array([0, 45, 90])
        degree = 2
        
        # Create dummy coefficients for degree 2
        # Degree 2: 3 + 5 = 8 coefficients
        coefficients = np.ones(8)
        
        Bx, By, Bz = reconstruct_field(lat, lon, degree, coefficients)
        
        assert Bx.shape == (3,), f"Expected Bx shape (3,), got {Bx.shape}"
        assert By.shape == (3,), f"Expected By shape (3,), got {By.shape}"
        assert Bz.shape == (3,), f"Expected Bz shape (3,), got {Bz.shape}"
    
    def test_basis_functions_single_point(self):
        """Test with single measurement point."""
        lat = np.array([45.0])
        lon = np.array([-120.0])
        degree = 2
        
        A = compute_basis_functions(lat, lon, degree)
        
        # 1 point × 3 components = 3 rows
        # Degree 2: 3 + 5 = 8 coefficients
        assert A.shape == (3, 8)
    
    def test_basis_functions_non_zero(self):
        """Test that basis functions are non-zero for typical inputs."""
        lat = np.array([0, 45])
        lon = np.array([0, 90])
        degree = 2
        
        A = compute_basis_functions(lat, lon, degree)
        
        # At least some elements should be non-zero
        assert np.any(A != 0), "Basis functions should not be all zeros"
        
        # Should not contain NaN or Inf
        assert not np.any(np.isnan(A)), "Basis functions contain NaN"
        assert not np.any(np.isinf(A)), "Basis functions contain Inf"


class TestFieldReconstruction:
    """Test suite for magnetic field reconstruction."""
    
    def test_reconstruct_field_with_zero_coefficients(self):
        """Test field reconstruction with zero coefficients."""
        lat = np.array([0, 30])
        lon = np.array([0, 45])
        degree = 1
        coefficients = np.zeros(3)  # All zeros for degree 1
        
        Bx, By, Bz = reconstruct_field(lat, lon, degree, coefficients)
        
        # With zero coefficients, field should be zero
        np.testing.assert_array_almost_equal(Bx, np.zeros(2), decimal=10)
        np.testing.assert_array_almost_equal(By, np.zeros(2), decimal=10)
        np.testing.assert_array_almost_equal(Bz, np.zeros(2), decimal=10)
    
    def test_reconstruct_field_dipole(self):
        """Test dipole field (degree 1) reconstruction."""
        lat = np.array([90.0, 0.0, -90.0])  # North pole, equator, south pole
        lon = np.array([0.0, 0.0, 0.0])
        degree = 1
        
        # Simple dipole: g_1^0 = 1, others = 0
        coefficients = np.array([1.0, 0.0, 0.0])
        
        Bx, By, Bz = reconstruct_field(lat, lon, degree, coefficients)
        
        # For a pure axial dipole (g_1^0 only):
        # - At poles: Bz should be largest
        # - At equator: Bx should be largest
        # Basic sanity checks
        assert abs(Bz[0]) > abs(Bx[0]), "At north pole, Bz should dominate"
        assert abs(Bz[2]) > abs(Bx[2]), "At south pole, Bz should dominate"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

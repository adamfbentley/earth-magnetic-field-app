#!/usr/bin/env python3
"""
Generate sample magnetic field data for testing and demonstration.

Creates synthetic magnetometer measurements with realistic Earth's magnetic
field characteristics for testing the spherical harmonic analysis.
"""

import numpy as np
import pandas as pd
from pathlib import Path


def generate_dipole_field(lat, lon, g10=30000):
    """
    Generate simple dipole magnetic field (degree 1, order 0).
    
    Args:
        lat: Latitude in degrees
        lon: Longitude in degrees  
        g10: Dipole coefficient in nT (default ~Earth's value)
    
    Returns:
        Bx, By, Bz: North, East, Down components in nT
    """
    lat_rad = np.deg2rad(lat)
    lon_rad = np.deg2rad(lon)
    
    # Simple dipole field approximation
    # Bx (north) ~ -2 * g10 * sin(lat)
    # By (east) ~ 0 (axial dipole)
    # Bz (down) ~ g10 * cos(lat)
    
    Bx = -2 * g10 * np.sin(lat_rad)
    By = np.zeros_like(lat)  # Axial dipole has no east component
    Bz = g10 * np.cos(lat_rad)
    
    return Bx, By, Bz


def generate_sample_measurements(n_points=100, noise_level=100):
    """
    Generate synthetic magnetic field measurements.
    
    Args:
        n_points: Number of measurement points
        noise_level: Standard deviation of measurement noise in nT
    
    Returns:
        DataFrame with columns: latitude, longitude, Bx, By, Bz
    """
    # Generate random sampling locations
    lat = np.random.uniform(-90, 90, n_points)
    lon = np.random.uniform(-180, 180, n_points)
    
    # Generate dipole field
    Bx, By, Bz = generate_dipole_field(lat, lon)
    
    # Add measurement noise
    Bx += np.random.normal(0, noise_level, n_points)
    By += np.random.normal(0, noise_level, n_points)
    Bz += np.random.normal(0, noise_level, n_points)
    
    # Create DataFrame
    df = pd.DataFrame({
        'latitude': lat,
        'longitude': lon,
        'Bx': Bx,
        'By': By,
        'Bz': Bz
    })
    
    return df


def generate_grid_measurements(lat_points=10, lon_points=20, noise_level=50):
    """
    Generate measurements on a regular grid.
    
    Args:
        lat_points: Number of latitude points
        lon_points: Number of longitude points
        noise_level: Standard deviation of noise in nT
    
    Returns:
        DataFrame with gridded measurements
    """
    # Create regular grid
    lat = np.linspace(-90, 90, lat_points)
    lon = np.linspace(-180, 180, lon_points)
    
    lat_grid, lon_grid = np.meshgrid(lat, lon)
    lat_flat = lat_grid.flatten()
    lon_flat = lon_grid.flatten()
    
    # Generate field
    Bx, By, Bz = generate_dipole_field(lat_flat, lon_flat)
    
    # Add noise
    n_total = len(lat_flat)
    Bx += np.random.normal(0, noise_level, n_total)
    By += np.random.normal(0, noise_level, n_total)
    Bz += np.random.normal(0, noise_level, n_total)
    
    df = pd.DataFrame({
        'latitude': lat_flat,
        'longitude': lon_flat,
        'Bx': Bx,
        'By': By,
        'Bz': Bz
    })
    
    return df


def main():
    """Generate and save sample datasets."""
    # Create data directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    print("Generating sample magnetic field datasets...")
    
    # Generate random sample
    print("  - Creating random_measurements.csv (100 points, dipole field + noise)")
    df_random = generate_sample_measurements(n_points=100, noise_level=100)
    df_random.to_csv(data_dir / "random_measurements.csv", index=False)
    
    # Generate grid sample
    print("  - Creating grid_measurements.csv (10x20 grid, dipole field + noise)")
    df_grid = generate_grid_measurements(lat_points=10, lon_points=20, noise_level=50)
    df_grid.to_csv(data_dir / "grid_measurements.csv", index=False)
    
    # Generate clean dipole (for validation)
    print("  - Creating dipole_clean.csv (200 points, no noise)")
    df_clean = generate_sample_measurements(n_points=200, noise_level=0)
    df_clean.to_csv(data_dir / "dipole_clean.csv", index=False)
    
    print(f"\nSample data created in {data_dir}/")
    print("\nFiles created:")
    print("  - random_measurements.csv: Random sampling with noise")
    print("  - grid_measurements.csv: Regular grid with noise")
    print("  - dipole_clean.csv: Clean dipole field for validation")
    print("\nUse these files to test the application:")
    print("  python main.py")
    print("  Then load any CSV file via the Data Ingestion tab")


if __name__ == "__main__":
    main()

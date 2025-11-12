import numpy as np
from scipy.special import lpmn

def compute_basis_functions(latitude: np.ndarray, longitude: np.ndarray, degree: int) -> np.ndarray:
    """
    Calculates the spherical harmonic basis functions for magnetic field components (Bx, By, Bz)
    at given coordinates and maximum spherical harmonic degree (L_max).

    The basis functions are derived from the scalar potential for internal sources, assuming
    measurements are on the Earth's surface (r=a). Schmidt semi-normalized associated Legendre
    polynomials are used.

    The design matrix 'A' is constructed such that B_obs = A * C, where B_obs is the stacked
    observed field components [Bx, By, Bz] and C are the Gauss coefficients [g_lm, h_lm].

    Args:
        latitude (np.ndarray): Array of latitudes in degrees.
        longitude (np.ndarray): Array of longitudes in degrees.
        degree (int): The maximum spherical harmonic degree (L_max).

    Returns:
        np.ndarray: A design matrix of shape (N_points * 3, N_coefficients).
                    The rows correspond to [Bx_points, By_points, Bz_points].
                    The columns correspond to Gauss coefficients (g_l^m, h_l^m).

    Raises:
        ValueError: If degree is less than 1.
    """
    if degree < 1:
        raise ValueError("Spherical harmonic degree must be at least 1 for magnetic field modeling.")

    num_points = len(latitude)

    # Convert degrees to radians
    theta_rad = np.deg2rad(90 - latitude)  # Co-latitude
    phi_rad = np.deg2rad(longitude)

    design_matrix_cols = []

    # Iterate through spherical harmonic degrees (l) and orders (m)
    # For internal field, l starts from 1 (g_0^0 is a monopole and typically excluded)
    for l in range(1, degree + 1):
        # lpmn returns (P_m_l, dP_m_l_dx) where x = cos(theta)
        # P_m_l[m, l] is P_l^m(cos(theta))
        # dP_m_l_dx[m, l] is dP_l^m(cos(theta))/d(cos(theta))
        P_lm_all_m, dP_lm_dx_all_m = lpmn(l, l, np.cos(theta_rad))

        for m in range(l + 1):
            P_lm = P_lm_all_m[m, l]  # P_l^m(cos(theta)) for all points
            dP_lm_dx = dP_lm_dx_all_m[m, l]  # dP_l^m(cos(theta))/d(cos(theta)) for all points

            cos_m_phi = np.cos(m * phi_rad)
            sin_m_phi = np.sin(m * phi_rad)

            sin_theta = np.sin(theta_rad)
            
            # dP_l^m(cos(theta))/dtheta = (dP_l^m/dx) * (dx/dtheta) = (dP_l^m/dx) * (-sin(theta))
            dP_lm_dtheta_actual = np.nan_to_num(dP_lm_dx * (-sin_theta))

            # Handle division by sin(theta) for By terms. P_l^m is proportional to sin^m(theta),
            # so P_l^m / sin(theta) is well-behaved (proportional to sin^(m-1)(theta)).
            # Use np.divide with where clause to avoid warnings for exact zeros at poles, and clean up any NaNs.
            P_lm_div_sin_theta = np.divide(P_lm, sin_theta, out=np.zeros_like(P_lm), where=sin_theta != 0)
            np.nan_to_num(P_lm_div_sin_theta, copy=False)

            # Basis functions for g_l^m coefficients
            # Bx (North) = -B_theta
            # By (East)  = B_phi
            # Bz (Down)  = -B_r
            # Assuming r=a, (a/r)^(l+2) = 1.

            # For g_l^m
            # Corrected: Bx_g_lm = dP_lm_dtheta_actual * cos_m_phi
            g_lm_Bx = dP_lm_dtheta_actual * cos_m_phi
            # Corrected: By_g_lm = m * P_lm_div_sin_theta * sin_m_phi
            g_lm_By = m * P_lm_div_sin_theta * sin_m_phi
            # Correct: Bz_g_lm = -(l + 1) * P_lm * cos_m_phi
            g_lm_Bz = -(l + 1) * P_lm * cos_m_phi
            design_matrix_cols.append(np.concatenate((g_lm_Bx, g_lm_By, g_lm_Bz)))

            # For h_l^m (only if m > 0)
            if m > 0:
                # Corrected: Bx_h_lm = dP_lm_dtheta_actual * sin_m_phi
                h_lm_Bx = dP_lm_dtheta_actual * sin_m_phi
                # Corrected: By_h_lm = -m * P_lm_div_sin_theta * cos_m_phi
                h_lm_By = -m * P_lm_div_sin_theta * cos_m_phi
                # Correct: Bz_h_lm = -(l + 1) * P_lm * sin_m_phi
                h_lm_Bz = -(l + 1) * P_lm * sin_m_phi
                design_matrix_cols.append(np.concatenate((h_lm_Bx, h_lm_By, h_lm_Bz)))

    # Stack all columns to form the final design matrix
    if not design_matrix_cols:
        # This case should ideally not be reached if degree >= 1
        return np.empty((num_points * 3, 0))

    return np.column_stack(design_matrix_cols)

def reconstruct_field(latitude: np.ndarray, longitude: np.ndarray, coefficients: np.ndarray, degree: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Reconstructs magnetic field components (Bx, By, Bz) at specified points
    using Gauss coefficients and spherical harmonic expansion.

    Args:
        latitude (np.ndarray): Array of latitudes in degrees.
        longitude (np.ndarray): Array of longitudes in degrees.
        coefficients (np.ndarray): A 1D array of Gauss coefficients (g_l^m, h_l^m)
                                   in the order they are generated by compute_basis_functions.
        degree (int): The maximum spherical harmonic degree (L_max) used for reconstruction.

    Returns:
        tuple[np.ndarray, np.ndarray, np.ndarray]: A tuple containing three np.ndarrays:
                                                   - Bx (np.ndarray): Reconstructed North component of the magnetic field.
                                                   - By (np.ndarray): Reconstructed East component of the magnetic field.
                                                   - Bz (np.ndarray): Reconstructed Down component of the magnetic field.

    Raises:
        ValueError: If degree is less than 1, or if the number of coefficients
                    does not match the expected number for the given degree.
    """
    if degree < 1:
        raise ValueError("Spherical harmonic degree must be at least 1 for magnetic field modeling.")

    num_points = len(latitude)
    expected_num_coefficients = (degree + 1)**2 - 1
    if len(coefficients) != expected_num_coefficients:
        raise ValueError(
            f"Number of provided coefficients ({len(coefficients)}) does not match "
            f"the expected number ({expected_num_coefficients}) for degree {degree}."
        )

    # Compute the design matrix using the existing function
    design_matrix = compute_basis_functions(latitude, longitude, degree)

    # Perform the matrix multiplication to reconstruct the field components
    # B_obs = A @ C
    # B_obs will be a 1D array of shape (num_points * 3,)
    B_obs = design_matrix @ coefficients

    # Reshape B_obs into Bx, By, Bz components
    Bx_reconstructed = B_obs[:num_points]
    By_reconstructed = B_obs[num_points:2*num_points]
    Bz_reconstructed = B_obs[2*num_points:]
    
    return Bx_reconstructed, By_reconstructed, Bz_reconstructed


EARTH_RADIUS_KM = 6371.2

def get_field_at_point_r(lat_deg: float, lon_deg: float, radius_km: float, coefficients: np.ndarray, degree: int) -> tuple[float, float, float]:
    """
    Calculates the magnetic field vector (Bx, By, Bz) at a single point in space.

    Args:
        lat_deg (float): Latitude in degrees.
        lon_deg (float): Longitude in degrees.
        radius_km (float): Radius from the center of the Earth in kilometers.
        coefficients (np.ndarray): 1D array of Gauss coefficients.
        degree (int): Maximum spherical harmonic degree (L_max).

    Returns:
        tuple[float, float, float]: The Bx (North), By (East), and Bz (Down) components of the magnetic field.
    """
    if radius_km <= 0:
        raise ValueError("Radius must be positive.")

    lat = np.array([lat_deg])
    lon = np.array([lon_deg])
    
    theta_rad = np.deg2rad(90 - lat)  # Co-latitude
    phi_rad = np.deg2rad(lon)

    Br = 0.0
    B_theta = 0.0
    B_phi = 0.0
    
    coeff_idx = 0
    for l in range(1, degree + 1):
        P_lm_all, dP_lm_dx_all = lpmn(l, l, np.cos(theta_rad))
        
        for m in range(l + 1):
            P_lm = P_lm_all[m, l][0]
            dP_lm_dx = dP_lm_dx_all[m, l][0]

            # dP/d_theta = dP/dx * dx/d_theta = dP/dx * (-sin(theta))
            dP_lm_dtheta = dP_lm_dx * -np.sin(theta_rad[0])

            g_lm = coefficients[coeff_idx]
            coeff_idx += 1
            if m > 0:
                h_lm = coefficients[coeff_idx]
                coeff_idx += 1
            else:
                h_lm = 0.0

            radial_term = (EARTH_RADIUS_KM / radius_km)**(l + 2)
            
            cos_m_phi = np.cos(m * phi_rad[0])
            sin_m_phi = np.sin(m * phi_rad[0])

            # Equations for Br, B_theta, B_phi
            Br += radial_term * (l + 1) * P_lm * (g_lm * cos_m_phi + h_lm * sin_m_phi)
            B_theta += radial_term * -dP_lm_dtheta * (g_lm * cos_m_phi + h_lm * sin_m_phi)
            
            if np.sin(theta_rad[0]) != 0:
                B_phi += radial_term * (m / np.sin(theta_rad[0])) * P_lm * (g_lm * sin_m_phi - h_lm * cos_m_phi)

    # Convert from (Br, B_theta, B_phi) to (Bx, By, Bz)
    # Bx (North) = -B_theta
    # By (East)  = B_phi
    # Bz (Down)  = -Br
    return -B_theta, B_phi, -Br

def calculate_declination(latitude: np.ndarray, longitude: np.ndarray, coefficients: np.ndarray, degree: int) -> np.ndarray:
    """
    Calculates the magnetic declination (angle between magnetic north and true north)
    at specified points using Gauss coefficients.

    Args:
        latitude (np.ndarray): Array of latitudes in degrees.
        longitude (np.ndarray): Array of longitudes in degrees.
        coefficients (np.ndarray): A 1D array of Gauss coefficients (g_l^m, h_l^m).
        degree (int): The maximum spherical harmonic degree (L_max) used for reconstruction.

    Returns:
        np.ndarray: An array of magnetic declination values in degrees.
                    Positive values indicate East declination, negative values indicate West declination.
    """
    Bx, By, _ = reconstruct_field(latitude, longitude, coefficients, degree)
    
    # Magnetic Declination (D) = atan2(By, Bx)
    # atan2 returns values in radians, convert to degrees
    declination = np.degrees(np.arctan2(By, Bx))
    
    return declination

def calculate_total_intensity(latitude: np.ndarray, longitude: np.ndarray, coefficients: np.ndarray, degree: int) -> np.ndarray:
    """
    Calculates the total magnetic field intensity (F) at specified points.

    The total intensity is calculated as the magnitude of the magnetic field vector:
    F = sqrt(Bx^2 + By^2 + Bz^2).

    Args:
        latitude (np.ndarray): Array of latitudes in degrees.
        longitude (np.ndarray): Array of longitudes in degrees.
        coefficients (np.ndarray): A 1D array of Gauss coefficients (g_l^m, h_l^m).
        degree (int): The maximum spherical harmonic degree (L_max) used for reconstruction.

    Returns:
        np.ndarray: An array of total magnetic field intensity values.
    """
    Bx, By, Bz = reconstruct_field(latitude, longitude, coefficients, degree)
    
    # Total Intensity (F) = sqrt(Bx^2 + By^2 + Bz^2)
    intensity = np.sqrt(Bx**2 + By**2 + Bz**2)
    
    return intensity

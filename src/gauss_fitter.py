import numpy as np
from scipy.linalg import lstsq

def fit_coefficients(design_matrix: np.ndarray, observed_field_components: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Applies least squares fitting to calculate Gauss coefficients from observed magnetic field data
    and a spherical harmonic design matrix, including uncertainty estimates.

    Args:
        design_matrix (np.ndarray): The design matrix 'A' from spherical harmonic basis functions,
                                    shape (N_points * 3, N_coefficients).
        observed_field_components (np.ndarray): A 1D array of observed magnetic field components,
                                                stacked as [Bx_points, By_points, Bz_points],
                                                shape (N_points * 3,).

    Returns:
        tuple[np.ndarray, np.ndarray]: A tuple containing:
                                       - coefficients (np.ndarray): The calculated Gauss coefficients,
                                         shape (N_coefficients,).
                                       - uncertainties (np.ndarray): The standard errors of the Gauss
                                         coefficients, shape (N_coefficients,).

    Raises:
        ValueError: If the dimensions of design_matrix and observed_field_components are incompatible,
                    or if the system is underdetermined.
        np.linalg.LinAlgError: If the design matrix is singular or ill-conditioned for uncertainty calculation.
    """
    if design_matrix.shape[0] != observed_field_components.shape[0]:
        raise ValueError(
            f"Dimension mismatch: design_matrix has {design_matrix.shape[0]} rows, "
            f"but observed_field_components has {observed_field_components.shape[0]} elements."
        )
    if design_matrix.shape[0] < design_matrix.shape[1]:
        raise ValueError(
            f"Underdetermined system: Number of observations ({design_matrix.shape[0]}) "
            f"is less than the number of coefficients ({design_matrix.shape[1]})."
        )

    # Perform least squares fitting
    # lstsq returns: x (coefficients), residuals, rank, s (singular values)
    coefficients, residuals_sum_sq, rank, s = lstsq(design_matrix, observed_field_components)

    num_observations = design_matrix.shape[0] # N_points * 3
    num_coefficients = design_matrix.shape[1]

    # Calculate the variance of the residuals (sigma^2)
    # residuals_sum_sq is the sum of squared residuals, which is a scalar for a 1D observed_field_components.
    if residuals_sum_sq.size == 0:
        # This can happen if the system is perfectly determined with zero residuals.
        # In such cases, sigma^2 is effectively 0, and uncertainties would be 0.
        sigma_squared = 0.0
    else:
        # Ensure residuals_sum_sq is a scalar for the calculation
        if isinstance(residuals_sum_sq, np.ndarray) and residuals_sum_sq.size == 1:
            residuals_sum_sq = residuals_sum_sq.item()
        elif isinstance(residuals_sum_sq, np.ndarray) and residuals_sum_sq.size > 1:
            # This case should not happen for a single observed_field_components vector
            residuals_sum_sq = np.sum(residuals_sum_sq)

        degrees_of_freedom = num_observations - num_coefficients
        if degrees_of_freedom <= 0:
            # System is perfectly determined or underdetermined, cannot estimate variance reliably.
            # Set sigma_squared to 0 for perfectly determined, or handle as an edge case.
            sigma_squared = 0.0 # No statistical uncertainty if no degrees of freedom
        else:
            sigma_squared = residuals_sum_sq / degrees_of_freedom

    # Calculate the covariance matrix of the coefficients
    # Cov(C) = sigma^2 * (A^T * A)^-1
    try:
        ATA = design_matrix.T @ design_matrix
        # Check for ill-conditioning before inversion. A high condition number indicates
        # that the matrix is close to singular, and its inverse (and thus uncertainties)
        # will be highly sensitive to small changes, making them unreliable.
        if np.linalg.cond(ATA) > 1e10: # Threshold for ill-conditioning
            uncertainties = np.full_like(coefficients, np.nan) # Indicate non-computable uncertainties
        else:
            cov_matrix_inv = np.linalg.inv(ATA)
            covariance_matrix = sigma_squared * cov_matrix_inv
            uncertainties = np.sqrt(np.diag(covariance_matrix))

    except np.linalg.LinAlgError:
        # Handle singular matrix case (e.g., if design_matrix is rank deficient)
        # In this case, standard errors cannot be computed in the usual way.
        uncertainties = np.full_like(coefficients, np.nan) # Indicate non-computable uncertainties

    return coefficients, uncertainties

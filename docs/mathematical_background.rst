Mathematical Background
=======================

This section provides an overview of the core mathematical and geophysical principles underpinning the Magnetic Field Data Analyzer.

Spherical Harmonics Theory
--------------------------

The Earth's magnetic field can be approximated by a scalar potential :math:`V` that satisfies Laplace's equation :math:`\nabla^2 V = 0` in source-free regions. This potential can be expressed as a series of spherical harmonic functions:

.. math::
   V(r, \theta, \phi) = a \sum_{l=1}^{L_{max}} \sum_{m=0}^{l} \left( \frac{a}{r} \right)^{l+1} \left( g_l^m \cos(m\phi) + h_l^m \sin(m\phi) \right) P_l^m(\cos\theta)

where:

*   :math:`r, \theta, \phi` are spherical coordinates (radius, colatitude, longitude).
*   :math:`a` is the Earth's reference radius (e.g., 6371.2 km).
*   :math:`L_{max}` is the maximum spherical harmonic degree.
*   :math:`P_l^m(\cos\theta)` are the Schmidt semi-normalized associated Legendre functions.
*   :math:`g_l^m` and :math:`h_l^m` are the Gauss coefficients, which are the unknown parameters to be determined.

The magnetic field components (:math:`B_r, B_\theta, B_\phi`) are derived from the negative gradient of the scalar potential:

.. math::
   B_r = -\frac{\partial V}{\partial r}
   B_\theta = -\frac{1}{r}\frac{\partial V}{\partial \theta}
   B_\phi = -\frac{1}{r\sin\theta}\frac{\partial V}{\partial \phi}

Gauss Coefficients
------------------

Gauss coefficients :math:`g_l^m` and :math:`h_l^m` are fundamental to describing the internal magnetic field. They represent the amplitudes of the spherical harmonic components. These coefficients are typically determined by fitting observed magnetic field data to the spherical harmonic model.

Least Squares Fitting Methodology
---------------------------------

The process of determining the Gauss coefficients from observed magnetic field data is typically performed using a least squares fitting approach. Given a set of :math:`N` observations of the magnetic field components (:math:`B_x, B_y, B_z` or :math:`B_r, B_\theta, B_\phi`) at various locations, we can formulate a linear system of equations.

Each observation point contributes three equations (one for each component) to a design matrix :math:`A`. The observed field components form the observation vector :math:`\mathbf{d}`. The unknown Gauss coefficients form the model vector :math:`\mathbf{m}`.

The system can be written as:

.. math::
   A \mathbf{m} = \mathbf{d}

Where:

*   :math:`A` is the design matrix, constructed from the spherical harmonic basis functions evaluated at each observation point.
*   :math:`\mathbf{m}` is the vector of unknown Gauss coefficients.
*   :math:`\mathbf{d}` is the vector of observed magnetic field components.

The least squares solution for :math:`\mathbf{m}` minimizes the sum of the squares of the residuals :math:`||A\mathbf{m} - \mathbf{d}||^2`. The solution is given by:

.. math::
   \mathbf{m} = (A^T A)^{-1} A^T \mathbf{d}

Uncertainties in the coefficients can also be estimated from the covariance matrix, which is related to :math:`(A^T A)^{-1}` and the variance of the residuals.

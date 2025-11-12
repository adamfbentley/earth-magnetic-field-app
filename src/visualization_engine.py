import plotly.graph_objects as go
import pandas as pd
import numpy as np
from plotly.subplots import make_subplots
import plotly.io as pio
import os
from PIL import Image
from src.spherical_harmonics import get_field_at_point_r, EARTH_RADIUS_KM, calculate_declination, calculate_total_intensity

def _spherical_to_cartesian_vectors(latitude: np.ndarray, longitude: np.ndarray, Bx: np.ndarray, By: np.ndarray, Bz: np.ndarray, R: float = 1.0):
    """
    Converts spherical coordinates (latitude, longitude) and magnetic field
    components (Bx, By, Bz in North, East, Down) to Cartesian coordinates (x, y, z)
    and Cartesian vector components (u, v, w) for Plotly cone plots.

    Args:
        latitude (np.ndarray): Array of latitudes in degrees.
        longitude (np.ndarray): Array of longitudes in degrees.
        Bx (np.ndarray): North component of the magnetic field.
        By (np.ndarray): East component of the magnetic field.
        Bz (np.ndarray): Down component of the magnetic field.
        R (float): Radius of the sphere for position calculation (e.g., Earth radius).

    Returns:
        tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        (x, y, z, u, v, w) Cartesian coordinates and vector components.
    """
    lat_rad = np.deg2rad(latitude)
    lon_rad = np.deg2rad(longitude)

    x = R * np.cos(lat_rad) * np.cos(lon_rad)
    y = R * np.cos(lat_rad) * np.sin(lon_rad)
    z = R * np.sin(lat_rad)

    sin_lat = np.sin(lat_rad)
    cos_lat = np.cos(lat_rad)
    sin_lon = np.sin(lon_rad)
    cos_lon = np.cos(lon_rad)

    R_matrix_all = np.zeros((len(latitude), 3, 3))

    R_matrix_all[:, 0, 0] = -sin_lat * cos_lon
    R_matrix_all[:, 1, 0] = -sin_lat * sin_lon
    R_matrix_all[:, 2, 0] = cos_lat

    R_matrix_all[:, 0, 1] = -sin_lon
    R_matrix_all[:, 1, 1] = cos_lon
    R_matrix_all[:, 2, 1] = np.zeros_like(lat_rad)

    R_matrix_all[:, 0, 2] = -cos_lat * cos_lon
    R_matrix_all[:, 1, 2] = -cos_lat * sin_lon
    R_matrix_all[:, 2, 2] = -sin_lat

    vec_ned_all = np.stack([Bx, By, Bz], axis=-1)

    # The matmul operation expects a stack of vectors (N, 3, 1), but vec_ned_all is (N, 3).
    # We add a new axis to vec_ned_all to make it (N, 3, 1) and then squeeze the result back to (N, 3).
    vec_ecef_all = np.matmul(R_matrix_all, vec_ned_all[..., np.newaxis]).squeeze(axis=-1)

    u, v, w = vec_ecef_all[:, 0], vec_ecef_all[:, 1], vec_ecef_all[:, 2]

    return x, y, z, u, v, w

def create_3d_globe(data_points: pd.DataFrame) -> go.Figure:
    """
    Creates an interactive 3D globe plot displaying magnetic field measurement locations.

    Args:
        data_points (pd.DataFrame): A DataFrame containing at least 'latitude' and 'longitude' columns.

    Returns:
        plotly.graph_objects.Figure: An interactive Plotly 3D globe figure.

    Raises:
        ValueError: If the DataFrame is empty or missing required columns.
    """
    if data_points.empty:
        # Return an empty figure or a figure with a placeholder message
        fig = go.Figure()
        fig.update_layout(
            title_text='3D Globe: No Data Available',
            title_x=0.5,
            geo=dict(
                scope='world',
                projection_type='orthographic',
                showland=True, landcolor='rgb(243, 243, 243)',
                showocean=True, oceancolor='rgb(100, 150, 200)',
                showcountries=True, countrycolor='rgb(204, 204, 204)',
                showframe=False, showcoastlines=True
            ),
            height=700,
            margin={"r":0,"t":50,"l":0,"b":0}
        )
        return fig

    if 'latitude' not in data_points.columns or 'longitude' not in data_points.columns:
        raise ValueError("DataFrame must contain 'latitude' and 'longitude' columns for 3D globe visualization.")

    scatter_trace = go.Scattergeo(
        lon=data_points['longitude'],
        lat=data_points['latitude'],
        mode='markers',
        marker=dict(
            size=8,
            opacity=0.8,
            color='blue',
            line=dict(width=0.5, color='white')
        ),
        name='Measurement Locations',
        hoverinfo='text',
        text=[f"Lat: {lat:.2f}°<br>Lon: {lon:.2f}°" for lat, lon in zip(data_points['latitude'], data_points['longitude'])]
    )

    fig = go.Figure(data=[scatter_trace])

    fig.update_layout(
        title_text='3D Globe of Magnetic Field Measurement Locations',
        title_x=0.5,
        showlegend=True,
        geo=dict(
            scope='world',
            projection_type='orthographic',
            showland=True,
            landcolor='rgb(243, 243, 243)',
            countrycolor='rgb(204, 204, 204)',
            showocean=True,
            oceancolor='rgb(100, 150, 200)',
            showcountries=True,
            showframe=False,
            showcoastlines=True,
            coastlinecolor='rgb(100, 100, 100)',
            lataxis_showgrid=True,
            lonaxis_showgrid=True,
            lataxis_gridcolor='rgb(150, 150, 150)',
            lonaxis_gridcolor='rgb(150, 150, 150)'
        ),
        height=700,
        margin={"r":0,"t":50,"l":0,"b":0}
    )
    return fig

def add_field_vectors(figure: go.Figure, latitude: np.ndarray, longitude: np.ndarray, observed_vectors: np.ndarray, modeled_vectors: np.ndarray) -> go.Figure:
    """
    Overlays observed and modeled magnetic field vectors onto the 3D globe.
    Assumes the figure already contains a Scattergeo trace with 'lat' and 'lon' data.

    Args:
        figure (plotly.graph_objects.Figure): The existing Plotly 3D globe figure.
        latitude (np.ndarray): Array of latitudes in degrees, corresponding to the vectors.
        longitude (np.ndarray): Array of longitudes in degrees, corresponding to the vectors.
        observed_vectors (np.ndarray): An (N, 3) array of observed magnetic field vectors (Bx, By, Bz).
        modeled_vectors (np.ndarray): An (N, 3) array of modeled magnetic field vectors (Bx, By, Bz).

    Returns:
        plotly.graph_objects.Figure: The updated Plotly figure with vectors.

    Raises:
        ValueError: If the figure does not contain latitude/longitude data or vector dimensions mismatch.
    """
    if len(latitude) != observed_vectors.shape[0] or len(latitude) != modeled_vectors.shape[0]:
        raise ValueError("Number of data points in figure and vectors must match.")
    if observed_vectors.shape[1] != 3 or modeled_vectors.shape[1] != 3:
        raise ValueError("Observed and modeled vectors must be (N, 3) arrays (Bx, By, Bz).")

    x_obs, y_obs, z_obs, u_obs, v_obs, w_obs = _spherical_to_cartesian_vectors(
        latitude, longitude, observed_vectors[:, 0], observed_vectors[:, 1], observed_vectors[:, 2]
    )

    x_mod, y_mod, z_mod, u_mod, v_mod, w_mod = _spherical_to_cartesian_vectors(
        latitude, longitude, modeled_vectors[:, 0], modeled_vectors[:, 1], modeled_vectors[:, 2]
    )

    magnitudes_obs = np.linalg.norm(observed_vectors, axis=1)
    magnitudes_mod = np.linalg.norm(modeled_vectors, axis=1)
    
    max_magnitude = 0.0
    if magnitudes_obs.size > 0:
        max_magnitude = max(max_magnitude, np.max(magnitudes_obs))
    if magnitudes_mod.size > 0:
        max_magnitude = max(max_magnitude, np.max(magnitudes_mod))

    target_visual_length = 0.1 
    
    dynamic_sizeref = 1.0
    if max_magnitude > 1e-9:
        dynamic_sizeref = max_magnitude / target_visual_length
        dynamic_sizeref = np.clip(dynamic_sizeref, 0.01, 1000.0)

    figure.add_trace(go.Cone(
        x=x_obs, y=y_obs, z=z_obs,
        u=u_obs, v=v_obs, w=w_obs,
        sizemode="absolute", sizeref=dynamic_sizeref,
        anchor="tail",
        colorscale=[[0, 'red'], [1, 'red']],
        showscale=False,
        name='Observed Vectors',
        hoverinfo='text',
        text=[f"Bx: {bx:.2f}<br>By: {by:.2f}<br>Bz: {bz:.2f}" for bx, by, bz in observed_vectors]
    ))

    figure.add_trace(go.Cone(
        x=x_mod, y=y_mod, z=z_mod,
        u=u_mod, v=v_mod, w=w_mod,
        sizemode="absolute", sizeref=dynamic_sizeref,
        anchor="tail",
        colorscale=[[0, 'green'], [1, 'green']],
        showscale=False,
        name='Modeled Vectors',
        hoverinfo='text',
        text=[f"Bx: {bx:.2f}<br>By: {by:.2f}<br>Bz: {bz:.2f}" for bx, by, bz in modeled_vectors]
    ))

    figure.update_layout(
        title_text='3D Globe with Magnetic Field Vectors',
        title_x=0.5,
        showlegend=True
    )

    return figure

def plot_residuals(observed: np.ndarray, modeled: np.ndarray) -> go.Figure:
    """
    Generates plots showing the distribution and statistical summaries of residuals.

    Args:
        observed (np.ndarray): An (N, 3) array of observed magnetic field components (Bx, By, Bz).
        modeled (np.ndarray): An (N, 3) array of modeled magnetic field components (Bx, By, Bz).

    Returns:
        plotly.graph_objects.Figure: A Plotly figure with residual histograms and statistics.

    Raises:
        ValueError: If input arrays are not (N, 3) or have incompatible dimensions.
    """
    if observed.shape != modeled.shape or observed.shape[1] != 3:
        raise ValueError("Observed and modeled arrays must be (N, 3) and have compatible dimensions.")
    if observed.size == 0:
        raise ValueError("Input arrays for residuals cannot be empty.")

    residuals = observed - modeled
    
    residuals_bx = residuals[:, 0]
    residuals_by = residuals[:, 1]
    residuals_bz = residuals[:, 2]

    fig = make_subplots(
        rows=4, cols=1,
        subplot_titles=("Residuals Bx (North)", "Residuals By (East)", "Residuals Bz (Down)", "Residual Statistics"),
        vertical_spacing=0.08,
        row_heights=[0.3, 0.3, 0.3, 0.1],
        specs=[[{"type": "xy"}],
               [{"type": "xy"}],
               [{"type": "xy"}],
               [{"type": "table"}]]
    )

    fig.add_trace(go.Histogram(x=residuals_bx, name='Bx Residuals', marker_color='#1f77b4', opacity=0.7, showlegend=False),
                  row=1, col=1)
    fig.add_trace(go.Histogram(x=residuals_by, name='By Residuals', marker_color='#ff7f0e', opacity=0.7, showlegend=False),
                  row=2, col=1)
    fig.add_trace(go.Histogram(x=residuals_bz, name='Bz Residuals', marker_color='#2ca02c', opacity=0.7, showlegend=False),
                  row=3, col=1)

    fig.update_xaxes(title_text="Residual Value", row=1, col=1)
    fig.update_yaxes(title_text="Count", row=1, col=1)
    fig.update_xaxes(title_text="Residual Value", row=2, col=1)
    fig.update_yaxes(title_text="Count", row=2, col=1)
    fig.update_xaxes(title_text="Residual Value", row=3, col=1)
    fig.update_yaxes(title_text="Count", row=3, col=1)

    stats_data = {
        'Component': ['Bx', 'By', 'Bz'],
        'Mean': [np.mean(residuals_bx), np.mean(residuals_by), np.mean(residuals_bz)],
        'Std Dev': [np.std(residuals_bx), np.std(residuals_by), np.std(residuals_bz)],
        'Min': [np.min(residuals_bx), np.min(residuals_by), np.min(residuals_bz)],
        'Max': [np.max(residuals_bx), np.max(residuals_by), np.max(residuals_bz)]
    }
    
    header_values = list(stats_data.keys())
    cell_values = [list(map(lambda x: f"{x:.4f}" if isinstance(x, (float, np.floating)) else x, stats_data[col])) for col in header_values]

    fig.add_trace(go.Table(
        header=dict(values=header_values, fill_color='paleturquoise', align='left'),
        cells=dict(values=cell_values, fill_color='lavender', align='left')
    ), row=4, col=1)

    fig.update_layout(
        title_text='Magnetic Field Residuals Distribution and Statistics',
        title_x=0.5,
        height=1000,
        showlegend=False
    )
    return fig

def create_3d_field_line_globe(coefficients: np.ndarray, degree: int) -> go.Figure:
    """
    Creates a 3D globe with traced magnetic field lines.
    """
    # Create a sphere to represent the Earth
    u = np.linspace(0, 2 * np.pi, 100)
    v = np.linspace(0, np.pi, 100)
    x = EARTH_RADIUS_KM * np.outer(np.cos(u), np.sin(v))
    y = EARTH_RADIUS_KM * np.outer(np.sin(u), np.sin(v))
    z = EARTH_RADIUS_KM * np.outer(np.ones(np.size(u)), np.cos(v))

    # Load the world map texture
    try:
        # Open the image and ensure it's in RGB format
        img = Image.open("world_map.jpg").convert('RGB')
        
        earth_sphere = go.Surface(
            x=x, y=y, z=z,
            surfacecolor=img.transpose(Image.Transpose.FLIP_TOP_BOTTOM),
            showscale=False,
            hoverinfo='none',
            name='Earth'
        )
    except Exception as e:
        print(f"Warning: Could not load 'world_map.png': {e}. Globe will be colored instead.")
        earth_sphere = go.Surface(
            x=x, y=y, z=z,
            surfacecolor=z, # Color by height as a fallback
            colorscale='Blues',
            showscale=False,
            hoverinfo='none',
            name='Earth'
        )

    fig = go.Figure(data=[earth_sphere])

    # Define seed points for the field lines
    seed_lat = 80  # Start near the pole
    num_lines = 16
    seed_lons = np.linspace(0, 360, num_lines, endpoint=False)

    for i, lon in enumerate(seed_lons):
        # Trace field line forwards (e.g., North to South)
        line_points_fwd = _trace_field_line(seed_lat, lon, coefficients, degree, step_size_km=150)
        # Trace field line backwards (e.g., South to North)
        line_points_bwd = _trace_field_line(seed_lat, lon, coefficients, degree, step_size_km=-150)
        
        # Combine the two halves
        line_points = np.vstack((np.flipud(line_points_bwd), line_points_fwd))

        if line_points.shape[0] > 1:
            lx, ly, lz = line_points[:, 0], line_points[:, 1], line_points[:, 2]
            fig.add_trace(go.Scatter3d(
                x=lx, y=ly, z=lz,
                mode='lines',
                line=dict(color='purple', width=2),
                hoverinfo='none',
                name=f'Field Line', # Keep name the same to group them in legend
                showlegend=(i==0) # Show legend only for the first line
            ))

    fig.update_layout(
        title_text='3D Globe with Magnetic Field Lines',
        title_x=0.5,
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            aspectmode='data'
        ),
        height=800,
        margin={"r":0,"t":50,"l":0,"b":0}
    )

    return fig

def create_declination_map(latitude: np.ndarray, longitude: np.ndarray, declination: np.ndarray) -> go.Figure:
    """
    Creates an interactive 2D map displaying magnetic declination.

    Args:
        latitude (np.ndarray): Array of latitudes in degrees.
        longitude (np.ndarray): Array of longitudes in degrees.
        declination (np.ndarray): Array of magnetic declination values in degrees.

    Returns:
        plotly.graph_objects.Figure: An interactive Plotly 2D map figure.
    """
    if latitude.size == 0 or longitude.size == 0 or declination.size == 0:
        fig = go.Figure()
        fig.update_layout(
            title_text='Magnetic Declination Map: No Data Available',
            title_x=0.5,
            geo=dict(
                scope='world',
                showland=True, landcolor='rgb(243, 243, 243)',
                showocean=True, oceancolor='rgb(100, 150, 200)',
                showcountries=True, countrycolor='rgb(204, 204, 204)',
                showframe=False, showcoastlines=True
            ),
            height=700,
            margin={"r":0,"t":50,"l":0,"b":0}
        )
        return fig

    # Determine a suitable color range for declination (e.g., -30 to +30 degrees)
    # Or dynamically based on data range
    max_abs_declination = np.max(np.abs(declination))
    color_range = max(30, max_abs_declination * 1.1) # Ensure a reasonable range

    scatter_trace = go.Scattergeo(
        lon=longitude,
        lat=latitude,
        mode='markers',
        marker=dict(
            size=8,
            opacity=0.8,
            colorscale='RdBu', # Red-Blue diverging colorscale
            cmin=-color_range,
            cmax=color_range,
            color=declination,
            colorbar=dict(
                title='Declination (°)',
                outlinewidth=0,
                ticks='outside'
            ),
            line=dict(width=0.5, color='white')
        ),
        name='Magnetic Declination',
        hoverinfo='text',
        text=[f"Lat: {lat:.2f}°<br>Lon: {lon:.2f}°<br>Declination: {dec:.2f}°"
              for lat, lon, dec in zip(latitude, longitude, declination)]
    )

    fig = go.Figure(data=[scatter_trace])

    fig.update_layout(
        title_text='Magnetic Declination Map',
        title_x=0.5,
        showlegend=True,
        geo=dict(
            scope='world',
            showland=True,
            landcolor='rgb(243, 243, 243)',
            countrycolor='rgb(204, 204, 204)',
            showocean=True,
            oceancolor='rgb(100, 150, 200)',
            showcountries=True,
            showframe=False,
            showcoastlines=True,
            coastlinecolor='rgb(100, 100, 100)',
            lataxis_showgrid=True,
            lonaxis_showgrid=True,
            lataxis_gridcolor='rgb(150, 150, 150)',
            lonaxis_gridcolor='rgb(150, 150, 150)'
        ),
        height=700,
        margin={"r":0,"t":50,"l":0,"b":0}
    )
    return fig

def _trace_field_line(lat_start_deg: float, lon_start_deg: float, coefficients: np.ndarray, degree: int, step_size_km: float, max_steps: int = 1500) -> np.ndarray:
    """
    Traces a single magnetic field line using numerical integration (Euler method).
    """
    line_points = []
    
    # Start just above the surface
    r_start = EARTH_RADIUS_KM + abs(step_size_km) * 0.1
    
    # Convert start point to Cartesian
    lat_rad = np.deg2rad(lat_start_deg)
    lon_rad = np.deg2rad(lon_start_deg)
    
    x = r_start * np.cos(lat_rad) * np.cos(lon_rad)
    y = r_start * np.cos(lat_rad) * np.sin(lon_rad)
    z = r_start * np.sin(lat_rad)
    
    current_pos_cart = np.array([x, y, z])

    for _ in range(max_steps):
        r_km = np.linalg.norm(current_pos_cart)
        if r_km < EARTH_RADIUS_KM:
            break # Stop if we hit or go inside the Earth

        # Convert Cartesian position back to spherical for field calculation
        lat_rad = np.arcsin(current_pos_cart[2] / r_km)
        lon_rad = np.arctan2(current_pos_cart[1], current_pos_cart[0])
        lat_deg = np.rad2deg(lat_rad)
        lon_deg = np.rad2deg(lon_rad)

        # Get field vector in NED components
        try:
            Bx, By, Bz = get_field_at_point_r(lat_deg, lon_deg, r_km, coefficients, degree)
        except ValueError:
            break # Stop if there's a calculation error

        # Convert NED vector at the point to a Cartesian direction vector
        _, _, _, u, v, w = _spherical_to_cartesian_vectors(
            np.array([lat_deg]), np.array([lon_deg]), 
            np.array([Bx]), np.array([By]), np.array([Bz]), R=1.0
        )
        
        field_vec_cart = np.array([u[0], v[0], w[0]])
        
        norm = np.linalg.norm(field_vec_cart)
        if norm == 0:
            break # Stop if field is zero

        # Normalize the direction vector and take a step
        direction = field_vec_cart / norm
        current_pos_cart = current_pos_cart + direction * step_size_km
        
        line_points.append(current_pos_cart)

    return np.array(line_points)

def save_plot_as_image(figure: go.Figure, file_path: str, format: str = 'png', scale: int = 2) -> None:
    """
    Saves a Plotly figure as a high-resolution image file.

    Args:
        figure (plotly.graph_objects.Figure): The Plotly figure to save.
        file_path (str): The path to save the image file (e.g., 'output.png').
        format (str): The image format ('png', 'jpeg', 'webp', 'svg', 'pdf', 'html').
        scale (int): Scaling factor for resolution (e.g., 2 for 2x resolution).

    Raises:
        IOError: If there is an error writing the image file.
        ValueError: If the format is unsupported or kaleido is not installed.
    """
    try:
        output_dir = os.path.dirname(file_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        pio.write_image(figure, file_path, format=format, scale=scale)
    except Exception as e:
        raise IOError(f"Failed to save plot to {file_path} in {format} format: {e}") from e

def update_3d_globe_realtime(figure: go.Figure, new_data: pd.DataFrame) -> go.Figure:
    """
    Updates an existing 3D globe figure with new real-time measurement points and field vectors.
    Optimized for dynamic updates by modifying existing traces rather than recreating the figure.

    Args:
        figure (plotly.graph_objects.Figure): The existing Plotly 3D globe figure to update.
        new_data (pd.DataFrame): A DataFrame containing the latest real-time data points.
                                 Must contain 'latitude', 'longitude', 'Bx', 'By', 'Bz' columns.

    Returns:
        plotly.graph_objects.Figure: The updated Plotly 3D globe figure.

    Raises:
        ValueError: If new_data is empty or missing required columns.
    """
    if new_data.empty:
        # If no new data, update existing traces with empty arrays to effectively hide them (CQ-VE-001)
        if len(figure.data) > 0 and isinstance(figure.data[0], go.Scattergeo):
            figure.data[0].update(lon=[], lat=[], text=[])
        if len(figure.data) > 1 and isinstance(figure.data[1], go.Cone):
            figure.data[1].update(x=[], y=[], z=[], u=[], v=[], w=[], text=[])
        figure.update_layout(title_text='Real-time 3D Globe: No Data Streaming', showlegend=False)
        return figure

    required_cols = ['latitude', 'longitude', 'Bx', 'By', 'Bz']
    if not all(col in new_data.columns for col in required_cols):
        raise ValueError(f"DataFrame for real-time update must contain {required_cols} columns.")

    latitude = new_data['latitude'].values
    longitude = new_data['longitude'].values
    observed_Bx = new_data['Bx'].values
    observed_By = new_data['By'].values
    observed_Bz = new_data['Bz'].values

    # For real-time, we only have 'observed' data, so modeled vectors are not applicable here
    # We will just plot the observed vectors.
    x_obs, y_obs, z_obs, u_obs, v_obs, w_obs = _spherical_to_cartesian_vectors(
        latitude, longitude, observed_Bx, observed_By, observed_Bz
    )

    # Calculate magnitudes to determine an appropriate sizeref for vectors
    magnitudes_obs = np.linalg.norm(np.column_stack((observed_Bx, observed_By, observed_Bz)), axis=1)
    max_magnitude = np.max(magnitudes_obs) if magnitudes_obs.size > 0 else 0.0

    target_visual_length = 0.1
    dynamic_sizeref = 1.0
    if max_magnitude > 1e-9:
        dynamic_sizeref = max_magnitude / target_visual_length
        dynamic_sizeref = np.clip(dynamic_sizeref, 0.01, 1000.0)

    # Update existing traces or create new ones if they don't exist
    # Trace 0: Scattergeo for points
    # Trace 1: Cone for observed vectors

    if len(figure.data) == 0:
        # If figure is empty, add initial traces
        figure.add_trace(go.Scattergeo(
            lon=longitude, lat=latitude, mode='markers',
            marker=dict(size=8, opacity=0.8, color='blue', line=dict(width=0.5, color='white')),
            name='Real-time Locations', hoverinfo='text',
            text=[f"Lat: {lat:.2f}°<br>Lon: {lon:.2f}°<br>Bx: {bx:.2f}<br>By: {by:.2f}<br>Bz: {bz:.2f}"
                  for lat, lon, bx, by, bz in zip(latitude, longitude, observed_Bx, observed_By, observed_Bz)]
        ))
        figure.add_trace(go.Cone(
            x=x_obs, y=y_obs, z=z_obs,
            u=u_obs, v=v_obs, w=w_obs,
            sizemode="absolute", sizeref=dynamic_sizeref, anchor="tail",
            colorscale=[[0, 'red'], [1, 'red']], showscale=False,
            name='Real-time Vectors', hoverinfo='text',
            text=[f"Bx: {bx:.2f}<br>By: {by:.2f}<br>Bz: {bz:.2f}" for bx, by, bz in zip(observed_Bx, observed_By, observed_Bz)]
        ))
    else:
        # Update existing traces
        figure.data[0].update(
            lon=longitude, lat=latitude,
            text=[f"Lat: {lat:.2f}°<br>Lon: {lon:.2f}°<br>Bx: {bx:.2f}<br>By: {by:.2f}<br>Bz: {bz:.2f}"
                  for lat, lon, bx, by, bz in zip(latitude, longitude, observed_Bx, observed_By, observed_Bz)]
        )
        figure.data[1].update(
            x=x_obs, y=y_obs, z=z_obs,
            u=u_obs, v=v_obs, w=w_obs,
            sizeref=dynamic_sizeref,
            text=[f"Bx: {bx:.2f}<br>By: {by:.2f}<br>Bz: {bz:.2f}" for bx, by, bz in zip(observed_Bx, observed_By, observed_Bz)]
        )

    figure.update_layout(
        title_text='Real-time 3D Globe of Magnetic Field Data',
        title_x=0.5,
        showlegend=True
    )
    return figure

def create_contour_map_field_intensity(coefficients: np.ndarray, degree: int) -> go.Figure:
    """
    Creates an interactive 2D contour map of the total magnetic field intensity.

    Args:
        coefficients (np.ndarray): A 1D array of Gauss coefficients.
        degree (int): The maximum spherical harmonic degree of the model.

    Returns:
        plotly.graph_objects.Figure: An interactive Plotly 2D contour map.
    """
    # 1. Generate a dense grid of latitude/longitude points
    lat_grid = np.linspace(-90, 90, 181)  # 1-degree resolution
    lon_grid = np.linspace(-180, 180, 361) # 1-degree resolution
    lon_mesh, lat_mesh = np.meshgrid(lon_grid, lat_grid)
    
    grid_lat_flat = lat_mesh.flatten()
    grid_lon_flat = lon_mesh.flatten()

    # 2. Calculate total field intensity for each point on the grid
    intensity_values = calculate_total_intensity(grid_lat_flat, grid_lon_flat, coefficients, degree)
    intensity_mesh = intensity_values.reshape(lat_mesh.shape)

    # 3. Create the contour map using Plotly
    contour_trace = go.Contour(
        z=intensity_mesh,
        x=lon_grid,
        y=lat_grid,
        colorscale='Viridis',
        colorbar=dict(title='Field Intensity (nT)'),
        contours=dict(
            coloring='heatmap',
            showlabels=True,
            labelfont=dict(size=10, color='white'),
        ),
        hoverinfo='x+y+z'
    )

    fig = go.Figure(data=[contour_trace])

    # 4. Ensure appropriate geographical context
    fig.update_layout(
        title_text='2D Contour Map of Total Magnetic Field Intensity',
        title_x=0.5,
        xaxis_title='Longitude (°)',
        yaxis_title='Latitude (°)',
        geo=dict(
            showland=True,
            landcolor='rgb(217, 217, 217)',
            subunitcolor='rgb(255, 255, 255)',
            countrycolor='rgb(255, 255, 255)',
            showlakes=True,
            lakecolor='rgb(127, 205, 255)',
            projection_type='natural earth'
        ),
        height=700,
        margin={"r":0,"t":50,"l":0,"b":0}
    )
    
    return fig
import ipywidgets as widgets
from IPython.display import display, HTML
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import os
import io

# Import core modules
from src.data_ingestion import load_data
from src.data_validation import validate_data
from src.spherical_harmonics import compute_basis_functions, reconstruct_field
from src.gauss_fitter import fit_coefficients
from src.visualization_engine import create_3d_globe, add_field_vectors, plot_residuals

class JupyterAnalyzer:
    """
    Manages the interactive analysis workflow within a Jupyter Notebook environment.
    Provides widgets for data loading, parameter control, analysis execution, and result display.
    """
    def __init__(self):
        self.data_df = None
        self.observed_field_components = None  # Nx3 array of Bx, By, Bz
        self.modeled_field_components = None   # Nx3 array of Bx, By, Bz
        self.gauss_coefficients = None
        self.gauss_uncertainties = None
        self.analysis_metrics = {}
        self.current_globe_figure = None
        self.current_residuals_figure = None

        # Widgets for UI
        self.file_upload = widgets.FileUpload(accept='.csv,.xls,.xlsx', multiple=False, description='Upload Data File')
        # Removed: self.file_path_text = widgets.Text(description='Local Path:', placeholder='Or enter local file path...')
        # Removed: self.load_button = widgets.Button(description='Load & Validate Data', button_style='info')
        self.degree_slider = widgets.IntSlider(min=1, max=10, value=2, description='SH Degree (L_max)')
        self.run_analysis_button = widgets.Button(description='Run Analysis', button_style='success')
        self.display_globe_button = widgets.Button(description='Show 3D Globe', button_style='primary')
        self.display_residuals_button = widgets.Button(description='Show Residuals', button_style='primary')
        self.output_area = widgets.Output()

        # Link callbacks to widget events
        self.file_upload.observe(self._on_file_upload_change, names='value')
        # Removed: self.load_button.on_click(self._on_load_button_click)
        self.run_analysis_button.on_click(self._on_run_analysis_click)
        self.display_globe_button.on_click(lambda b: self._display_plot(self.current_globe_figure))
        self.display_residuals_button.on_click(lambda b: self._display_plot(self.current_residuals_figure))

    def _on_file_upload_change(self, change):
        """Handles file upload event, loads and validates the data."""
        with self.output_area:
            self.output_area.clear_output()
            if self.file_upload.value:
                # Assuming single file upload due to multiple=False
                uploaded_file = list(self.file_upload.value.values())[0]
                file_name = uploaded_file['metadata']['name']
                file_content = uploaded_file['content']
                
                file_extension = os.path.splitext(file_name)[1].lower()
                
                try:
                    if file_extension == '.csv':
                        self.data_df = pd.read_csv(io.BytesIO(file_content))
                    elif file_extension in ('.xls', '.xlsx'):
                        self.data_df = pd.read_excel(io.BytesIO(file_content))
                    else:
                        raise ValueError(f"Unsupported uploaded file format: {file_extension}")
                    
                    self._validate_and_store_data()
                    print(f"File '{file_name}' uploaded and loaded successfully.")
                except Exception as e:
                    print(f"Error processing uploaded file: {e}")
                    self.data_df = None
                    self.observed_field_components = None
            else:
                print("No file uploaded.")

    # Removed _on_load_button_click method to prevent arbitrary local file path access

    def _validate_and_store_data(self):
        """Validates the loaded DataFrame and stores observed field components."""
        if self.data_df is not None and not self.data_df.empty:
            is_valid, errors = validate_data(self.data_df) # Use existing data_validation module
            if is_valid:
                display(HTML("Data validation: <span style='color:green; font-weight:bold;'>Valid</span>"))
                # Store observed field components for analysis
                self.observed_field_components = np.column_stack((
                    self.data_df['Bx'].values,
                    self.data_df['By'].values,
                    self.data_df['Bz'].values
                ))
            else:
                display(HTML("Data validation: <span style='color:red; font-weight:bold;'>Invalid</span>"))
                print("Errors:")
                for error in errors:
                    print(f"- {error}")
                self.data_df = None
                self.observed_field_components = None
        else:
            print("No data to validate.")
            self.data_df = None
            self.observed_field_components = None

    def _on_run_analysis_click(self, b):
        """
        Executes the magnetic field analysis pipeline based on current parameters.
        """
        with self.output_area:
            self.output_area.clear_output()
            if self.data_df is None or self.observed_field_components is None:
                print("Please load and validate data first.")
                return

            degree = self.degree_slider.value
            latitude = self.data_df['latitude'].values
            longitude = self.data_df['longitude'].values
            
            try:
                print(f"Running analysis for L_max = {degree}...")
                # 1. Compute Spherical Harmonic Basis Functions
                design_matrix = compute_basis_functions(latitude, longitude, degree)

                # 2. Fit Gauss Coefficients
                # observed_field_components needs to be a 1D array for fit_coefficients
                observed_1d = np.concatenate((
                    self.observed_field_components[:, 0],
                    self.observed_field_components[:, 1],
                    self.observed_field_components[:, 2]
                ))
                self.gauss_coefficients, self.gauss_uncertainties = fit_coefficients(design_matrix, observed_1d)

                # 3. Reconstruct Magnetic Field
                modeled_Bx, modeled_By, modeled_Bz = reconstruct_field(latitude, longitude, self.gauss_coefficients, degree)
                self.modeled_field_components = np.column_stack((modeled_Bx, modeled_By, modeled_Bz))

                # 4. Calculate Residuals and Metrics
                residuals_Bx = self.observed_field_components[:, 0] - modeled_Bx
                residuals_By = self.observed_field_components[:, 1] - modeled_By
                residuals_Bz = self.observed_field_components[:, 2] - modeled_Bz

                rmse_Bx = np.sqrt(np.mean(residuals_Bx**2))
                rmse_By = np.sqrt(np.mean(residuals_By**2))
                rmse_Bz = np.sqrt(np.mean(residuals_Bz**2))
                total_rmse = np.sqrt(np.mean(np.concatenate((residuals_Bx, residuals_By, residuals_Bz))**2))

                self.analysis_metrics = {
                    "RMSE_Bx": rmse_Bx,
                    "RMSE_By": rmse_By,
                    "RMSE_Bz": rmse_Bz,
                    "Total_RMSE": total_rmse
                }

                display(HTML("<span style='color:green; font-weight:bold;'>Analysis completed successfully!</span>"))
                self._display_analysis_results()

                # 5. Generate Visualizations
                self.current_globe_figure = create_3d_globe(self.data_df)
                self.current_globe_figure = add_field_vectors(
                    self.current_globe_figure,
                    latitude, longitude,
                    self.observed_field_components,
                    self.modeled_field_components
                )
                
                self.current_residuals_figure = plot_residuals(
                    self.observed_field_components,
                    self.modeled_field_components
                )
                
                print("Visualizations generated. Use buttons above to view.")

            except ValueError as e:
                print(f"Analysis Error: {e}")
            except Exception as e:
                print(f"An unexpected error occurred during analysis: {e}")

    def _display_analysis_results(self):
        """Displays Gauss coefficients and model metrics in the output area."""
        print("<h3>Gauss Coefficients:</h3>")
        if self.gauss_coefficients is not None:
            coeff_names = self._generate_coeff_names(self.degree_slider.value)
            coeff_data = []
            for i, coeff_value in enumerate(self.gauss_coefficients):
                name = coeff_names[i] if i < len(coeff_names) else f"coeff_{i}"
                uncertainty = self.gauss_uncertainties[i] if self.gauss_uncertainties is not None and i < len(self.gauss_uncertainties) else np.nan
                coeff_data.append([name, f"{coeff_value:.6e}", f"{uncertainty:.6e}"])
            
            coeff_df = pd.DataFrame(coeff_data, columns=['Coefficient', 'Value', 'Uncertainty'])
            display(coeff_df)
        else:
            print("No coefficients available.")

        print("<h3>Model Validation Metrics:</h3>")
        if self.analysis_metrics:
            metrics_text = ""
            for key, value in self.analysis_metrics.items():
                metrics_text += f"{key}: {value:.4f}<br>"
            display(HTML(metrics_text))
        else:
            print("No metrics available.")

    def _display_plot(self, plot_object: go.Figure):
        """Displays a Plotly figure in the output area."""
        with self.output_area:
            self.output_area.clear_output()
            if plot_object:
                display(plot_object)
            else:
                print("No plot available. Run analysis first.")

    def _generate_coeff_names(self, degree: int) -> list[str]:
        """Helper to generate standard Gauss coefficient names (g_l^m, h_l^m)."""
        names = []
        for l in range(1, degree + 1):
            for m in range(l + 1):
                names.append(f"g_{l}^{m}")
                if m > 0:
                    names.append(f"h_{l}^{m}")
        return names

    def create_interactive_ui(self):
        """Assembles and returns the interactive UI for the Jupyter Notebook."""
        file_input_box = widgets.VBox([
            self.file_upload
            # Removed: widgets.HBox([self.file_path_text, self.load_button])
        ])
        
        analysis_controls = widgets.VBox([
            self.degree_slider,
            self.run_analysis_button
        ])

        plot_controls = widgets.HBox([
            self.display_globe_button,
            self.display_residuals_button
        ])

        ui = widgets.VBox([
            widgets.HTML("<h2>Magnetic Field Data Analyzer (Jupyter)</h2>"),
            widgets.HTML("<h3>1. Load Data</h3>"),
            file_input_box,
            widgets.HTML("<h3>2. Configure & Run Analysis</h3>"),
            analysis_controls,
            widgets.HTML("<h3>3. View Results & Visualizations</h3>"),
            plot_controls,
            self.output_area
        ])
        return ui

# API contract function for COMP-008
def create_interactive_controls(parameters: dict) -> widgets.Widget:
    """
    Generates a set of ipywidgets for interactive adjustment of analysis parameters
    and orchestration of the magnetic field analysis workflow.

    Args:
        parameters (dict): A dictionary of initial parameters for widgets, e.g.,
                           {'min_degree': 1, 'max_degree': 5, 'default_degree': 2}.

    Returns:
        ipywidgets.Widget: A VBox widget containing the complete interactive UI.
    """
    analyzer = JupyterAnalyzer()
    # Apply initial parameters if provided
    if 'min_degree' in parameters: analyzer.degree_slider.min = parameters['min_degree']
    if 'max_degree' in parameters: analyzer.degree_slider.max = parameters['max_degree']
    if 'default_degree' in parameters: analyzer.degree_slider.value = parameters['default_degree']
    
    return analyzer.create_interactive_ui()

# API contract function for COMP-008
def display_inline_plot(plot_object: go.Figure):
    """
    Ensures a Plotly figure is rendered directly within the Jupyter Notebook output.

    Args:
        plot_object (plotly.graph_objects.Figure): The Plotly figure to display.
    """
    display(plot_object)

# Architecture of the Earth's Magnetic Field Modeling Application

## High-Level Overview

This project is a desktop application for analyzing the Earth's magnetic field. It features a graphical user interface (GUI) built with PyQt6 and can also be used interactively within a Jupyter Notebook. The application provides the following core functionalities:

-   **Data Ingestion**: Load magnetic field data from CSV or Excel files.
-   **Data Validation**: Validate the data for completeness, correctness, and format.
-   **Spherical Harmonic Analysis**: Model the Earth's magnetic field using spherical harmonics.
-   **Real-time Data Acquisition**: Connect to hardware sensors for real-time data streaming.
-   **Visualization**: Display data and model results on an interactive 3D globe and through residual plots.
-   **Reporting**: Generate comprehensive PDF reports of the analysis.
-   **Data Export**: Export raw and modeled data for further use.

## Core Components

The application is designed with a modular architecture, where each component is responsible for a specific part of the workflow.

### 1. GUI Manager (`gui_manager.py`)

-   **Role**: The main entry point and central orchestrator of the desktop application.
-   **Technology**: PyQt6.
-   **Functionality**:
    -   Constructs the main application window with a tabbed interface for different functionalities (Data Input, Configuration, Analysis, etc.).
    -   Handles user interactions (button clicks, file selection) and triggers the corresponding actions in other modules.
    -   Manages the real-time data acquisition and visualization loop.

### 2. Data Ingestion (`data_ingestion.py`)

-   **Role**: Handles loading data from external files.
-   **Technology**: pandas.
-   **Functionality**:
    -   Loads data from CSV and Excel files into pandas DataFrames.
    -   Provides a single function to handle different file formats.

### 3. Data Validation (`data_validation.py`)

-   **Role**: Ensures the integrity and quality of the input data.
-   **Technology**: pandas.
-   **Functionality**:
    -   Checks for the presence of required columns (latitude, longitude, Bx, By, Bz).
    -   Verifies that the data is within valid ranges (e.g., latitude between -90 and 90).
    -   Detects missing or non-numeric values.

### 4. Spherical Harmonics Engine (`spherical_harmonics.py`)

-   **Role**: Contains the core scientific logic for magnetic field modeling.
-   **Technology**: NumPy, SciPy.
-   **Functionality**:
    -   `compute_basis_functions`: Calculates the spherical harmonic basis functions for the given locations.
    -   `reconstruct_field`: Reconstructs the magnetic field components from the Gauss coefficients.

### 5. Gauss Coefficient Fitter (`gauss_fitter.py`)

-   **Role**: Determines the Gauss coefficients from the observed data.
-   **Technology**: NumPy, SciPy.
-   **Functionality**:
    -   Uses a least-squares fitting algorithm (`scipy.linalg.lstsq`) to solve the linear system that relates the observed magnetic field to the Gauss coefficients.

### 6. Visualization Engine (`visualization_engine.py`)

-   **Role**: Creates interactive visualizations of the data and model results.
-   **Technology**: Plotly.
-   **Functionality**:
    -   `create_3d_globe`: Generates an interactive 3D globe showing the measurement locations.
    -   `add_field_vectors`: Overlays observed and modeled magnetic field vectors on the globe.
    -   `plot_residuals`: Creates histograms and statistical summaries of the model residuals.
    -   `update_3d_globe_realtime`: Updates the 3D globe with real-time data.
    -   `create_3d_field_line_globe`: Generates a 3D plot of magnetic field lines based on Gauss coefficients.
    -   `create_declination_map`: Generates an interactive 2D map displaying magnetic declination.
    -   `create_contour_map_field_intensity`: Generates an interactive 2D contour map of total field intensity.

## Future Visualizations (TODO)

-   **Residuals Map**:
    *   **Goal**: Geographically display the residuals (observed - modeled) to identify areas where the model performs well or poorly.
    *   **Data Source**: Original input data (latitude, longitude) and calculated residuals from `_run_analysis` in `gui_manager.py`.
    *   **Implementation Steps**:
        1.  **`visualization_engine.py`**: Create a `create_residuals_map` function. This function will:
            *   Take latitude, longitude, and residual values (e.g., total residual magnitude or individual component residuals) as input.
            *   Use Plotly's `go.Scattergeo` with color-coded markers (similar to the declination map) to represent the residuals.
            *   Use a diverging color scale (e.g., red for large positive, blue for large negative, white for near zero) if plotting signed residuals, or a sequential scale for residual magnitude.
            *   Ensure interactivity (hover info, zoom, pan) and geographical context.
        2.  **`gui_manager.py`**:
            *   Modify the existing "Show Residuals" button or add a new one for the geographical residuals map.
            *   Implement a `_show_geographical_residuals_map` method (or extend the existing `_display_residuals_plot` if appropriate) to pass the necessary data to the new visualization function.
            *   Add a `QWebEngineView` if a separate view is desired, or reuse an existing one.
        3.  **`architecture.md`**: Update `Visualization Engine` functionality to include `create_residuals_map`.
        4.  **`docs/user_guide.rst`**: Add instructions for using the new visualization.


### 7. Report Generator (`report_generator.py`)

-   **Role**: Creates PDF reports of the analysis results.
-   **Technology**: ReportLab.
-   **Functionality**:
    -   Generates a structured PDF document containing:
        -   Gauss coefficients and their uncertainties.
        -   Model validation metrics.
        -   Embedded plots (3D globe and residual plots).

### 8. Configuration Manager (`config_manager.py`)

-   **Role**: Manages application settings.
-   **Functionality**:
    -   Loads and saves application configuration from/to a JSON file.
    -   Stores settings like the default data directory and the last used file.

### 9. Error Handling (`error_handling.py`)

-   **Role**: Provides a centralized mechanism for handling and logging errors.
-   **Functionality**:
    -   Logs exceptions to the console.
    -   Displays user-friendly error messages in the GUI.

### 10. Jupyter Integration (`jupyter_integration.py`)

-   **Role**: Enables the use of the analysis workflow within a Jupyter Notebook.
-   **Technology**: ipywidgets.
-   **Functionality**:
    -   Provides a `JupyterAnalyzer` class that creates interactive widgets for data loading, parameter selection, and analysis execution.

### 11. Hardware Integration & Real-time Processing

-   **`hardware_integration.py`**: Manages the serial connection to external sensors.
-   **`realtime_data_processor.py`**: Parses and validates the raw data stream from the hardware.
-   **`realtime_data_buffer.py`**: A rolling buffer that stores the most recent real-time data points.
-   **`realtime_worker.py`**: A `QThread` that runs in the background to continuously read data from the hardware without blocking the GUI.

### 12. Data Export (`data_export.py`)

-   **Role**: Exports data for external use.
-   **Technology**: pandas.
-   **Functionality**:
    -   Saves the original data along with the modeled magnetic field components to a CSV file.

### 13. Testing (`testing_module.py`)

-   **Role**: Contains unit tests for the core components.
-   **Technology**: pytest.
-   **Functionality**:
    -   Provides a suite of tests to verify the correctness of the mathematical and data processing modules.

## Data Flow

1.  **Data Loading**: The user selects a file through the GUI (`gui_manager.py`). The `data_ingestion.py` module loads the data into a pandas DataFrame.
2.  **Data Validation**: The loaded DataFrame is passed to `data_validation.py` to check for errors. The results are displayed in the GUI.
3.  **Analysis**:
    -   The user specifies the desired spherical harmonic degree in the GUI.
    -   `gui_manager.py` orchestrates the analysis by calling the following modules in sequence:
        1.  `spherical_harmonics.py` to compute the design matrix.
        2.  `gauss_fitter.py` to calculate the Gauss coefficients.
        3.  `spherical_harmonics.py` again to reconstruct the magnetic field based on the fitted coefficients.
4.  **Visualization**:
    -   The results of the analysis are passed to `visualization_engine.py`.
    -   A 3D globe with measurement locations and field vectors is generated.
    -   A plot of the residuals (the difference between observed and modeled data) is also created.
    -   These plots are displayed in the "Visualization" tab of the GUI.
5.  **Results Display**: The calculated Gauss coefficients and model performance metrics are displayed in the "Results" tab.
6.  **Report Generation**: If requested, `report_generator.py` is called to create a PDF report summarizing the analysis.
7.  **Real-time Data Flow**:
    -   The user connects to a hardware sensor through the GUI.
    -   `hardware_integration.py` establishes the serial connection.
    -   `realtime_worker.py` starts a background thread that continuously reads data from the sensor.
    -   The raw data is processed by `realtime_data_processor.py` and stored in `realtime_data_buffer.py`.
    -   A timer in `gui_manager.py` periodically retrieves data from the buffer and updates the real-time 3D globe visualization.

## Integration of Visualizations (TODO)

To ensure all generated visualizations are available in reports and interactive environments, the following integrations are planned:

-   **PDF Report Integration (`report_generator.py`, `gui_manager.py`):**
    *   **Goal**: Include all relevant generated Plotly figures (3D Globe, Residuals, 3D Field Lines, Magnetic Declination Map, 2D Contour Map, Geographical Residuals Map) in the PDF report.
    *   **Implementation Steps (`gui_manager.py` -> `_generate_report` method):**
        1.  Modify the `_generate_report` method to check for the existence of `self.current_globe_figure`, `self.current_residuals_figure`, `self.current_field_line_figure`, `self.declination_map_figure`, and any future visualization figures (e.g., `self.field_intensity_map_figure`, `self.geographical_residuals_map_figure`).
        2.  For each existing figure, convert it to an image format (e.g., PNG using `pio.to_image`) and append it to the `plots_to_embed` list.
        3.  Ensure appropriate titles or labels are passed to the `report_generator.py` to identify each plot in the PDF.

-   **Jupyter Notebook Integration (`jupyter_integration.py`):**
    *   **Goal**: Enable generation and interactive display of all visualizations within the Jupyter Notebook environment.
    *   **Implementation Steps (`jupyter_integration.py` -> `JupyterAnalyzer` class):**
        1.  **`__init__` method**:
            *   Add instance variables for all visualization figures: `self.current_field_line_figure = None`, `self.current_declination_map_figure = None`, and placeholders for future figures (e.g., `self.current_field_intensity_map_figure = None`, `self.current_geographical_residuals_map_figure = None`).
        2.  **`_on_run_analysis_click` method**:
            *   After calculating Gauss coefficients and reconstructing the field, call the respective `create_...` functions from `visualization_engine.py` to generate all visualization figures (e.g., `create_3d_field_line_globe`, `create_declination_map`, etc.).
            *   Assign the generated figures to their respective instance variables (e.g., `self.current_field_line_figure = create_3d_field_line_globe(...)`).
        3.  **`create_interactive_ui` method**:
            *   Add new `widgets.Button` instances for each new visualization (e.g., `self.display_field_lines_button`, `self.display_declination_map_button`).
            *   Connect these buttons to the `_display_plot` method, passing the corresponding figure instance (e.g., `self.display_field_lines_button.on_click(lambda b: self._display_plot(self.current_field_line_figure))`).
            *   Organize these new buttons within the `plot_controls` layout.
        4.  **Imports**: Update the import statement from `src.visualization_engine` to include all new visualization creation functions.
        5.  **`_display_plot` method**: This method should already handle displaying any `go.Figure` object, so no changes are expected here.

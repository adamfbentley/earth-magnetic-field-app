User Guide
==========

Introduction
------------
The Magnetic Field Data Analyzer is a powerful tool designed for scientists and researchers to process, analyze, and visualize magnetic field data. It supports data ingestion from common formats (CSV, Excel), performs spherical harmonic analysis to fit Gauss coefficients, reconstructs magnetic fields, and generates interactive 3D visualizations and comprehensive reports.

Installation
------------
To install the Magnetic Field Data Analyzer and its dependencies, it is recommended to use a Python virtual environment.

1.  **Create a virtual environment (optional but recommended):**

    .. code-block:: bash

        python -m venv venv
        source venv/bin/activate  # On Windows: `venv\Scripts\activate`

2.  **Install dependencies:**

    .. code-block:: bash

        pip install -r requirements.txt

    (Note: A `requirements.txt` file is not explicitly part of this sprint, but it's good practice. The required dependencies are listed in the blueprint.)

Usage (GUI Application)
-----------------------
The primary interface for the Magnetic Field Data Analyzer is a PyQt6-based desktop application.

1.  **Start the application:**

    .. code-block:: bash

        python -m src.gui_manager

2.  **Data Input Tab:**
    *   Use the "Browse..." button to select your magnetic field data file (CSV or Excel).
    *   Click "Load & Validate Data" to load the selected file and perform initial data validation.
    *   A preview of your data will appear in the table, and validation status/errors will be displayed.

3.  **Analysis Tab:**
    *   Set the "Max Spherical Harmonic Degree (L_max)" using the spinbox. This determines the complexity of the magnetic field model.
    *   Click "Run Magnetic Field Analysis" to compute Gauss coefficients, reconstruct the field, and calculate model metrics.

4.  **Visualization Tab:**
    *   After running the analysis, use the "Show 3D Globe", "Show Residuals", "Show Field Lines", and "Show Declination Map" buttons to switch between interactive plots.
    *   The 3D Globe displays measurement locations and overlays observed/modeled magnetic field vectors.
    *   The Residuals plot shows histograms and statistics of the differences between observed and modeled field components.
    *   The Field Lines plot visualizes the magnetic field lines in 3D space.
    *   The Magnetic Declination Map displays the angle between magnetic north and true north across the globe, with a color scale indicating declination values.
    *   The Field Intensity Map displays a 2D contour map of the total magnetic field intensity across the globe.
    *   Use the "Save Current Plot as Image..." button to export the currently displayed plot to various image formats (PNG, JPEG, SVG, PDF).

5.  **Results Tab:**
    *   View the calculated Gauss coefficients and their uncertainties in a table.
    *   Review model validation metrics (e.g., RMSE) in the text area.
    *   Click "Generate PDF Report..." to create a comprehensive PDF document containing all analysis results and embedded plots.

6.  **Configuration Tab:**
    *   Set a "Default Data Directory" for easier file browsing.
    *   Set a "Default Spherical Harmonic Degree (L_max)" for analysis.
    *   Click "Save Configuration" to persist these settings for future sessions.

7.  **Real-time Data Acquisition Tab:**
    *   **Connect to Device**: Select the serial port of your hardware sensor from the dropdown menu and click "Connect".
    *   **Start Acquisition**: Once connected, click "Start Real-time Acquisition" to begin streaming data from the sensor.
    *   **Real-time Visualization**: The 3D globe in the "Visualization" tab will update in real-time with the incoming sensor data.
    *   **Stop Acquisition**: Click "Stop Real-time Acquisition" to halt data streaming.
    *   **Disconnect**: Click "Disconnect" to close the serial connection to the device.

Usage (Jupyter Notebook)
------------------------
For interactive exploration and scripting, the analyzer can also be used within a Jupyter Notebook environment.

1.  **Start Jupyter Lab/Notebook:**

    .. code-block:: bash

        jupyter lab

2.  **Open `notebooks/magnetic_field_analysis.ipynb`:**
    *   Navigate to the `notebooks` directory and open the provided notebook.
    *   Ensure the `src` directory is added to your Python path (the notebook handles this automatically).

3.  **Interactive Controls:**
    *   Use the `FileUpload` widget to upload your data file.
    *   Adjust the "SH Degree (L_max)" slider.
    *   Click "Run Analysis" to execute the analysis pipeline.
    *   Use the "Show 3D Globe" and "Show Residuals" buttons to display plots inline.

4.  **Review Output:**
    *   Analysis progress, results, and interactive Plotly figures will be displayed directly in the notebook output cells.

Example Workflow
----------------
1.  **Load Data:** Start the GUI application. In the "Data Input" tab, click "Browse..." and select your magnetic field data file (e.g., `sample_data.csv`). Click "Load & Validate Data".
2.  **Configure Analysis:** Switch to the "Analysis" tab. Set the "Max Spherical Harmonic Degree (L_max)" to `2`.
3.  **Run Analysis:** Click "Run Magnetic Field Analysis". A confirmation message will appear upon completion.
4.  **View Results:** The application will automatically switch to the "Results" tab, displaying the calculated Gauss coefficients and model metrics.
5.  **Visualize:** Switch to the "Visualization" tab. Click "Show 3D Globe" to see measurement points and field vectors. Click "Show Residuals" to view residual histograms.
6.  **Export Data:** Go back to the "Data Input" tab and click "Export Data (CSV)" to save the original and modeled data.
7.  **Generate Report:** In the "Results" tab, click "Generate PDF Report..." to create a summary PDF.

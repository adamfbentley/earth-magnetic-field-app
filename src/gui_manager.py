import sys
import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QFileDialog, QTabWidget,
    QTableWidget, QTableWidgetItem, QTextEdit, QHeaderView, QMessageBox, QSpinBox, QStackedWidget, QComboBox
)
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal, QTimer
from PyQt6.QtWebEngineWidgets import QWebEngineView

# Import core modules
from src.data_ingestion import load_data
from src.data_validation import validate_data
from src.error_handling import handle_error
from src.config_manager import load_config, save_config
from src.spherical_harmonics import compute_basis_functions, reconstruct_field, calculate_declination
from src.gauss_fitter import fit_coefficients
from src.visualization_engine import create_3d_globe, add_field_vectors, plot_residuals, save_plot_as_image, update_3d_globe_realtime, create_3d_field_line_globe, create_declination_map, create_contour_map_field_intensity
from src.report_generator import generate_pdf_report
from src.data_export import export_magnetic_field_data
from src.hardware_integration import HardwareIntegration
from src.realtime_data_processor import parse_raw_data, validate_realtime_point
from src.realtime_data_buffer import RealtimeDataBuffer
from src.realtime_worker import RealtimeWorker

class MainWindow(QMainWindow):
    """
    Main application window for the Magnetic Field Data Analyzer.
    Manages the PyQt6 main application window, tabbed interface, and user interactions,
    orchestrating calls to core modules (COMP-007).
    """
    _CONFIG_FILE_NAME = "config.json"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Magnetic Field Data Analyzer")
        self.setGeometry(100, 100, 1200, 800)

        self.data_dataframe = None
        self.gauss_coefficients = None
        self.gauss_uncertainties = None
        self.modeled_field_components = None # (Bx, By, Bz) stacked
        self.observed_field_components = None # (Bx, By, Bz) stacked
        self.analysis_metrics = {}

        self.current_globe_figure = None
        self.current_residuals_figure = None
        self.current_field_line_figure = None
        self.declination_map_figure = None # New figure for declination map
        self.field_intensity_map_figure = None # New figure for field intensity map
        self.field_intensity_map_figure = None # New figure for field intensity map
        self.realtime_globe_figure = None # Dedicated figure for real-time updates

        # Real-time components
        self.hardware_integration = HardwareIntegration()
        self.realtime_data_buffer = RealtimeDataBuffer(max_size=500) # Buffer for 500 points
        self.realtime_worker = RealtimeWorker(self.hardware_integration, self.realtime_data_buffer)
        self.realtime_update_timer = QTimer(self)
        self.realtime_update_interval_ms = 100 # Update GUI every 100 ms

        self._init_ui()
        self._load_initial_config()
        self._init_realtime_connections()

    def _init_ui(self):
        """Initializes and displays the main PyQt6 application window with menu and tabs."""
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)

        self._create_data_input_tab()
        self._create_configuration_tab()
        self._create_analysis_tab()
        self._create_visualization_tab()
        self._create_results_tab()
        self._create_realtime_tab() # New real-time tab

    def _create_data_input_tab(self):
        """Creates the 'Data Input' tab for file loading and data preview."""
        self.data_input_tab = QWidget()
        self.tab_widget.addTab(self.data_input_tab, "Data Input")
        
        layout = QVBoxLayout(self.data_input_tab)

        file_selection_layout = QHBoxLayout()
        self.file_path_line_edit = QLineEdit()
        self.file_path_line_edit.setPlaceholderText("Select CSV or Excel file...")
        self.file_path_line_edit.setReadOnly(True)
        file_selection_layout.addWidget(self.file_path_line_edit)

        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self._browse_file)
        file_selection_layout.addWidget(self.browse_button)

        self.load_data_button = QPushButton("Load & Validate Data")
        self.load_data_button.clicked.connect(self._load_and_validate_data)
        file_selection_layout.addWidget(self.load_data_button)
        
        layout.addLayout(file_selection_layout)

        self.data_preview_table = QTableWidget()
        self.data_preview_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(QLabel("Data Preview:"))
        layout.addWidget(self.data_preview_table)

        self.validation_status_label = QLabel("Validation Status: Not loaded")
        self.validation_status_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.validation_status_label)

        self.validation_errors_text = QTextEdit()
        self.validation_errors_text.setReadOnly(True)
        self.validation_errors_text.setPlaceholderText("Validation errors will appear here.")
        self.validation_errors_text.setFixedHeight(100)
        layout.addWidget(QLabel("Validation Details:"))
        layout.addWidget(self.validation_errors_text)

        export_layout = QHBoxLayout()
        export_layout.addStretch(1)
        self.export_data_button = QPushButton("Export Data (CSV)")
        self.export_data_button.clicked.connect(self._export_data)
        export_layout.addWidget(self.export_data_button)
        layout.addLayout(export_layout)

    def _create_configuration_tab(self):
        """Creates the 'Configuration' tab with UI elements for application settings."""
        self.config_tab = QWidget()
        self.tab_widget.addTab(self.config_tab, "Configuration")
        layout = QVBoxLayout(self.config_tab)

        default_dir_layout = QHBoxLayout()
        default_dir_layout.addWidget(QLabel("Default Data Directory:"))
        self.default_data_dir_line_edit = QLineEdit()
        self.default_data_dir_line_edit.setPlaceholderText("e.g., /path/to/data")
        default_dir_layout.addWidget(self.default_data_dir_line_edit)
        self.browse_default_dir_button = QPushButton("Browse...")
        self.browse_default_dir_button.clicked.connect(self._browse_default_data_directory)
        default_dir_layout.addWidget(self.browse_default_dir_button)
        layout.addLayout(default_dir_layout)

        default_lmax_layout = QHBoxLayout()
        default_lmax_layout.addWidget(QLabel("Default Spherical Harmonic Degree (L_max):"))
        self.default_lmax_spinbox = QSpinBox()
        self.default_lmax_spinbox.setMinimum(1)
        self.default_lmax_spinbox.setMaximum(10)
        self.default_lmax_spinbox.setValue(2)
        default_lmax_layout.addWidget(self.default_lmax_spinbox)
        default_lmax_layout.addStretch(1)
        layout.addLayout(default_lmax_layout)

        self.save_config_button = QPushButton("Save Configuration")
        self.save_config_button.clicked.connect(self._save_current_config)
        layout.addWidget(self.save_config_button)

        layout.addStretch(1)

    def _create_analysis_tab(self):
        """Creates the 'Analysis' tab."""
        self.analysis_tab = QWidget()
        self.tab_widget.addTab(self.analysis_tab, "Analysis")
        layout = QVBoxLayout(self.analysis_tab)

        degree_layout = QHBoxLayout()
        degree_layout.addWidget(QLabel("Max Spherical Harmonic Degree (L_max):"))
        self.degree_spinbox = QSpinBox()
        self.degree_spinbox.setMinimum(1)
        self.degree_spinbox.setMaximum(10)
        self.degree_spinbox.setValue(2)
        degree_layout.addWidget(self.degree_spinbox)
        degree_layout.addStretch(1)
        layout.addLayout(degree_layout)

        self.run_analysis_button = QPushButton("Run Magnetic Field Analysis")
        self.run_analysis_button.clicked.connect(self._run_analysis)
        layout.addWidget(self.run_analysis_button)

        layout.addStretch(1)

    def _create_visualization_tab(self):
        """
        Creates the 'Visualization' tab and embeds a QWebEngineView for Plotly figures.
        """
        self.visualization_tab = QWidget()
        self.tab_widget.addTab(self.visualization_tab, "Visualization")
        layout = QVBoxLayout(self.visualization_tab)

        viz_control_layout = QHBoxLayout()
        self.show_globe_button = QPushButton("Show 3D Globe")
        self.show_globe_button.clicked.connect(lambda: self.display_visualization(self.current_globe_figure))
        viz_control_layout.addWidget(self.show_globe_button)

        self.show_residuals_button = QPushButton("Show Residuals")
        self.show_residuals_button.clicked.connect(lambda: self._display_residuals_plot(self.current_residuals_figure))
        viz_control_layout.addWidget(self.show_residuals_button)

        self.show_field_lines_button = QPushButton("Show Field Lines")
        self.show_field_lines_button.clicked.connect(self._show_field_line_plot)
        viz_control_layout.addWidget(self.show_field_lines_button)

        self.show_declination_map_button = QPushButton("Show Declination Map")
        self.show_declination_map_button.clicked.connect(self._show_declination_map)
        viz_control_layout.addWidget(self.show_declination_map_button)

        self.show_field_intensity_map_button = QPushButton("Show Field Intensity Map")
        self.show_field_intensity_map_button.clicked.connect(self._show_field_intensity_map)
        viz_control_layout.addWidget(self.show_field_intensity_map_button)

        viz_control_layout.addStretch(1)

        self.save_plot_button = QPushButton("Save Current Plot as Image...")
        self.save_plot_button.clicked.connect(self._save_current_plot)
        viz_control_layout.addWidget(self.save_plot_button)

        layout.addLayout(viz_control_layout)

        self.visualization_stack = QStackedWidget()
        self.globe_view = QWebEngineView()
        self.residuals_view = QWebEngineView()
        self.field_line_view = QWebEngineView()
        self.declination_map_view = QWebEngineView() # New view for declination map
        self.field_intensity_map_view = QWebEngineView() # New view for field intensity
        self.visualization_stack.addWidget(self.globe_view)
        self.visualization_stack.addWidget(self.residuals_view)
        self.visualization_stack.addWidget(self.field_line_view)
        self.visualization_stack.addWidget(self.declination_map_view) # Add new view to stack
        self.visualization_stack.addWidget(self.field_intensity_map_view)
        layout.addWidget(self.visualization_stack)

    def _create_results_tab(self):
        """Creates the 'Results' tab with widgets for displaying coefficients and metrics."""
        self.results_tab = QWidget()
        self.tab_widget.addTab(self.results_tab, "Results")
        layout = QVBoxLayout(self.results_tab)

        layout.addWidget(QLabel("Gauss Coefficients:"))
        self.coefficients_table = QTableWidget()
        self.coefficients_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.coefficients_table.setColumnCount(3)
        self.coefficients_table.setHorizontalHeaderLabels(["Coefficient", "Value", "Uncertainty"])
        self.coefficients_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.coefficients_table)

        layout.addWidget(QLabel("Model Metrics:"))
        self.metrics_text_edit = QTextEdit()
        self.metrics_text_edit.setReadOnly(True)
        self.metrics_text_edit.setPlaceholderText("Model validation metrics will appear here.")
        self.metrics_text_edit.setFixedHeight(150)
        layout.addWidget(self.metrics_text_edit)

        report_layout = QHBoxLayout()
        report_layout.addStretch(1)
        self.generate_report_button = QPushButton("Generate PDF Report...")
        self.generate_report_button.clicked.connect(self._generate_report)
        report_layout.addWidget(self.generate_report_button)
        layout.addLayout(report_layout)

        layout.addStretch(1)

    def _create_realtime_tab(self):
        """
        Creates the 'Real-time Data' tab for hardware connection and real-time visualization.
        Implements init_realtime_controls() API contract.
        """
        self.realtime_tab = QWidget()
        self.tab_widget.addTab(self.realtime_tab, "Real-time Data")
        layout = QVBoxLayout(self.realtime_tab)

        # Connection Controls
        connection_group_layout = QVBoxLayout()
        connection_group_layout.addWidget(QLabel("<b>Serial Connection:</b>"))

        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Port:"))
        self.serial_port_combo = QComboBox()
        self.serial_port_combo.setEditable(True)
        # Populate with common ports or last used - REMOVED HARDCODED ENTRIES (CQ-GM-001)
        port_layout.addWidget(self.serial_port_combo)
        self.refresh_ports_button = QPushButton("Refresh Ports")
        self.refresh_ports_button.clicked.connect(self._refresh_serial_ports)
        port_layout.addWidget(self.refresh_ports_button)
        connection_group_layout.addLayout(port_layout)

        baud_rate_layout = QHBoxLayout()
        baud_rate_layout.addWidget(QLabel("Baud Rate:"))
        self.baud_rate_spinbox = QSpinBox()
        self.baud_rate_spinbox.setRange(9600, 115200)
        self.baud_rate_spinbox.setValue(9600)
        baud_rate_layout.addWidget(self.baud_rate_spinbox)
        baud_rate_layout.addStretch(1)
        connection_group_layout.addLayout(baud_rate_layout)

        connect_buttons_layout = QHBoxLayout()
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self._connect_serial)
        connect_buttons_layout.addWidget(self.connect_button)

        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.clicked.connect(self._disconnect_serial)
        self.disconnect_button.setEnabled(False)
        connect_buttons_layout.addWidget(self.disconnect_button)
        connection_group_layout.addLayout(connect_buttons_layout)

        self.connection_status_label = QLabel("Status: Disconnected")
        self.connection_status_label.setStyleSheet("color: red;")
        connection_group_layout.addWidget(self.connection_status_label)
        layout.addLayout(connection_group_layout)
        layout.addSpacing(20)

        # Stream Controls
        stream_group_layout = QVBoxLayout()
        stream_group_layout.addWidget(QLabel("<b>Real-time Stream:</b>"))

        stream_buttons_layout = QHBoxLayout()
        self.start_stream_button = QPushButton("Start Stream")
        self.start_stream_button.clicked.connect(self._start_realtime_stream)
        self.start_stream_button.setEnabled(False)
        stream_buttons_layout.addWidget(self.start_stream_button)

        self.stop_stream_button = QPushButton("Stop Stream")
        self.stop_stream_button.clicked.connect(self._stop_realtime_stream)
        self.stop_stream_button.setEnabled(False)
        stream_buttons_layout.addWidget(self.stop_stream_button)
        stream_group_layout.addLayout(stream_buttons_layout)

        self.stream_status_label = QLabel("Stream: Stopped")
        self.stream_status_label.setStyleSheet("color: gray;")
        stream_group_layout.addWidget(self.stream_status_label)
        layout.addLayout(stream_group_layout)
        layout.addSpacing(20)

        # Real-time Visualization
        layout.addWidget(QLabel("<b>Real-time 3D Globe:</b>"))
        self.realtime_web_view = QWebEngineView()
        layout.addWidget(self.realtime_web_view)

        layout.addStretch(1)
        self._refresh_serial_ports()

    def _init_realtime_connections(self):
        """
        Initializes connections for the real-time worker thread and GUI update timer.
        """
        self.realtime_worker.error_signal.connect(self._handle_realtime_error)
        self.realtime_worker.status_signal.connect(self._update_realtime_status)
        # Removed data_received_signal connection (CQ-GM-002)

        self.realtime_update_timer.timeout.connect(self._update_realtime_visualization)
        self.realtime_update_timer.start(self.realtime_update_interval_ms)

    def _refresh_serial_ports(self):
        """
        Populates the serial port combo box with available ports.
        """
        from serial.tools import list_ports
        ports = [p.device for p in list_ports.comports()]
        self.serial_port_combo.clear()
        if ports:
            self.serial_port_combo.addItems(ports)
        else:
            self.serial_port_combo.addItem("No ports found")
            self.serial_port_combo.setEnabled(False)
        self.connect_button.setEnabled(len(ports) > 0)

    def _connect_serial(self):
        """
        Connects to the selected serial device.
        """
        port = self.serial_port_combo.currentText()
        baud_rate = self.baud_rate_spinbox.value()

        if not port or port == "No ports found":
            QMessageBox.warning(self, "Connection Error", "Please select a valid serial port.")
            return

        if self.hardware_integration.connect_device(port, baud_rate):
            self.connection_status_label.setText(f"Status: Connected to {port}")
            self.connection_status_label.setStyleSheet("color: green;")
            self.connect_button.setEnabled(False)
            self.disconnect_button.setEnabled(True)
            self.start_stream_button.setEnabled(True)
            QMessageBox.information(self, "Connection Success", f"Successfully connected to {port}.")
        else:
            self.connection_status_label.setText("Status: Connection Failed")
            self.connection_status_label.setStyleSheet("color: red;")
            self.connect_button.setEnabled(True)
            self.disconnect_button.setEnabled(False)
            self.start_stream_button.setEnabled(False)

    def _disconnect_serial(self):
        """
        Disconnects from the serial device and stops the real-time stream if active.
        """
        if self.realtime_worker.isRunning():
            self._stop_realtime_stream()

        self.hardware_integration.disconnect_device()
        self.connection_status_label.setText("Status: Disconnected")
        self.connection_status_label.setStyleSheet("color: red;")
        self.connect_button.setEnabled(True)
        self.disconnect_button.setEnabled(False)
        self.start_stream_button.setEnabled(False)
        QMessageBox.information(self, "Disconnection Success", "Disconnected from serial device.")

    def _start_realtime_stream(self):
        """
        Starts the real-time data acquisition thread.
        """
        if not self.hardware_integration.is_connected():
            QMessageBox.warning(self, "Stream Error", "Not connected to a serial device. Please connect first.")
            return
        
        if not self.realtime_worker.isRunning():
            self.realtime_data_buffer.clear_buffer() # Clear buffer on new stream start
            self.realtime_worker.start_streaming()
            self.stream_status_label.setText("Stream: Running")
            self.stream_status_label.setStyleSheet("color: green;")
            self.start_stream_button.setEnabled(False)
            self.stop_stream_button.setEnabled(True)
            # Initialize the real-time globe figure if it's the first time or cleared
            if self.realtime_globe_figure is None:
                self.realtime_globe_figure = create_3d_globe(pd.DataFrame({'latitude': [], 'longitude': []}))
            # Force an update to display the initial empty state or current data
            self._update_realtime_visualization()
            QMessageBox.information(self, "Stream Started", "Real-time data stream started.")

    def _stop_realtime_stream(self):
        """
        Stops the real-time data acquisition thread.
        """
        if self.realtime_worker.isRunning():
            self.realtime_worker.stop_streaming()
            self.realtime_worker.wait() # Wait for the thread to finish
            self.stream_status_label.setText("Stream: Stopped")
            self.stream_status_label.setStyleSheet("color: red;")
            self.start_stream_button.setEnabled(True)
            self.stop_stream_button.setEnabled(False)
            # Force an update to display the 'stopped' state
            self._update_realtime_visualization()
            QMessageBox.information(self, "Stream Stopped", "Real-time data stream stopped.")

    # Removed _handle_realtime_data method (CQ-GM-002)

    def _handle_realtime_error(self, exception: Exception, message: str):
        """
        Slot to handle errors from the RealtimeWorker.
        """
        handle_error(exception, f"Real-time data error: {message}")
        self._stop_realtime_stream()
        self.connection_status_label.setText("Status: Error")
        self.connection_status_label.setStyleSheet("color: red;")

    def _update_realtime_status(self, status_message: str):
        """
        Slot to update real-time status messages from the RealtimeWorker. (CQ-GM-003)
        """
        # Update a dedicated status label with the message from the worker
        self.stream_status_label.setText(f"Stream: {status_message}")
        # Color can be managed by start/stop methods or based on message content if more states are introduced

    def _update_realtime_visualization(self):
        """
        Periodically fetches data from the buffer and updates the real-time globe visualization.
        Implements update_realtime_display() API contract.
        (Refined for CQ-VE-001 consistency)
        """
        # Always ensure realtime_globe_figure is initialized
        if self.realtime_globe_figure is None:
            # Initialize with an empty DataFrame to get the 'No Data Available' state
            self.realtime_globe_figure = create_3d_globe(pd.DataFrame({'latitude': [], 'longitude': []}))
            # Display it once
            self.realtime_web_view.setHtml(self.realtime_globe_figure.to_html(include_plotlyjs='cdn'))

        current_realtime_df = pd.DataFrame({'latitude': [], 'longitude': [], 'Bx': [], 'By': [], 'Bz': []})
        if self.realtime_worker.isRunning() and self.realtime_data_buffer.buffer:
            # Only get data if worker is running and buffer has data
            temp_df = self.realtime_data_buffer.get_current_data()
            if not temp_df.empty:
                current_realtime_df = temp_df
        
        # Always call update_3d_globe_realtime, it will handle empty data gracefully
        self.realtime_globe_figure = update_3d_globe_realtime(
            self.realtime_globe_figure,
            current_realtime_df
        )
        self.realtime_web_view.setHtml(self.realtime_globe_figure.to_html(include_plotlyjs='cdn'))

    def _browse_file(self):
        """
        Opens a file dialog to select a CSV or Excel file.
        """
        initial_dir = self.default_data_dir_line_edit.text() if os.path.isdir(self.default_data_dir_line_edit.text()) else os.getcwd()
        file_dialog = QFileDialog(self, "Select Data File", initial_dir)
        file_dialog.setNameFilter("Data Files (*.csv *.xls *.xlsx)")
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)

        if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
            selected_file = file_dialog.selectedFiles()[0]
            self.file_path_line_edit.setText(selected_file)
            self._load_and_validate_data()

    def _browse_default_data_directory(self):
        """
        Opens a directory dialog to select the default data directory.
        """
        initial_dir = self.default_data_dir_line_edit.text() if os.path.isdir(self.default_data_dir_line_edit.text()) else os.getcwd()
        dir_dialog = QFileDialog(self, "Select Default Data Directory", initial_dir)
        dir_dialog.setFileMode(QFileDialog.FileMode.Directory)
        dir_dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)

        if dir_dialog.exec() == QFileDialog.DialogCode.Accepted:
            selected_dir = dir_dialog.selectedFiles()[0]
            self.default_data_dir_line_edit.setText(selected_dir)

    def _load_and_validate_data(self):
        """
        Loads data from the selected file, validates it, and updates the GUI.
        Orchestrates calls to COMP-001 (data_ingestion) and COMP-002 (data_validation).
        """
        file_path = self.file_path_line_edit.text()
        if not file_path:
            QMessageBox.warning(self, "No File Selected", "Please select a data file first to load and validate.")
            self.data_dataframe = None
            self.update_data_preview(pd.DataFrame())
            self.validation_status_label.setText("Validation Status: No file selected")
            self.validation_status_label.setStyleSheet("font-weight: bold; color: gray;")
            self.validation_errors_text.clear()
            return

        try:
            self.data_dataframe = load_data(file_path)
            self.update_data_preview(self.data_dataframe)

            is_valid, errors = validate_data(self.data_dataframe)

            if is_valid:
                self.validation_status_label.setText("Validation Status: <font color='green'>Valid</font>")
                self.validation_status_label.setStyleSheet("font-weight: bold; color: green;")
                self.validation_errors_text.setText("Data is valid. No issues found.")
                self.observed_field_components = np.column_stack((
                    self.data_dataframe['Bx'].values,
                    self.data_dataframe['By'].values,
                    self.data_dataframe['Bz'].values
                ))
            else:
                error_message = "\n".join(errors)
                self.validation_status_label.setText("Validation Status: <font color='red'>Invalid</font>")
                self.validation_status_label.setStyleSheet("font-weight: bold; color: red;")
                self.validation_errors_text.setText(error_message)
                handle_error(ValueError("Data validation failed."), f"Loaded data is invalid:\n{error_message}")
                self.data_dataframe = None
                self.observed_field_components = None

        except FileNotFoundError as e:
            handle_error(e, f"The selected file was not found: {file_path}")
            self.data_dataframe = None
            self.observed_field_components = None
            self.update_data_preview(pd.DataFrame())
            self.validation_status_label.setText("Validation Status: <font color='red'>Error</font>")
            self.validation_status_label.setStyleSheet("font-weight: bold; color: red;")
            self.validation_errors_text.setText(f"Error: {e}")
        except ValueError as e:
            handle_error(e, f"Error processing data from {file_path}")
            self.data_dataframe = None
            self.observed_field_components = None
            self.update_data_preview(pd.DataFrame())
            self.validation_status_label.setText("Validation Status: <font color='red'>Error</font>")
            self.validation_status_label.setStyleSheet("font-weight: bold; color: red;")
            self.validation_errors_text.setText(f"Error: {e}")
        except Exception as e:
            handle_error(e, f"An unexpected error occurred while loading/validating data from {file_path}")
            self.data_dataframe = None
            self.observed_field_components = None
            self.update_data_preview(pd.DataFrame())
            self.validation_status_label.setText("Validation Status: <font color='red'>Error</font>")
            self.validation_status_label.setStyleSheet("font-weight: bold; color: red;")
            self.validation_errors_text.setText(f"Unexpected Error: {e}")

    def _export_data(self):
        """
        Exports the raw and modeled magnetic field data to a CSV file (STORY-602).
        """
        if self.data_dataframe is None or self.data_dataframe.empty or self.modeled_field_components is None:
            QMessageBox.warning(self, "Export Error", "No analysis data available to export. Please load data and run analysis first.")
            return

        initial_dir = self.default_data_dir_line_edit.text() if os.path.isdir(self.default_data_dir_line_edit.text()) else os.getcwd()
        file_name, _ = QFileDialog.getSaveFileName(self, "Export Data to CSV", 
                                                   os.path.join(initial_dir, "magnetic_field_data.csv"), 
                                                   "CSV Files (*.csv)")
        if file_name:
            try:
                export_magnetic_field_data(
                    self.data_dataframe,
                    self.modeled_field_components[:, 0],
                    self.modeled_field_components[:, 1],
                    self.modeled_field_components[:, 2],
                    file_name
                )
                QMessageBox.information(self, "Export Complete", f"Data successfully exported to {file_name}")
            except Exception as e:
                handle_error(e, f"Failed to export data to CSV: {e}")
                QMessageBox.critical(self, "Export Error", f"Failed to export data: {e}")

    def update_data_preview(self, dataframe: pd.DataFrame):
        """
        Displays a preview of the loaded data in a QTableWidget (COMP-007 API contract).

        Args:
            dataframe (pandas.DataFrame): The DataFrame to display.
        """
        self.data_preview_table.clear()
        if dataframe.empty:
            self.data_preview_table.setRowCount(0)
            self.data_preview_table.setColumnCount(0)
            self.data_preview_table.setHorizontalHeaderLabels([])
            return

        self.data_preview_table.setRowCount(dataframe.shape[0])
        self.data_preview_table.setColumnCount(dataframe.shape[1])
        self.data_preview_table.setHorizontalHeaderLabels(dataframe.columns.values.tolist())

        for i, row in enumerate(dataframe.itertuples(index=False)):
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                self.data_preview_table.setItem(i, j, item)
        
        self.data_preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.data_preview_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

    def _run_analysis(self):
        """
        Orchestrates the magnetic field analysis: computes basis functions, fits coefficients,
        reconstructs the field, calculates residuals, and updates visualization and results tabs.
        """
        if self.data_dataframe is None or self.data_dataframe.empty or self.observed_field_components is None:
            QMessageBox.warning(self, "Analysis Error", "Please load and validate data first before running analysis.")
            return

        degree = self.degree_spinbox.value()
        latitude = self.data_dataframe['latitude'].values
        longitude = self.data_dataframe['longitude'].values

        try:
            design_matrix = compute_basis_functions(latitude, longitude, degree)

            observed_1d = np.concatenate((
                self.observed_field_components[:, 0],
                self.observed_field_components[:, 1],
                self.observed_field_components[:, 2]
            ))
            self.gauss_coefficients, self.gauss_uncertainties = fit_coefficients(design_matrix, observed_1d)

            modeled_Bx, modeled_By, modeled_Bz = reconstruct_field(latitude, longitude, self.gauss_coefficients, degree)
            self.modeled_field_components = np.column_stack((modeled_Bx, modeled_By, modeled_Bz))

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

            coeff_dict = {}
            coeff_names = self._generate_coeff_names(degree)
            for i, name in enumerate(coeff_names):
                if i < len(self.gauss_coefficients):
                    coeff_dict[name] = {
                        'value': self.gauss_coefficients[i],
                        'uncertainty': self.gauss_uncertainties[i] if self.gauss_uncertainties is not None and i < len(self.gauss_uncertainties) else np.nan
                    }
            self.show_results(coeff_dict, self.analysis_metrics)

            globe_fig = create_3d_globe(self.data_dataframe)
            globe_fig = add_field_vectors(globe_fig, latitude, longitude, 
                                          self.observed_field_components,
                                          self.modeled_field_components)
            self.current_globe_figure = globe_fig
            self.display_visualization(self.current_globe_figure)

            self.current_residuals_figure = plot_residuals(
                self.observed_field_components,
                self.modeled_field_components
            )

            QMessageBox.information(self, "Analysis Complete", "Magnetic field analysis completed successfully!")
            self.tab_widget.setCurrentWidget(self.results_tab)

        except ValueError as e:
            handle_error(e, f"Analysis parameter error: {e}")
        except Exception as e:
            handle_error(e, f"An unexpected error occurred during analysis: {e}")

    def display_visualization(self, plot_object: go.Figure):
        """
        Embeds and displays a Plotly figure within the GUI's visualization tab (COMP-007 API contract).
        This method specifically updates the globe view.

        Args:
            plot_object (plotly.graph_objects.Figure): The Plotly figure to display.
        """
        if plot_object is None:
            self.globe_view.setHtml("<h1>No Globe Visualization Available</h1><p>Run analysis first.</p>")
            return
        self.globe_view.setHtml(plot_object.to_html(include_plotlyjs='cdn'))
        self.visualization_stack.setCurrentWidget(self.globe_view)

    def _display_residuals_plot(self, plot_object: go.Figure):
        """
        Displays a Plotly figure for residuals within the GUI's visualization tab.
        This is an internal helper method for the residuals view.

        Args:
            plot_object (plotly.graph_objects.Figure): The Plotly figure to display.
        """
        if plot_object is None:
            self.residuals_view.setHtml("<h1>No Residuals Visualization Available</h1><p>Run analysis first.</p>")
            return
        self.residuals_view.setHtml(plot_object.to_html(include_plotlyjs='cdn'))
        self.visualization_stack.setCurrentWidget(self.residuals_view)

    def _show_field_line_plot(self):
        """
        Generates and displays the 3D magnetic field line plot.
        """
        print("[_show_field_line_plot] Button clicked.")
        if self.gauss_coefficients is None:
            print("[_show_field_line_plot] No Gauss coefficients available. Displaying placeholder.")
            self.field_line_view.setHtml("<h1>No Field Line Visualization Available</h1><p>Run analysis first.</p>")
        else:
            try:
                degree = self.degree_spinbox.value()
                print(f"[_show_field_line_plot] Generating field line plot with degree: {degree}")
                self.current_field_line_figure = create_3d_field_line_globe(self.gauss_coefficients, degree)
                print(f"[_show_field_line_plot] Figure generated: {self.current_field_line_figure is not None}")
                if self.current_field_line_figure:
                    self.field_line_view.setHtml(self.current_field_line_figure.to_html(include_plotlyjs='cdn'))
                    print("[_show_field_line_plot] HTML set to QWebEngineView.")
                else:
                    self.field_line_view.setHtml("<h1>Error</h1><p>Generated an empty figure.</p>")
                    print("[_show_field_line_plot] Generated an empty figure.")
            except Exception as e:
                handle_error(e, "Failed to generate the 3D field line plot.")
                self.field_line_view.setHtml(f"<h1>Error</h1><p>Could not generate field line plot: {e}</p>")
                print(f"[_show_field_line_plot] Exception caught: {e}")
        
        self.visualization_stack.setCurrentWidget(self.field_line_view)
        print("[_show_field_line_plot] Set current widget to field_line_view.")

    def _show_declination_map(self):
        """
        Generates and displays the Magnetic Declination Map.
        """
        print("[_show_declination_map] Button clicked.")
        if self.gauss_coefficients is None or self.data_dataframe is None or self.data_dataframe.empty:
            print("[_show_declination_map] No Gauss coefficients or data available. Displaying placeholder.")
            self.declination_map_view.setHtml("<h1>No Magnetic Declination Map Available</h1><p>Run analysis first.</p>")
        else:
            try:
                degree = self.degree_spinbox.value()
                latitude = self.data_dataframe['latitude'].values
                longitude = self.data_dataframe['longitude'].values

                print(f"[_show_declination_map] Calculating declination with degree: {degree}")
                declination_values = calculate_declination(latitude, longitude, self.gauss_coefficients, degree)

                print(f"[_show_declination_map] Generating declination map.")
                declination_map_figure = create_declination_map(latitude, longitude, declination_values)
                
                if declination_map_figure:
                    self.declination_map_figure = declination_map_figure # Store the figure
                    self.declination_map_view.setHtml(self.declination_map_figure.to_html(include_plotlyjs='cdn'))
                    print("[_show_declination_map] HTML set to QWebEngineView.")
                else:
                    self.declination_map_view.setHtml("<h1>Error</h1><p>Generated an empty figure.</p>")
                    print("[_show_declination_map] Generated an empty figure.")
            except Exception as e:
                handle_error(e, "Failed to generate the Magnetic Declination Map.")
                self.declination_map_view.setHtml(f"<h1>Error</h1><p>Could not generate declination map: {e}</p>")
                print(f"[_show_declination_map] Exception caught: {e}")
        
        self.visualization_stack.setCurrentWidget(self.declination_map_view)
        print("[_show_declination_map] Set current widget to declination_map_view.")

    def _show_field_intensity_map(self):
        """
        Generates and displays the 2D Contour Map of Field Intensity.
        """
        if self.gauss_coefficients is None:
            self.field_intensity_map_view.setHtml("<h1>No Field Intensity Map Available</h1><p>Run analysis first.</p>")
        else:
            try:
                degree = self.degree_spinbox.value()
                self.field_intensity_map_figure = create_contour_map_field_intensity(self.gauss_coefficients, degree)
                if self.field_intensity_map_figure:
                    self.field_intensity_map_view.setHtml(self.field_intensity_map_figure.to_html(include_plotlyjs='cdn'))
                else:
                    self.field_intensity_map_view.setHtml("<h1>Error</h1><p>Generated an empty figure.</p>")
            except Exception as e:
                handle_error(e, "Failed to generate the Field Intensity Map.")
                self.field_intensity_map_view.setHtml(f"<h1>Error</h1><p>Could not generate field intensity map: {e}</p>")
        
        self.visualization_stack.setCurrentWidget(self.field_intensity_map_view)


    def _save_current_plot(self):
        """
        Saves the currently displayed Plotly figure as an image file (STORY-603).
        """
        current_widget = self.visualization_stack.currentWidget()
        current_plot = None
        if current_widget == self.globe_view and self.current_globe_figure:
            current_plot = self.current_globe_figure
        elif current_widget == self.residuals_view and self.current_residuals_figure:
            current_plot = self.current_residuals_figure
        elif current_widget == self.field_line_view and self.current_field_line_figure:
            current_plot = self.current_field_line_figure
        elif current_widget == self.declination_map_view and self.declination_map_figure:
            current_plot = self.declination_map_figure
        elif current_widget == self.field_intensity_map_view and self.field_intensity_map_figure:
            current_plot = self.field_intensity_map_figure
        
        if current_plot is None:
            QMessageBox.warning(self, "Save Plot Error", "No plot is currently displayed to save.")
            return

        initial_dir = self.default_data_dir_line_edit.text() if os.path.isdir(self.default_data_dir_line_edit.text()) else os.getcwd()
        file_name, selected_filter = QFileDialog.getSaveFileName(self, "Save Plot as Image", 
                                                                 os.path.join(initial_dir, "plot.png"), 
                                                                 "PNG Image (*.png);;JPEG Image (*.jpeg *.jpg);;SVG Image (*.svg);;PDF Document (*.pdf)")
        
        if file_name:
            file_format = os.path.splitext(file_name)[1].lower().lstrip('.')
            if file_format == 'jpg': file_format = 'jpeg'

            try:
                save_plot_as_image(current_plot, file_name, format=file_format, scale=2)
                QMessageBox.information(self, "Save Plot Complete", f"Plot successfully saved to {file_name}")
            except Exception as e:
                handle_error(e, f"Failed to save plot as image: {e}")
                QMessageBox.critical(self, "Save Plot Error", f"Failed to save plot: {e}")

    def show_results(self, coefficients: dict, metrics: dict):
        """
        Populates the results tab with Gauss coefficients and model validation metrics (COMP-007 API contract).

        Args:
            coefficients (dict): A dictionary of Gauss coefficients, e.g., {'g_1^0': {'value': 0.1, 'uncertainty': 0.01}}.
            metrics (dict): A dictionary of model validation metrics, e.g., {'RMSE_total': 1.23}.
        """
        self.coefficients_table.setRowCount(len(coefficients))
        self.coefficients_table.setColumnCount(3)
        self.coefficients_table.setHorizontalHeaderLabels(["Coefficient", "Value", "Uncertainty"])

        for i, (coeff_name, data) in enumerate(coefficients.items()):
            self.coefficients_table.setItem(i, 0, QTableWidgetItem(coeff_name))
            self.coefficients_table.setItem(i, 1, QTableWidgetItem(f"{data.get('value', np.nan):.6e}"))
            self.coefficients_table.setItem(i, 2, QTableWidgetItem(f"{data.get('uncertainty', np.nan):.6e}"))
        self.coefficients_table.resizeColumnsToContents()

        metrics_text = ""
        for key, value in metrics.items():
            if isinstance(value, (float, np.floating)):
                metrics_text += f"{key}: {value:.4f}\n"
            else:
                metrics_text += f"{key}: {value}\n"
        self.metrics_text_edit.setText(metrics_text)

        self.tab_widget.setCurrentWidget(self.results_tab)

    def _generate_report(self):
        """
        Generates a PDF report of the analysis results and plots (STORY-601).
        """
        if self.gauss_coefficients is None or not self.analysis_metrics or (self.current_globe_figure is None and self.current_residuals_figure is None):
            QMessageBox.warning(self, "Report Error", "No analysis results or plots available to generate a report. Please run analysis first.")
            return

        initial_dir = self.default_data_dir_line_edit.text() if os.path.isdir(self.default_data_dir_line_edit.text()) else os.getcwd()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save PDF Report", 
                                                   os.path.join(initial_dir, "magnetic_field_report.pdf"), 
                                                   "PDF Files (*.pdf)")
        if file_name:
            try:
                plots_to_embed = []
                if self.current_globe_figure:
                    plots_to_embed.append(pio.to_image(self.current_globe_figure, format='png', width=800, height=600, scale=2))
                if self.current_residuals_figure:
                    plots_to_embed.append(pio.to_image(self.current_residuals_figure, format='png', width=800, height=600, scale=2))
                if self.field_intensity_map_figure:
                    plots_to_embed.append(pio.to_image(self.field_intensity_map_figure, format='png', width=800, height=600, scale=2))

                coeff_dict = {}
                degree = self.degree_spinbox.value()
                coeff_names = self._generate_coeff_names(degree)
                for i, name in enumerate(coeff_names):
                    if i < len(self.gauss_coefficients):
                        coeff_dict[name] = {
                            'value': self.gauss_coefficients[i],
                            'uncertainty': self.gauss_uncertainties[i] if self.gauss_uncertainties is not None and i < len(self.gauss_uncertainties) else np.nan
                        }

                pdf_bytes = generate_pdf_report(coeff_dict, self.analysis_metrics, plots_to_embed)
                
                with open(file_name, 'wb') as f:
                    f.write(pdf_bytes)
                QMessageBox.information(self, "Report Generated", f"PDF report successfully generated and saved to {file_name}")
            except Exception as e:
                handle_error(e, f"Failed to generate PDF report: {e}")
                QMessageBox.critical(self, "Report Error", f"Failed to generate report: {e}")

    def _generate_coeff_names(self, degree: int) -> list[str]:
        """
        Helper to generate standard Gauss coefficient names (g_l^m, h_l^m).
        """
        names = []
        for l in range(1, degree + 1):
            for m in range(l + 1):
                names.append(f"g_{l}^{m}")
                if m > 0:
                    names.append(f"h_{l}^{m}")
        return names

    def _load_initial_config(self):
        """
        Loads application configuration on startup.
        """
        self.config_file_path = self._CONFIG_FILE_NAME
        try:
            self.app_config = load_config(self.config_file_path)
            if 'last_opened_file' in self.app_config and os.path.exists(self.app_config['last_opened_file']):
                self.file_path_line_edit.setText(self.app_config['last_opened_file'])
            
            if 'default_data_directory' in self.app_config:
                self.default_data_dir_line_edit.setText(self.app_config['default_data_directory'])
            if 'default_lmax' in self.app_config:
                self.default_lmax_spinbox.setValue(self.app_config['default_lmax'])
            
            if 'default_lmax' in self.app_config:
                self.degree_spinbox.setValue(self.app_config['default_lmax'])

        except Exception as e:
            handle_error(e, "Failed to load application configuration. Using default settings.")
            self.app_config = {}

    def _save_current_config(self):
        """
        Saves the current application configuration.
        """
        if self.data_dataframe is not None and not self.data_dataframe.empty:
            current_file_path = self.file_path_line_edit.text()
            if current_file_path and os.path.exists(current_file_path):
                self.app_config['last_opened_file'] = current_file_path
            else:
                self.app_config.pop('last_opened_file', None)
        else:
            self.app_config.pop('last_opened_file', None)

        self.app_config['default_data_directory'] = self.default_data_dir_line_edit.text()
        self.app_config['default_lmax'] = self.default_lmax_spinbox.value()

        try:
            save_config(self.app_config, self.config_file_path)
            QMessageBox.information(self, "Configuration Saved", "Application configuration saved successfully!")
        except Exception as e:
            handle_error(e, "Failed to save application configuration.")
            QMessageBox.critical(self, "Save Error", f"Failed to save configuration: {e}")

    def closeEvent(self, event):
        """
        Overrides close event to save configuration and stop real-time operations.
        """
        self._save_current_config()
        if self.realtime_worker.isRunning():
            self._stop_realtime_stream()
        if self.hardware_integration.is_connected():
            self.hardware_integration.disconnect_device()
        self.realtime_update_timer.stop()
        super().closeEvent(event)

def init_main_window():
    """
    Initializes and displays the main PyQt6 application window with menu and tabs (COMP-007 API contract).
    This function acts as the entry point for the GUI.
    """
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    init_main_window()

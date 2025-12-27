#!/usr/bin/env python3
"""
Earth's Magnetic Field Modeling Application
Main entry point for the PyQt6 desktop application.

This launches the GUI manager which provides:
- Data ingestion from CSV/Excel files
- Spherical harmonic analysis up to degree 13
- Interactive 3D visualization with Plotly
- Real-time magnetometer data acquisition
- PDF report generation

Usage:
    python main.py

Requirements:
    - Python 3.11+
    - PyQt6, numpy, scipy, pandas, plotly
    - See requirements.txt for full list
"""

import sys
from PyQt6.QtWidgets import QApplication
from src.gui_manager import MainWindow


def main():
    """Initialize and launch the application."""
    app = QApplication(sys.argv)
    app.setApplicationName("Magnetic Field Analyzer")
    app.setOrganizationName("Adam Bentley")
    app.setOrganizationDomain("github.com/adamfbentley")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

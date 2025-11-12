# Earth's Magnetic Field modelling Application

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.0+-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A professional desktop application for geophysical data analysis featuring **spherical harmonic analysis** of Earth's magnetic field. Built with PyQt6, this application provides real-time sensor integration, interactive 3D visualisations, and automated PDF reporting for research and educational purposes.

## 🌍 Overview

This application allows geophysicists, researchers, and students to:
- Model Earth's magnetic field using spherical harmonic expansion
- Acquire and process real-time magnetometer data
- Visualize magnetic field vectors, declination, and intensity in 3D
- Generate comprehensive PDF reports with analysis results
- Validate models against measured data

## ✨ Key Features

### Scientific Computing
- **Spherical Harmonic Analysis**: Mathematical modelling using associated Legendre polynomials
- **Gauss Coefficient Determination**: Least-squares fitting for up to degree 13 harmonics
- **Field Component Calculations**: Compute Br, Bθ, Bφ components at any Earth location
- **Model Validation**: Statistical metrics (RMSE, R², residual analysis) for quality assessment

### Interactive visualisations
- **3D Globe Rendering**: Interactive Earth visualisation with Plotly
- **Magnetic Field Vectors**: Directional arrows showing field orientation
- **Declination Maps**: Color-coded magnetic declination across Earth's surface
- **Intensity Contours**: Field strength visualisation with customizable colormaps
- **Field Line Plots**: Magnetic field line tracing from pole to pole

### Real-Time Data Acquisition
- **Hardware Integration**: PySerial connection to magnetometer sensors
- **Multi-threaded Processing**: Non-blocking data streaming and buffering
- **Live Updates**: Real-time display of sensor measurements
- **Data Logging**: Automatic CSV export of time-series data

### Automated Reporting
- **PDF Generation**: Comprehensive reports with ReportLab
- **Embedded visualisations**: High-quality plots and statistical tables
- **Gauss Coefficients**: Complete spherical harmonic coefficient listings
- **Model Validation Metrics**: RMSE, correlation coefficients, residual plots

### Professional Architecture
- **Modular Design**: 15+ separate modules with clean separation of concerns
- **PyQt6 GUI**: Modern desktop interface with tabbed navigation
- **Comprehensive Testing**: pytest test suite with >80% coverage
- **Sphinx Documentation**: Full API reference and user guide

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- (Optional) USB magnetometer sensor for real-time data acquisition

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/adamfbentley/earth-magnetic-field-app.git
cd earth-magnetic-field-app
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run the application**
```bash
python main.py
```

## 📖 Usage

### Loading Data

**From CSV/Excel:**
1. Navigate to **Data Ingestion** tab
2. Click **Load File** and select your data file
3. Map columns (latitude, longitude, magnetic field components)
4. Click **Validate & Import**

**From Real-Time Sensor:**
1. Connect magnetometer via USB
2. Navigate to **Real-Time Acquisition** tab
3. Select COM port and configure baud rate
4. Click **Start Acquisition**

### Spherical Harmonic Analysis

1. Navigate to **Analysis** tab
2. Select harmonic degree (1-13)
3. Click **Fit Model** to compute Gauss coefficients
4. View fitting statistics and residuals
5. Export coefficients to CSV

### visualisation

**3D Field visualisation:**
```python
# Navigate to visualisation tab
# Select visualisation type:
#   - Vector Field: Directional arrows
#   - Declination Map: Angular deviation from geographic north
#   - Intensity Contours: Field strength magnitudes
#   - Field Lines: Magnetic field line tracing

# Customize:
#   - Resolution: Points per degree
#   - Altitude: Height above Earth's surface (km)
#   - Colormap: Viridis, Plasma, Jet, etc.
```

### Generate Report

1. Navigate to **Reporting** tab
2. Select report components:
   - Model summary
   - Gauss coefficients
   - Validation metrics
   - visualisations
3. Click **Generate PDF Report**
4. Save to desired location

## 🧮 Scientific Background

### Spherical Harmonic Expansion

Earth's magnetic field B can be represented as the gradient of a scalar potential V:

$$
V(r, \theta, \phi) = a \sum_{n=1}^{N} \sum_{m=0}^{n} \left(\frac{a}{r}\right)^{n+1} P_n^m(\cos\theta) [g_n^m \cos(m\phi) + h_n^m \sin(m\phi)]
$$

Where:
- $a$ = Earth's mean radius (6371.2 km)
- $P_n^m$ = Associated Legendre polynomials
- $g_n^m, h_n^m$ = Gauss coefficients
- $n$ = Degree, $m$ = Order

### Field Components

The magnetic field components in spherical coordinates:

$$
B_r = -\frac{\partial V}{\partial r}, \quad
B_\theta = -\frac{1}{r}\frac{\partial V}{\partial \theta}, \quad
B_\phi = -\frac{1}{r\sin\theta}\frac{\partial V}{\partial \phi}
$$

### Least-Squares Fitting

Gauss coefficients are determined by minimizing:

$$
\chi^2 = \sum_i \left[B_{\text{measured},i} - B_{\text{model},i}(g_n^m, h_n^m)\right]^2
$$

## 🛠️ Technology Stack

| Category | Technologies |
|----------|-------------|
| **GUI Framework** | PyQt6, PyQt6-WebEngine |
| **Scientific Computing** | NumPy, SciPy (special functions, optimisation) |
| **visualisation** | Plotly (3D interactive), Matplotlib |
| **Data Processing** | pandas, openpyxl |
| **Hardware** | PySerial (magnetometer integration) |
| **Reporting** | ReportLab (PDF generation) |
| **Testing** | pytest, pytest-qt |
| **Documentation** | Sphinx, autodoc |

## 📁 Project Structure

```
earth-magnetic-field-app/
├── src/
│   ├── gui_manager.py              # Main application window
│   ├── data_ingestion.py           # CSV/Excel data loading
│   ├── data_validation.py          # Quality checks and filtering
│   ├── spherical_harmonics.py      # Mathematical modelling engine
│   ├── gauss_coefficients.py       # Least-squares fitting
│   ├── visualisation_engine.py     # Plotly 3D rendering
│   ├── real_time_acquisition.py    # PySerial sensor interface
│   ├── report_generator.py         # PDF creation
│   └── utils/
│       ├── coordinate_transforms.py
│       ├── legendre_polynomials.py
│       └── statistics.py
├── tests/
│   ├── test_spherical_harmonics.py
│   ├── test_gauss_coefficients.py
│   └── test_visualisation.py
├── docs/                           # Sphinx documentation
├── data/                           # Sample datasets
├── requirements.txt
├── architecture.md                 # Design documentation
└── README.md
```

## 🧪 Testing

Run the test suite:

```bash
# All tests
pytest

# With coverage report
pytest --cov=src --cov-report=html

# Specific test modules
pytest tests/test_spherical_harmonics.py -v

# GUI tests (requires display)
pytest tests/test_gui.py --qt-api=pyqt6
```

## 📊 Sample Data

Included sample datasets in `data/`:
- `igrf13_coefficients.csv`: International Geomagnetic Reference Field (IGRF-13) model
- `sample_measurements.csv`: Synthetic magnetometer readings
- `observatory_data.xlsx`: Historical observatory measurements

## 🎓 Educational Use

This application is suitable for:
- **University Courses**: Geophysics, Applied Mathematics, Computational Physics
- **Research Projects**: Magnetic field modelling, sensor calibration
- **Student Labs**: Hands-on learning of spherical harmonics and data analysis
- **Science Communication**: Interactive demonstrations of Earth's magnetic field

## 🤝 Contributing

Contributions welcome! Areas of interest:
- Additional magnetic field models (CHAOS, WMM)
- Time-dependent modelling (secular variation)
- Improved sensor support (I2C, SPI interfaces)
- Machine learning for anomaly detection
- Web-based version (PyQt → FastAPI + React)

## 📚 References

**Scientific:**
- Langel, R.A., & Hinze, W.J. (1998). *The Magnetic Field of the Earth's Lithosphere*. Cambridge University Press.
- Lowes, F.J. (1974). "Spatial Power Spectrum of the Main Geomagnetic Field." *Geophysical Journal International*.

**Data Sources:**
- IGRF-13: International Geomagnetic Reference Field (2020)
- NOAA National Centers for Environmental Information
- BGS Geomagnetism Research Group

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 👤 Author

**Adam Bentley**
- Physics & Mathematics, Victoria University of Wellington
- Email: adam.f.bentley@gmail.com
- GitHub: [@adamfbentley](https://github.com/adamfbentley)

## 🙏 Acknowledgments

- PyQt development team for excellent GUI framework
- Plotly for beautiful 3D visualisations
- SciPy community for special functions implementation

---

**Screenshots**

*Coming soon: Application screenshots and demo videos*

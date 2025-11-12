import logging
import sys
from PyQt6.QtWidgets import QMessageBox # CQ-001: Added for GUI integration

# Configure basic logging
# This setup is for a simple console output. For a GUI, this would be integrated
# with a message box or status bar. For now, it logs to stderr.
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)

def handle_error(exception: Exception, message: str):
    """
    Processes an exception, logs it, and presents a user-friendly error message.
    For a desktop application, this would typically involve displaying a pop-up
    dialog. For this foundational sprint, it logs the error.

    Args:
        exception (Exception): The exception object that was caught.
        message (str): A user-friendly message describing the error context.
    """
    logging.error(f"Application Error: {message}", exc_info=True)
    # CQ-001: Replaced placeholder with actual QMessageBox integration
    QMessageBox.critical(None, "Application Error", f"An error occurred: {message}\nDetails logged.")

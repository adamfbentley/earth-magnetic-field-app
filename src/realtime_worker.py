import time
import logging
from PyQt6.QtCore import QThread, pyqtSignal

from src.hardware_integration import HardwareIntegration
from src.realtime_data_processor import parse_raw_data, validate_realtime_point
from src.realtime_data_buffer import RealtimeDataBuffer
from src.error_handling import handle_error

logger = logging.getLogger(__name__)

class RealtimeWorker(QThread):
    """
    A QThread subclass for real-time data acquisition.
    It reads raw data from a serial device, parses and validates it,
    and adds valid data points to a shared buffer.
    Emits signals for data reception, errors, and status updates.
    """
    data_received_signal = pyqtSignal(dict) # Emits a single validated data point
    error_signal = pyqtSignal(Exception, str) # Emits exception and a user-friendly message
    status_signal = pyqtSignal(str) # Emits status messages

    def __init__(self, hardware_integration: HardwareIntegration, data_buffer: RealtimeDataBuffer, parent=None):
        super().__init__(parent)
        self.hardware_integration = hardware_integration
        self.data_buffer = data_buffer
        self._running = False
        self.polling_interval_sec = 0.01 # Poll every 10 ms

    def start_streaming(self):
        """
        Starts the data acquisition loop in the worker thread.
        """
        if not self.hardware_integration.is_connected():
            self.error_signal.emit(ValueError("Not connected"), "Cannot start stream: No device connected.")
            return
        if not self._running:
            self._running = True
            self.start() # Start the QThread
            self.status_signal.emit("Real-time stream started.")
            logger.info("Real-time worker thread started.")

    def stop_streaming(self):
        """
        Stops the data acquisition loop in the worker thread.
        """
        if self._running:
            self._running = False
            self.status_signal.emit("Real-time stream stopping...")
            logger.info("Real-time worker thread stopping.")

    def run(self):
        """
        The main loop of the worker thread for data acquisition.
        """
        while self._running:
            if not self.hardware_integration.is_connected():
                self.error_signal.emit(ValueError("Disconnected"), "Serial device disconnected during stream.")
                self._running = False # Stop the loop if disconnected unexpectedly
                break

            raw_data = self.hardware_integration.read_data()
            if raw_data:
                data_point = parse_raw_data(raw_data)
                if data_point:
                    is_valid, errors = validate_realtime_point(data_point)
                    if is_valid:
                        self.data_buffer.add_data_point(data_point)
                        self.data_received_signal.emit(data_point)
                    else:
                        error_msg = f"Invalid real-time data point: {', '.join(errors)}"
                        self.error_signal.emit(ValueError(error_msg), error_msg)
                # else: parse_raw_data already handles errors and logs warnings
            
            time.sleep(self.polling_interval_sec)
        logger.info("Real-time worker thread finished.")

    def isRunning(self) -> bool:
        """
        Checks if the worker thread's streaming loop is active.
        """
        return self._running

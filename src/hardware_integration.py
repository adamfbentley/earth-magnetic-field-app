import serial
import logging
from src.error_handling import handle_error

logger = logging.getLogger(__name__)

class HardwareIntegration:
    """
    Manages connection to external magnetic field sensors via serial port
    and provides raw data streams (COMP-013).
    """
    def __init__(self):
        self.ser = None
        self.is_connected_flag = False

    def connect_device(self, port: str, baud_rate: int) -> bool:
        """
        Establishes a serial connection to the specified device.

        Args:
            port (str): The serial port name (e.g., 'COM1' on Windows, '/dev/ttyUSB0' on Linux).
            baud_rate (int): The baud rate for the serial communication.

        Returns:
            bool: True if connection is successful, False otherwise.
        """
        if self.is_connected_flag:
            logger.info(f"Already connected to {self.ser.port}. Disconnecting first.")
            self.disconnect_device()

        try:
            self.ser = serial.Serial(port, baud_rate, timeout=1)
            self.is_connected_flag = True
            logger.info(f"Successfully connected to serial port {port} at {baud_rate} baud.")
            return True
        except serial.SerialException as e:
            handle_error(e, f"Failed to connect to serial port {port}: {e}")
            self.is_connected_flag = False
            return False
        except Exception as e:
            handle_error(e, f"An unexpected error occurred during serial connection to {port}: {e}")
            self.is_connected_flag = False
            return False

    def disconnect_device(self) -> None:
        """
        Closes the serial connection.
        """
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
                self.is_connected_flag = False
                logger.info(f"Disconnected from serial port {self.ser.port}.")
            except Exception as e:
                handle_error(e, f"Error while disconnecting from serial port {self.ser.port}: {e}")
        else:
            logger.info("No active serial connection to disconnect.")

    def is_connected(self) -> bool:
        """
        Checks if a device is currently connected.

        Returns:
            bool: True if connected, False otherwise.
        """
        return self.is_connected_flag and self.ser.is_open

    def read_data(self) -> bytes | None:
        """
        Reads a chunk of raw data (a line) from the connected device.
        Assumes data is line-terminated (e.g., with '\n').

        Returns:
            bytes | None: A line of raw data as bytes, or None if no data or not connected.
        """
        if not self.is_connected_flag or not self.ser:
            handle_error(ValueError("Not connected to device."), "Cannot read data: No device connected.")
            return None

        try:
            # Read until newline character, with a timeout
            line = self.ser.readline()
            if line:
                return line.strip() # Remove leading/trailing whitespace and newline
            return None
        except serial.SerialTimeoutException:
            logger.warning("Serial read timed out, no data received.")
            return None
        except serial.SerialException as e:
            handle_error(e, f"Serial communication error during read: {e}")
            self.disconnect_device() # Attempt to disconnect on error
            return None
        except Exception as e:
            handle_error(e, f"An unexpected error occurred during serial read: {e}")
            self.disconnect_device()
            return None

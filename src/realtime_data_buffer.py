import pandas as pd
from collections import deque

class RealtimeDataBuffer:
    """
    Manages a rolling buffer of recent real-time magnetic field data points,
    optimized for efficient additions and retrieval for dynamic visualization (COMP-015).
    """
    def __init__(self, max_size: int = 1000):
        """
        Initializes the real-time data buffer.

        Args:
            max_size (int): The maximum number of data points to store in the buffer.
        """
        if not isinstance(max_size, int) or max_size <= 0:
            raise ValueError("max_size must be a positive integer.")
        self.buffer = deque(maxlen=max_size)

    def add_data_point(self, data_point: dict) -> None:
        """
        Adds a new validated data point to the buffer, maintaining a fixed maximum size.
        The oldest data point is automatically removed if the buffer is full.

        Args:
            data_point (dict): A dictionary representing a single validated data point.
        """
        if not isinstance(data_point, dict):
            raise TypeError("data_point must be a dictionary.")
        self.buffer.append(data_point)

    def get_current_data(self) -> pd.DataFrame:
        """
        Retrieves all data points currently in the buffer as a pandas DataFrame.

        Returns:
            pandas.DataFrame: A DataFrame containing the buffered data. Returns an empty
                              DataFrame if the buffer is empty.
        """
        if not self.buffer:
            return pd.DataFrame()
        return pd.DataFrame(list(self.buffer))

    def clear_buffer(self) -> None:
        """
        Clears all data from the buffer.
        """
        self.buffer.clear()

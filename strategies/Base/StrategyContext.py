class StrategyContext:
    """Manages the current execution state and prevents look-ahead bias."""
    
    def __init__(self):
        self._current_index = 0
        self._data_length = 0
    
    def update_index(self, index: int):
        """Update the current bar index."""
        if index < 0 or index >= self._data_length:
            raise IndexError(f"Index {index} out of bounds for data length {self._data_length}")
        self._current_index = index
    
    def get_current_index(self) -> int:
        """Get the current bar index."""
        return self._current_index
    
    def set_data_length(self, length: int):
        """Set the total data length."""
        if length <= 0:
            raise ValueError(f"Data length must be positive, got {length}")
        self._data_length = length
        self._current_index = length - 1  # Reset index when setting new data length

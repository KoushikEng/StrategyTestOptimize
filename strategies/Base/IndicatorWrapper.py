import numpy as np
from .StrategyContext import StrategyContext

class IndicatorWrapper:
    """Provides array-like access to pre-calculated indicator values with automatic look-ahead prevention."""
    
    def __init__(self, values: np.ndarray, context: StrategyContext):
        if not isinstance(values, np.ndarray):
            raise TypeError(f"Values must be numpy array, got {type(values)}")
        if len(values) == 0:
            raise ValueError("Values array cannot be empty")
        
        self._values = values
        self._context = context
    
    def __getitem__(self, index: int):
        """Access indicator value with negative indexing support."""
        if not isinstance(index, int):
            raise TypeError(f"Index must be integer, got {type(index)}")
        
        current_idx = self._context.get_current_index()
        
        if index < 0:
            # Negative indexing: -1 is current bar, -2 is previous bar, etc.
            actual_index = current_idx + index + 1
        else:
            # Positive indexing: 0 is first bar, 1 is second bar, etc.
            actual_index = index
        
        # Prevent look-ahead bias and out-of-bounds access
        if actual_index < 0:
            raise IndexError(f"Index {index} would access data before start of series")
        if actual_index > current_idx:
            raise IndexError(f"Index {index} would access future data (current bar: {current_idx})")
        if actual_index >= len(self._values):
            raise IndexError(f"Index {index} out of bounds for indicator length {len(self._values)}")
        
        return self._values[actual_index]
    
    def __len__(self) -> int:
        """Return the length up to current index."""
        current_idx = self._context.get_current_index()
        return min(current_idx + 1, len(self._values))
    
    @property
    def values(self) -> np.ndarray:
        """Get values up to current index to prevent look-ahead bias."""
        current_idx = self._context.get_current_index()
        return self._values[:current_idx + 1].copy()  # Return copy to prevent modification

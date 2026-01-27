from .IndicatorWrapper import IndicatorWrapper
from .StrategyContext import StrategyContext
import numpy as np


# Import DataTuple type for better type hints
try:
    from Utilities import DataTuple
except ImportError:
    # Fallback if import fails
    from typing import Any
    DataTuple = Any

class DataAccessor:
    """Provides clean access to market data with automatic slicing."""
    
    def __init__(self, data: DataTuple, context: StrategyContext):
        if not isinstance(data, tuple) or len(data) != 7:
            raise ValueError(f"Data must be a 7-element DataTuple, got {type(data)} with length {len(data) if hasattr(data, '__len__') else 'unknown'}")
        
        symbol, timestamps, opens, highs, lows, closes, volume = data
        self._context = context
        self.symbol = symbol
        
        # Validate data types and convert if necessary
        if not isinstance(timestamps, np.ndarray):
            timestamps = np.array(timestamps)
        if not isinstance(opens, np.ndarray):
            opens = np.array(opens)
        if not isinstance(highs, np.ndarray):
            highs = np.array(highs)
        if not isinstance(lows, np.ndarray):
            lows = np.array(lows)
        if not isinstance(closes, np.ndarray):
            closes = np.array(closes)
        if not isinstance(volume, np.ndarray):
            volume = np.array(volume)
        
        # Ensure correct data types as specified in requirements
        timestamps = timestamps.astype(np.int64)
        opens = opens.astype(np.float64)
        highs = highs.astype(np.float64)
        lows = lows.astype(np.float64)
        closes = closes.astype(np.float64)
        volume = volume.astype(np.int64)
        
        # Validate all arrays have the same length
        lengths = [len(timestamps), len(opens), len(highs), len(lows), len(closes), len(volume)]
        if not all(length == lengths[0] for length in lengths):
            raise ValueError(f"All data arrays must have the same length, got lengths: {lengths}")
        
        # Create IndicatorWrapper instances for each data series
        self.timestamps = IndicatorWrapper(timestamps.astype(np.float64), context)  # Convert to float for IndicatorWrapper
        self.Open = IndicatorWrapper(opens, context)
        self.High = IndicatorWrapper(highs, context)
        self.Low = IndicatorWrapper(lows, context)
        self.Close = IndicatorWrapper(closes, context)
        self.Volume = IndicatorWrapper(volume.astype(np.float64), context)  # Convert to float for IndicatorWrapper
        
        # Store original data types for reference
        self._original_timestamps = timestamps
        self._original_volume = volume
    
    def __getattribute__(self, name):
        """Override __getattribute__ to automatically return values from IndicatorWrapper instances."""
        attr = super().__getattribute__(name)
        
        # Check if it's an IndicatorWrapper instance
        if isinstance(attr, IndicatorWrapper):
            return attr.values  #  Return the underlying values instead of the wrapper
        
        return attr
    
    def get_current_bar_data(self) -> dict:
        """Get current bar's OHLCV data."""
        return {
            'timestamp': int(self._original_timestamps[self._context.get_current_index()]),
            'open': self.Open[-1],
            'high': self.High[-1],
            'low': self.Low[-1],
            'close': self.Close[-1],
            'volume': int(self._original_volume[self._context.get_current_index()])
        }

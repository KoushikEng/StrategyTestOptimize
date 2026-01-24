from abc import ABC, abstractmethod
from typing import Tuple, Callable, Any
from numpy.typing import NDArray
import numpy as np
from dataclasses import dataclass

# Import DataTuple type for better type hints
try:
    from Utilities import DataTuple
except ImportError:
    # Fallback if import fails
    from typing import Any
    DataTuple = Any


@dataclass
class TradeRecord:
    """Record of a completed trade."""
    entry_price: float
    exit_price: float
    entry_index: int
    exit_index: int
    return_pct: float
    position_size: float


@dataclass
class StrategyResults:
    """Results from strategy execution."""
    returns: np.ndarray
    equity_curve: np.ndarray
    win_rate: float
    total_trades: int


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
        self._current_index = 0  # Reset index when setting new data length


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


class PositionManager:
    """Handles position tracking and trade execution."""
    
    def __init__(self):
        self.position_size = 0.0
        self.entry_price = 0.0
        self.entry_index = -1
        self.trades = []  # List of TradeRecord objects
    
    def open_position(self, price: float, size: float, index: int):
        """Open a new position."""
        if self.is_in_position():
            raise ValueError("Already in position. Close current position before opening new one.")
        
        if size <= 0:
            raise ValueError(f"Position size must be positive, got {size}")
        if price <= 0:
            raise ValueError(f"Entry price must be positive, got {price}")
        if index < 0:
            raise ValueError(f"Entry index must be non-negative, got {index}")
        
        self.position_size = size
        self.entry_price = price
        self.entry_index = index
    
    def close_position(self, price: float, index: int) -> float:
        """Close current position and return the trade return."""
        if not self.is_in_position():
            raise ValueError("No position to close")
        
        if price <= 0:
            raise ValueError(f"Exit price must be positive, got {price}")
        if index < 0:
            raise ValueError(f"Exit index must be non-negative, got {index}")
        if index <= self.entry_index:
            raise ValueError(f"Exit index {index} must be after entry index {self.entry_index}")
        
        # Calculate return percentage
        trade_return = (price - self.entry_price) / self.entry_price
        
        # Create trade record
        trade_record = TradeRecord(
            entry_price=self.entry_price,
            exit_price=price,
            entry_index=self.entry_index,
            exit_index=index,
            return_pct=trade_return,
            position_size=self.position_size
        )
        self.trades.append(trade_record)
        
        # Reset position state
        self.position_size = 0.0
        self.entry_price = 0.0
        self.entry_index = -1
        
        return trade_return
    
    def is_in_position(self) -> bool:
        """Check if currently in a position."""
        return self.position_size != 0.0
    
    def get_current_position_info(self) -> dict:
        """Get information about current position."""
        return {
            'in_position': self.is_in_position(),
            'position_size': self.position_size,
            'entry_price': self.entry_price,
            'entry_index': self.entry_index
        }
    
    def get_trade_returns(self) -> np.ndarray:
        """Get array of all trade returns."""
        return np.array([trade.return_pct for trade in self.trades])
    
    def get_trade_count(self) -> int:
        """Get total number of completed trades."""
        return len(self.trades)


class IndicatorWrapper:
    """Provides array-like access to pre-calculated indicator values with automatic look-ahead prevention."""
    
    def __init__(self, values: np.ndarray, context: StrategyContext):
        if not isinstance(values, np.ndarray):
            raise TypeError(f"Values must be numpy array, got {type(values)}")
        if len(values) == 0:
            raise ValueError("Values array cannot be empty")
        
        self._values = values
        self._context = context
    
    def __getitem__(self, index: int) -> float:
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
        
        return float(self._values[actual_index])
    
    def __len__(self) -> int:
        """Return the length up to current index."""
        current_idx = self._context.get_current_index()
        return min(current_idx + 1, len(self._values))
    
    @property
    def values(self) -> np.ndarray:
        """Get values up to current index to prevent look-ahead bias."""
        current_idx = self._context.get_current_index()
        return self._values[:current_idx + 1].copy()  # Return copy to prevent modification

class Base(ABC):
    """Enhanced base class for strategies with backtesting.py-inspired interface."""
    
    def __init__(self):
        self._context = StrategyContext()
        self._position_manager = PositionManager()
        self._indicators = {}
        self.data = None
        self._raw_data = None
    
    @abstractmethod
    def init(self):
        """Initialize strategy indicators and parameters."""
        pass
    
    @abstractmethod
    def next(self):
        """Process the current bar."""
        pass
    
    def get_full_data_array(self, series_name: str) -> np.ndarray:
        """Get full data array for indicator calculation during init()."""
        if not hasattr(self, '_cached_data_arrays') or self._cached_data_arrays is None:
            raise RuntimeError("Cached data arrays not available")
        
        series_key = series_name.lower()
        if series_key not in self._cached_data_arrays:
            raise ValueError(f"Unknown series name: {series_name}")
        
        return self._cached_data_arrays[series_key]
    
    def I(self, func: Callable, *args, **kwargs) -> IndicatorWrapper:
        """Register and calculate an indicator."""
        if not callable(func):
            raise TypeError(f"Indicator function must be callable, got {type(func)}")
        
        # Create a unique key for this indicator call
        func_name = getattr(func, '__name__', str(func))
        
        # Create hashable representation of args and kwargs
        # For proper caching, we need to identify when the same function is called
        # with the same parameters (including array contents)
        hashable_args = []
        for arg in args:
            if isinstance(arg, np.ndarray):
                # Use array identity (id) for exact caching, or content hash for value-based caching
                # For this implementation, we'll use a content-based approach
                try:
                    # Use a hash of the array contents for caching
                    array_hash = hash(arg.tobytes())
                    hashable_args.append(f"array_{arg.shape}_{arg.dtype}_{array_hash}")
                except TypeError:
                    # Fallback if array is not hashable
                    hashable_args.append(f"array_{arg.shape}_{arg.dtype}_{id(arg)}")
            else:
                hashable_args.append(arg)
        
        key = f"{func_name}_{hash((tuple(hashable_args), tuple(sorted(kwargs.items()))))}"
        
        # Check if indicator is already calculated
        if key in self._indicators:
            return self._indicators[key]
        
        try:
            # Calculate indicator values
            if self.data is None:
                raise RuntimeError("Cannot register indicators before data is set")
            
            # Call the indicator function with the provided arguments
            values = func(*args, **kwargs)
            
            if not isinstance(values, np.ndarray):
                values = np.array(values)
            
            # Validate indicator length matches data length
            data_length = self._context._data_length
            if len(values) != data_length:
                raise ValueError(f"Indicator length {len(values)} doesn't match data length {data_length}")
            
            # Create and cache the indicator wrapper
            wrapper = IndicatorWrapper(values.astype(np.float64), self._context)
            self._indicators[key] = wrapper
            return wrapper
            
        except Exception as e:
            raise RuntimeError(f"Failed to register indicator {func_name}: {str(e)}")
    
    def buy(self, size: float = 1.0):
        """Open a long position."""
        if self._position_manager.is_in_position():
            raise ValueError("Already in position. Close current position before opening new one.")
        
        if self.data is None:
            raise RuntimeError("Cannot execute trades before data is set")
        
        current_index = self._context.get_current_index()
        current_price = self.data.Close[-1]  # Current close price
        
        self._position_manager.open_position(current_price, size, current_index)
    
    def sell(self, size: float = None):
        """Close current position."""
        if self.data is None:
            raise RuntimeError("Cannot execute trades before data is set")
        
        if not self._position_manager.is_in_position():
            raise ValueError("No position to close")
        
        current_index = self._context.get_current_index()
        current_price = self.data.Close[-1]  # Current close price
        
        return self._position_manager.close_position(current_price, current_index)
    
    @property
    def position(self) -> dict:
        """Get current position information."""
        return self._position_manager.get_current_position_info()
    
    def _execute_strategy(self, data: DataTuple, **kwargs) -> StrategyResults:
        """Execute the strategy using the new init() and next() interface."""
        # Set up data and context
        symbol, timestamps, opens, highs, lows, closes, volume = data
        data_length = len(closes)
        
        self._context.set_data_length(data_length)
        self.data = DataAccessor(data, self._context)
        
        # Clear previous state
        self._indicators.clear()
        self._position_manager = PositionManager()
        
        # Store raw data for indicator calculation during init
        self._raw_data = data
        
        # Cache data arrays to ensure consistent object identity for caching
        self._cached_data_arrays = {
            'open': opens,
            'high': highs,
            'low': lows,
            'close': closes,
            'volume': volume.astype(np.float64),
            'timestamps': timestamps.astype(np.float64)
        }
        
        # Initialize strategy - during init, indicators can access full data
        self.init()
        
        # Process each bar
        returns_array = np.zeros(data_length)
        
        for i in range(data_length):
            self._context.update_index(i)
            
            # Call strategy's next() method
            self.next()
            
            # If a position was closed on this bar, record the return
            if len(self._position_manager.trades) > 0:
                last_trade = self._position_manager.trades[-1]
                if last_trade.exit_index == i:
                    returns_array[i] = last_trade.return_pct
        
        # Get final results
        trade_returns = self._position_manager.get_trade_returns()
        total_trades = self._position_manager.get_trade_count()
        
        if total_trades > 0:
            equity_curve = np.cumprod(1 + trade_returns)
            win_rate = np.sum(trade_returns > 0) / total_trades
        else:
            equity_curve = np.array([1.0])
            win_rate = 0.0
        
        return StrategyResults(
            returns=trade_returns,
            equity_curve=equity_curve,
            win_rate=win_rate,
            total_trades=total_trades
        )
    
    def process(self, data: DataTuple, **kwargs) -> Tuple[NDArray, NDArray, float, int]:
        """
        Process the data using the enhanced strategy interface.
        
        Args:
            data (DataTuple): The data to process.
                             Format: (symbol, timestamps, opens, highs, lows, closes, volume)
            **kwargs: Strategy parameters.
            
        Returns:
            Tuple[np.ndarray, np.ndarray, float, int]: Tuple containing (returns, equity_curve, win_rate, no_of_trades)
        """
        results = self._execute_strategy(data, **kwargs)
        return results.returns, results.equity_curve, results.win_rate, results.total_trades
    
    # Legacy method for backward compatibility - now deprecated
    def run(self, data: DataTuple, **kwargs) -> NDArray:
        """
        Legacy run method for backward compatibility.
        
        DEPRECATED: Use init() and next() methods instead.
        This method is maintained for compatibility with existing strategies.
        """
        results = self._execute_strategy(data, **kwargs)
        
        # Convert trade returns to bar-by-bar returns for legacy compatibility
        symbol, timestamps, opens, highs, lows, closes, volume = data
        data_length = len(closes)
        bar_returns = np.zeros(data_length)
        
        for trade in self._position_manager.trades:
            bar_returns[trade.exit_index] = trade.return_pct
        
        return bar_returns
    
    @abstractmethod
    def validate_params(self, **kwargs) -> bool:
        """
        Validate the parameters of the strategy.
        
        Args:
            **kwargs: Strategy parameters.
            
        Returns:
            bool: True if parameters are valid, False otherwise.
        """
        return True

    @staticmethod
    @abstractmethod
    def get_optimization_params():
        """
        Get the optimization parameters for the strategy.
        
        Returns:
            Dict[str, Tuple[float, float]]: Dictionary containing the optimization parameters.
        """
        pass
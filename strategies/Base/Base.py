from abc import ABC, abstractmethod
from typing import Tuple, Callable, Any
from numpy.typing import NDArray
import numpy as np
from dataclasses import dataclass
from .StrategyContext import StrategyContext
from .PositionManager import PositionManager
from .DataAccessor import DataAccessor
from .IndicatorWrapper import IndicatorWrapper

# Import DataTuple type for better type hints
try:
    from Utilities import DataTuple
except ImportError:
    # Fallback if import fails
    from typing import Any
    DataTuple = Any


@dataclass
class StrategyResults:
    """Results from strategy execution."""
    returns: np.ndarray
    equity_curve: np.ndarray
    win_rate: float
    total_trades: int


class Base(ABC):
    """Enhanced base class for strategies with backtesting.py-inspired interface."""
    
    def __init__(self):
        self._context = StrategyContext()
        self._position_manager = PositionManager()
        self._indicators = {}
        self.data = None
    
    @abstractmethod
    def init(self):
        """Initialize strategy indicators and parameters."""
        pass
    
    @abstractmethod
    def next(self):
        """Process the current bar."""
        pass
    
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
        
        # Initialize strategy - during init, indicators can access full data
        self.init()
        
        # Process each bar
        for i in range(data_length):
            self._context.update_index(i)
            
            # Call strategy's next() method
            self.next()
        
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
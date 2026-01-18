from abc import ABC, abstractmethod
from typing import Tuple
from numpy.typing import NDArray
import numpy as np

# Import DataTuple type for better type hints
try:
    from Utilities import DataTuple
except ImportError:
    # Fallback if import fails
    from typing import Any
    DataTuple = Any

class Base(ABC):
    """Base class for strategies.
    """
    

    def __init__(self):
        pass
    
    @abstractmethod
    def run(self, data: DataTuple, **kwargs) -> NDArray:
        """
        Run the strategy on the given data.
        
        Args:
            data (DataTuple): The data to run on. 
                             Format: (symbol, timestamps, opens, highs, lows, closes, volume)
                             - timestamps: np.ndarray[np.int64] - Unix timestamps
                             - opens, highs, lows, closes: np.ndarray[np.float64] - Price data
                             - volume: np.ndarray[np.int64] - Volume data
            **kwargs: Strategy parameters.
            
        Returns:
            np.ndarray: Returns on each trade
            
        Note:
            With the new timestamp format, strategies should unpack data as:
            symbol, timestamps, opens, highs, lows, closes, volume = data
            
            Use datetime utility functions from datetime_utils module for time-based logic:
            - extract_hour(timestamp), extract_minute(timestamp), etc.
            - is_market_hours(timestamp), is_opening_hour(timestamp), etc.
        """
        return np.array([])

    def process(self, data: DataTuple, **kwargs) -> Tuple[NDArray, NDArray, float, int]:
        """
        Process the data on user-defined strategy (run method), and calculate returns, equity curve, win rate and number of trades.
        
        Args:
            data (DataTuple): The data to process.
                             Format: (symbol, timestamps, opens, highs, lows, closes, volume)
            **kwargs: Strategy parameters.
            
        Returns:
            Tuple[np.ndarray, np.ndarray, float, int]: Tuple containing (returns, equity_curve, win_rate, no_of_trades)
        """
        returns = self.run(data, **kwargs)
        total_trades = len(returns)
        equity_curve = np.cumprod(1 + returns)
        win_rate = np.sum(returns > 0) / total_trades if total_trades > 0 else 0.0
        return returns, equity_curve, win_rate, total_trades

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
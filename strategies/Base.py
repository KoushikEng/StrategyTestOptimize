from abc import ABC, abstractmethod
from typing import Tuple
from numpy.typing import NDArray
import numpy as np

class Base(ABC):
    """Base class for strategies.
    """
    

    def __init__(self):
        pass
    
    @abstractmethod
    def run(self, data, **kwargs) -> NDArray:
        """
        Run the strategy on the given data.
        
        Args:
            data (DataTuple): The data to run on.
            **kwargs: Strategy parameters.
            
        Returns:
            np.ndarray: Returns on each trade
        """
        pass

    def process(self, data, **kwargs) -> Tuple[NDArray, NDArray, float, int]:
        """
        Process the data on user-defined strategy (run method), and calculate returns, equity curve, win rate and number of trades.
        
        Args:
            data (DataTuple): The data to process.
            **kwargs: Strategy parameters.
            
        Returns:
            Tuple[np.ndarray, np.ndarray, float, int]: Tuple containing (returns, equity_curve, win_rate, no_of_trades)
        """
        returns = self.run(data, **kwargs)
        total_trades = len(returns)
        equity_curve = np.cumprod(1 + returns)
        win_rate = np.sum(returns > 0) / total_trades if total_trades > 0 else 0.0
        return returns, equity_curve, win_rate, total_trades

    @staticmethod
    @abstractmethod
    def get_optimization_params():
        """
        Get the optimization parameters for the strategy.
        
        Returns:
            Dict[str, Tuple[float, float]]: Dictionary containing the optimization parameters.
        """
        pass
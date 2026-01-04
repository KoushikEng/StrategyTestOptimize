from abc import ABC, abstractmethod

class Base(ABC):
    """Base class for strategies.
    """
    

    @abstractmethod
    def init(self):
        pass
    
    @abstractmethod
    def run(self, data, **kwargs):
        """
        Run the strategy on the given data.
        
        Args:
            data (DataTuple): The data to run on.
            **kwargs: Strategy parameters.
            
        Returns:
            Tuple[np.ndarray, np.ndarray, float]: Tuple containing (returns, equity_curve, win_rate)
        """
        pass
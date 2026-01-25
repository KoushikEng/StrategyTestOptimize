"""
Enhanced Moving Average Crossover Strategy

This strategy demonstrates the new enhanced Base class interface with:
- Clean init() and next() methods
- Efficient pre-calculated indicators with dynamic slicing
- Automatic look-ahead prevention
- Built-in position management with buy/sell methods
- Array-like indicator access (indicator[-1], indicator.values)
"""

from strategies.Base import Base
import numpy as np
from Utilities import DataTuple


def simple_moving_average(prices: np.ndarray, period: int) -> np.ndarray:
    """
    Calculate Simple Moving Average using numpy convolution.
    
    Args:
        prices: Array of price values
        period: Moving average period
        
    Returns:
        Array of SMA values with same length as input
    """
    if period <= 0:
        raise ValueError("Period must be positive")
    if period > len(prices):
        raise ValueError("Period cannot be larger than data length")
    
    # Use convolution for efficient SMA calculation
    weights = np.ones(period) / period
    sma = np.convolve(prices, weights, mode='same')
    
    # Fix the edges by using available data
    for i in range(min(period-1, len(prices))):
        if i == 0:
            sma[i] = prices[i]
        else:
            sma[i] = np.mean(prices[:i+1])
    
    return sma


def exponential_moving_average(prices: np.ndarray, period: int) -> np.ndarray:
    """
    Calculate Exponential Moving Average.
    
    Args:
        prices: Array of price values
        period: EMA period
        
    Returns:
        Array of EMA values with same length as input
    """
    if period <= 0:
        raise ValueError("Period must be positive")
    
    alpha = 2.0 / (period + 1)
    ema = np.zeros_like(prices)
    ema[0] = prices[0]
    
    for i in range(1, len(prices)):
        ema[i] = alpha * prices[i] + (1 - alpha) * ema[i-1]
    
    return ema


class EnhancedMACross(Base):
    """
    Enhanced Moving Average Crossover Strategy using the new Base interface.
    
    This strategy:
    1. Uses two moving averages (fast and slow)
    2. Buys when fast MA crosses above slow MA
    3. Sells when fast MA crosses below slow MA
    4. Demonstrates clean init()/next() interface
    5. Shows efficient indicator caching
    6. Uses built-in position management
    """
    
    def init(self):
        """
        Initialize strategy indicators and parameters.
        
        This method is called once before processing any bars.
        All indicators are pre-calculated here for efficiency.
        """
        self.use_ema = False
        self.fast_period = 10
        self.slow_period = 30
        
        # Get full price data for indicator calculation
        closes = self.data.Close
        
        # Choose MA type based on strategy parameter
        ma_func = exponential_moving_average if self.use_ema else simple_moving_average
        
        # Register indicators - they will be cached automatically
        # Multiple calls with same parameters return the same cached object
        self.fast_ma = self.I(ma_func, closes, self.fast_period)
        self.slow_ma = self.I(ma_func, closes, self.slow_period)
        
        print(f"Initialized {self.__class__.__name__} with:")
        print(f"  Fast MA: {self.fast_period} periods ({'EMA' if self.use_ema else 'SMA'})")
        print(f"  Slow MA: {self.slow_period} periods ({'EMA' if self.use_ema else 'SMA'})")
        print(f"  Data length: {len(closes)} bars")
    
    def next(self):
        """
        Process the current bar.
        
        This method is called once for each bar in the dataset.
        It has access to current and historical data through indicators.
        """
        # Need at least slow_period bars for valid signals
        if len(self) < self.slow_period:
            return
        
        # Get current and previous MA values using array-like access
        # -1 refers to current bar, -2 to previous bar, etc.
        fast_current = self.fast_ma[-1]
        fast_previous = self.fast_ma[-2]
        slow_current = self.slow_ma[-1]
        slow_previous = self.slow_ma[-2]
        
        # Current price for reference
        current_price = self.data.Close[-1]
        
        # Check for crossover signals
        if not self.position['in_position']:
            # Look for bullish crossover: fast MA crosses above slow MA
            if fast_current > slow_current and fast_previous <= slow_previous:
                self.buy(1.0)  # Buy with position size 1.0
                print(f"BUY at bar {len(self)-1}: Price={current_price:.2f}, "
                      f"Fast MA={fast_current:.2f}, Slow MA={slow_current:.2f}")
        
        else:
            # Look for bearish crossover: fast MA crosses below slow MA
            if fast_current < slow_current and fast_previous >= slow_previous:
                trade_return = self.sell()  # Sell and get return
                print(f"SELL at bar {len(self)-1}: Price={current_price:.2f}, "
                      f"Fast MA={fast_current:.2f}, Slow MA={slow_current:.2f}, "
                      f"Return={trade_return:.4f}")
    
    def __len__(self):
        """Return current data length (number of bars processed so far)."""
        return self._context.get_current_index() + 1
    
    def validate_params(self, fast_period=10, slow_period=30, use_ema=False, **kwargs) -> bool:
        """
        Validate strategy parameters.
        
        Args:
            fast_period: Fast moving average period
            slow_period: Slow moving average period
            use_ema: Whether to use EMA instead of SMA
            
        Returns:
            True if parameters are valid, False otherwise
        """
        if not isinstance(fast_period, int) or fast_period <= 0:
            return False
        if not isinstance(slow_period, int) or slow_period <= 0:
            return False
        if fast_period >= slow_period:
            return False
        if not isinstance(use_ema, bool):
            return False
        
        # Update instance parameters
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.use_ema = use_ema
        
        return True
    
    @staticmethod
    def get_optimization_params():
        """
        Get parameter ranges for optimization.
        
        Returns:
            Dictionary with parameter names and (min, max) ranges
        """
        return {
            "fast_period": (5, 50),
            "slow_period": (20, 200),
            "use_ema": (False, True)  # Boolean parameter
        }
    
    def get_strategy_info(self) -> dict:
        """
        Get information about the current strategy state.
        
        Returns:
            Dictionary with strategy information
        """
        return {
            'name': self.__class__.__name__,
            'fast_period': self.fast_period,
            'slow_period': self.slow_period,
            'ma_type': 'EMA' if self.use_ema else 'SMA',
            'current_position': self.position,
            'total_trades': len(self._position_manager.trades),
            'indicators_cached': len(self._indicators)
        }


# Example usage and testing
if __name__ == "__main__":
    # This demonstrates how to use the enhanced strategy
    
    # Create sample data for testing
    data_length = 100
    symbol = "EXAMPLE"
    timestamps = np.arange(1600000000, 1600000000 + data_length, dtype=np.int64)
    
    # Create trending price data with some noise
    base_price = 100.0
    trend = np.linspace(0, 20, data_length)  # Upward trend
    noise = np.random.normal(0, 2, data_length)  # Random noise
    closes = base_price + trend + noise
    
    # Create OHLC data
    opens = closes - np.random.uniform(0, 1, data_length)
    highs = closes + np.random.uniform(0, 2, data_length)
    lows = closes - np.random.uniform(0, 1, data_length)
    volume = np.random.randint(1000, 10000, data_length, dtype=np.int64)
    
    # Create DataTuple
    data_tuple = (symbol, timestamps, opens, highs, lows, closes, volume)
    
    # Create and run strategy
    strategy = EnhancedMACross()
    
    # Set custom parameters
    strategy.validate_params(fast_period=5, slow_period=20, use_ema=True)
    
    print("Running Enhanced MA Crossover Strategy...")
    print("=" * 50)
    
    # Run the strategy
    returns, equity_curve, win_rate, total_trades = strategy.process(data_tuple)
    
    print("=" * 50)
    print("Strategy Results:")
    print(f"Total Trades: {total_trades}")
    print(f"Win Rate: {win_rate:.2%}")
    if total_trades > 0:
        print(f"Average Return: {np.mean(returns):.4f}")
        print(f"Total Return: {equity_curve[-1] - 1:.4f}")
        print(f"Best Trade: {np.max(returns):.4f}")
        print(f"Worst Trade: {np.min(returns):.4f}")
    
    # Show strategy info
    print("\nStrategy Configuration:")
    info = strategy.get_strategy_info()
    for key, value in info.items():
        print(f"  {key}: {value}")
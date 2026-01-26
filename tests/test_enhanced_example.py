"""
Test script for the EnhancedMACross example strategy.
"""

import numpy as np
from strategies.EnhancedMACross import EnhancedMACross

def test_enhanced_example():
    """Test the enhanced MA crossover example strategy."""
    
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
    assert strategy.validate_params(fast_period=5, slow_period=20, use_ema=True)
    
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
    
    # Verify the strategy worked correctly
    assert isinstance(returns, np.ndarray), "Returns should be numpy array"
    assert isinstance(equity_curve, np.ndarray), "Equity curve should be numpy array"
    assert isinstance(win_rate, float), "Win rate should be float"
    assert isinstance(total_trades, int), "Total trades should be int"
    
    print("\n✅ Enhanced strategy example test passed!")

if __name__ == "__main__":
    test_enhanced_example()
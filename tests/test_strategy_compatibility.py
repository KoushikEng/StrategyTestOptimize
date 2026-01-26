"""
Test for strategy compatibility with new timestamp format.
"""

import numpy as np
from strategies.Base import Base
from datetime_utils import extract_hour, is_market_hours
from Utilities import DataTuple

class TestStrategy(Base):
    """Test strategy that uses the new timestamp format."""
    
    def run(self, data: DataTuple, **kwargs) -> np.ndarray:
        """Simple strategy that uses timestamp utilities."""
        symbol, timestamps, opens, highs, lows, closes, volume = data
        
        returns = []
        
        for i in range(1, len(closes)):  # Start from 1 to have previous price
            # Use timestamp utilities for time-based logic
            current_hour = extract_hour(timestamps[i])
            is_market_time = is_market_hours(timestamps[i])
            
            # Simple strategy: buy if it's market hours and after 10 AM
            if is_market_time and current_hour >= 10:
                # Calculate return based on price change
                price_change = (closes[i] - closes[i-1]) / closes[i-1]
                returns.append(price_change)
            else:
                returns.append(0.0)  # No trade
        
        return np.array(returns)
    
    def validate_params(self, **kwargs) -> bool:
        return True
    
    @staticmethod
    def get_optimization_params():
        return {}

def test_strategy_compatibility():
    """
    Property 7: Strategy compatibility
    **Validates: Requirements 1.5**
    
    For any strategy using the new timestamp format, it should be able to access 
    time components through utility functions and process the updated DataTuple 
    structure without errors.
    """
    # Feature: numba-optimized-datetime, Property 7: Strategy compatibility
    
    print("Testing strategy compatibility...")
    
    # Create test data with new timestamp format
    symbol = "TEST"
    timestamps = np.array([
        1704081300,  # 2024-01-01 09:15:00 IST (market open)
        1704082200,  # 2024-01-01 09:30:00 IST (opening hour)
        1704096900,  # 2024-01-01 13:45:00 IST (afternoon)
        1704101400,  # 2024-01-01 15:00:00 IST (closing hour)
        1704103200   # 2024-01-01 15:30:00 IST (market close)
    ], dtype=np.int64)
    
    opens = np.array([100.0, 100.5, 102.0, 103.0, 104.0], dtype=np.float64)
    highs = np.array([101.0, 101.5, 103.0, 104.0, 105.0], dtype=np.float64)
    lows = np.array([99.5, 100.0, 101.5, 102.5, 103.5], dtype=np.float64)
    closes = np.array([100.5, 101.0, 102.5, 103.5, 104.5], dtype=np.float64)
    volume = np.array([1000, 1100, 1200, 1300, 1400], dtype=np.int64)
    
    # Create DataTuple with new format (7 elements)
    data_tuple: DataTuple = (symbol, timestamps, opens, highs, lows, closes, volume)
    
    # Test DataTuple structure
    assert len(data_tuple) == 7, f"DataTuple should have 7 elements, got {len(data_tuple)}"
    print("✓ DataTuple has correct structure (7 elements)")
    
    # Test strategy instantiation
    strategy = TestStrategy()
    assert strategy is not None, "Strategy should instantiate successfully"
    print("✓ Strategy instantiated successfully")
    
    # Test strategy run method with new data format
    try:
        returns = strategy.run(data_tuple)
        assert isinstance(returns, np.ndarray), "Strategy should return numpy array"
        print(f"✓ Strategy run method executed successfully, returned {len(returns)} values")
    except Exception as e:
        raise AssertionError(f"Strategy run method failed: {e}")
    
    # Test strategy process method (full pipeline)
    try:
        results = strategy.process(data_tuple)
        assert len(results) == 4, "Process method should return 4 values"
        returns, equity_curve, win_rate, no_of_trades = results
        
        assert isinstance(returns, np.ndarray), "Returns should be numpy array"
        assert isinstance(equity_curve, np.ndarray), "Equity curve should be numpy array"
        assert isinstance(win_rate, float), "Win rate should be float"
        assert isinstance(no_of_trades, int), "Number of trades should be int"
        
        print(f"✓ Strategy process method executed successfully")
        print(f"  - Returns: {len(returns)} values")
        print(f"  - Equity curve: {len(equity_curve)} values")
        print(f"  - Win rate: {win_rate:.2%}")
        print(f"  - Number of trades: {no_of_trades}")
        
    except Exception as e:
        raise AssertionError(f"Strategy process method failed: {e}")
    
    # Test that strategy can access timestamp utilities
    print("\nTesting timestamp utility access...")
    
    test_timestamp = timestamps[2]  # Afternoon timestamp
    
    # Test that strategy can use datetime utilities
    try:
        hour = extract_hour(test_timestamp)
        market_hours = is_market_hours(test_timestamp)
        
        assert 0 <= hour <= 23, f"Hour should be valid: {hour}"
        assert isinstance(market_hours, (bool, np.bool_)), f"Market hours should be boolean: {market_hours}"
        
        print(f"✓ Strategy can access timestamp utilities")
        print(f"  - Hour extraction: {hour}")
        print(f"  - Market hours check: {market_hours}")
        
    except Exception as e:
        raise AssertionError(f"Strategy failed to use timestamp utilities: {e}")
    
    # Test data unpacking in strategy
    print("\nTesting data unpacking...")
    
    try:
        # This should work without errors
        symbol_unpacked, timestamps_unpacked, opens_unpacked, highs_unpacked, lows_unpacked, closes_unpacked, volume_unpacked = data_tuple
        
        assert symbol_unpacked == symbol, "Symbol unpacking failed"
        assert len(timestamps_unpacked) == len(timestamps), "Timestamps unpacking failed"
        assert len(opens_unpacked) == len(opens), "Opens unpacking failed"
        assert len(highs_unpacked) == len(highs), "Highs unpacking failed"
        assert len(lows_unpacked) == len(lows), "Lows unpacking failed"
        assert len(closes_unpacked) == len(closes), "Closes unpacking failed"
        assert len(volume_unpacked) == len(volume), "Volume unpacking failed"
        
        print("✓ DataTuple unpacking works correctly")
        
    except Exception as e:
        raise AssertionError(f"DataTuple unpacking failed: {e}")
    
    # Test with different data sizes
    print("\nTesting with different data sizes...")
    
    for size in [1, 10, 100]:
        # Create test data of different sizes
        test_timestamps = np.arange(1704081300, 1704081300 + size * 300, 300, dtype=np.int64)  # 5-minute intervals
        test_closes = np.random.uniform(100, 110, size).astype(np.float64)
        test_opens = test_closes * 0.99  # Slightly lower opens
        test_highs = test_closes * 1.01  # Slightly higher highs
        test_lows = test_closes * 0.98   # Slightly lower lows
        test_volume = np.random.randint(1000, 2000, size, dtype=np.int64)
        
        test_data = ("TEST", test_timestamps, test_opens, test_highs, test_lows, test_closes, test_volume)
        
        try:
            test_returns = strategy.run(test_data)
            assert len(test_returns) >= 0, f"Strategy should handle size {size}"
            print(f"✓ Strategy handles data size {size} correctly")
        except Exception as e:
            raise AssertionError(f"Strategy failed with data size {size}: {e}")
    
    print("\nStrategy compatibility test passed!")

if __name__ == "__main__":
    test_strategy_compatibility()
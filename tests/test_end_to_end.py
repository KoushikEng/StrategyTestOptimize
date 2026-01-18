"""
End-to-end integration tests for the complete numba-optimized datetime workflow.
"""

import os
import tempfile
import numpy as np
from Utilities import process_symbol_data, read_from_csv, DataTuple
from strategies.Base import Base
from datetime_utils import (
    extract_hour_vectorized, is_market_hours_vectorized,
    is_opening_hour_vectorized, is_closing_hour_vectorized
)
import numba

class EndToEndTestStrategy(Base):
    """Test strategy that uses vectorized datetime utilities for end-to-end testing."""
    
    def run(self, data: DataTuple, **kwargs) -> np.ndarray:
        """Strategy that uses vectorized datetime utilities and numba compilation."""
        symbol, timestamps, opens, highs, lows, closes, volume = data
        
        if len(timestamps) < 2:
            return np.array([])
        
        # Use vectorized datetime utilities
        hours = extract_hour_vectorized(timestamps)
        market_hours_mask = is_market_hours_vectorized(timestamps)
        opening_hour_mask = is_opening_hour_vectorized(timestamps)
        closing_hour_mask = is_closing_hour_vectorized(timestamps)
        
        returns = []
        
        for i in range(1, len(closes)):
            # Only trade during market hours
            if market_hours_mask[i]:
                # Different logic for different times
                if opening_hour_mask[i]:
                    # Opening hour: more conservative
                    if closes[i] > closes[i-1]:
                        returns.append(0.001)  # Small positive return
                    else:
                        returns.append(-0.001)  # Small negative return
                elif closing_hour_mask[i]:
                    # Closing hour: more aggressive
                    price_change = (closes[i] - closes[i-1]) / closes[i-1]
                    returns.append(price_change * 1.5)  # Amplified return
                else:
                    # Regular hours: normal logic
                    price_change = (closes[i] - closes[i-1]) / closes[i-1]
                    returns.append(price_change)
            else:
                # No trading outside market hours
                returns.append(0.0)
        
        return np.array(returns)
    
    def validate_params(self, **kwargs) -> bool:
        return True
    
    @staticmethod
    def get_optimization_params():
        return {}

def test_end_to_end_workflow():
    """
    Test complete pipeline: download → store → load → execute strategy
    Verify no string conversions occur during processing
    **Validates: Requirements 1.1, 1.3, 1.5**
    """
    print("Testing end-to-end workflow...")
    
    # Step 1: Create test data (simulating TvDatafeed output)
    print("Step 1: Creating test data...")
    
    # Generate realistic market data spanning different time periods
    base_timestamp = 1704081300  # 2024-01-01 09:15:00 IST (market open)
    num_points = 50
    
    test_data = []
    current_price = 100.0
    
    for i in range(num_points):
        timestamp = base_timestamp + i * 300  # 5-minute intervals
        
        # Simulate price movement
        price_change = np.random.uniform(-0.02, 0.02)  # ±2% change
        current_price *= (1 + price_change)
        
        open_price = current_price
        high_price = current_price * (1 + abs(price_change) * 0.5)
        low_price = current_price * (1 - abs(price_change) * 0.5)
        close_price = current_price
        volume = np.random.randint(1000, 5000)
        
        test_data.append([timestamp, open_price, high_price, low_price, close_price, volume])
    
    print(f"✓ Generated {len(test_data)} data points")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = temp_dir + "/"
        symbol = "E2E_TEST"
        
        # Step 2: Process and store data (no string conversions)
        print("Step 2: Processing and storing data...")
        
        process_symbol_data(test_data, temp_path, symbol)
        
        # Verify CSV file was created
        csv_file = f"{temp_path}{symbol}.csv"
        assert os.path.exists(csv_file), f"CSV file not created: {csv_file}"
        print(f"✓ CSV file created: {csv_file}")
        
        # Step 3: Load data using updated read_from_csv
        print("Step 3: Loading data...")
        
        data_tuple = read_from_csv(symbol, temp_path)
        
        # Verify data structure
        assert len(data_tuple) == 7, f"DataTuple should have 7 elements, got {len(data_tuple)}"
        symbol_loaded, timestamps, opens, highs, lows, closes, volume = data_tuple
        
        assert symbol_loaded == symbol, f"Symbol mismatch: {symbol_loaded} != {symbol}"
        assert len(timestamps) == num_points, f"Data length mismatch: {len(timestamps)} != {num_points}"
        
        # Verify data types are numba-compatible
        assert timestamps.dtype == np.int64, f"Timestamps should be int64, got {timestamps.dtype}"
        assert opens.dtype == np.float64, f"Opens should be float64, got {opens.dtype}"
        assert highs.dtype == np.float64, f"Highs should be float64, got {highs.dtype}"
        assert lows.dtype == np.float64, f"Lows should be float64, got {lows.dtype}"
        assert closes.dtype == np.float64, f"Closes should be float64, got {closes.dtype}"
        assert volume.dtype == np.int64, f"Volume should be int64, got {volume.dtype}"
        
        print("✓ Data loaded with correct types and structure")
        
        # Step 4: Execute strategy with vectorized datetime utilities
        print("Step 4: Executing strategy...")
        
        strategy = EndToEndTestStrategy()
        
        # Test strategy execution
        returns = strategy.run(data_tuple)
        assert isinstance(returns, np.ndarray), "Strategy should return numpy array"
        assert len(returns) > 0, "Strategy should generate some returns"
        
        print(f"✓ Strategy executed successfully, generated {len(returns)} returns")
        
        # Test full strategy processing pipeline
        results = strategy.process(data_tuple)
        returns, equity_curve, win_rate, no_of_trades = results
        
        assert isinstance(returns, np.ndarray), "Returns should be numpy array"
        assert isinstance(equity_curve, np.ndarray), "Equity curve should be numpy array"
        assert isinstance(win_rate, float), "Win rate should be float"
        assert isinstance(no_of_trades, int), "Number of trades should be int"
        
        print(f"✓ Strategy processing completed:")
        print(f"  - Returns: {len(returns)} values")
        print(f"  - Win rate: {win_rate:.2%}")
        print(f"  - Number of trades: {no_of_trades}")
        print(f"  - Final equity: {equity_curve[-1]:.4f}")
        
        # Step 5: Test numba compilation of strategy components
        print("Step 5: Testing numba compilation...")
        
        @numba.jit(nopython=True)
        def numba_strategy_component(timestamps, closes):
            """Numba-compiled strategy component using datetime utilities."""
            results = []
            market_mask = is_market_hours_vectorized(timestamps)
            
            for i in range(1, len(closes)):
                if market_mask[i]:
                    price_change = (closes[i] - closes[i-1]) / closes[i-1]
                    results.append(price_change)
                else:
                    results.append(0.0)
            
            return np.array(results)
        
        # This should compile and run without errors
        numba_returns = numba_strategy_component(timestamps, closes)
        assert isinstance(numba_returns, np.ndarray), "Numba strategy should return numpy array"
        assert len(numba_returns) == len(returns), "Numba returns should match strategy returns length"
        
        print("✓ Numba compilation successful")
        
        # Step 6: Verify no string datetime operations occurred
        print("Step 6: Verifying no string operations...")
        
        # Check that timestamps are raw integers
        for i, timestamp in enumerate(timestamps[:5]):  # Check first 5
            assert isinstance(timestamp, (int, np.integer)), f"Timestamp {i} is not integer: {type(timestamp)}"
            assert timestamp > 1000000000, f"Timestamp {i} doesn't look like Unix timestamp: {timestamp}"
        
        print("✓ All timestamps are raw integers (no string conversions)")
        
        # Step 7: Test data integrity throughout pipeline
        print("Step 7: Testing data integrity...")
        
        # Verify that original data is preserved
        for i in range(min(5, len(test_data))):  # Check first 5 rows
            original_timestamp = test_data[i][0]
            loaded_timestamp = timestamps[i]
            
            assert original_timestamp == loaded_timestamp, \
                f"Timestamp {i} not preserved: {original_timestamp} != {loaded_timestamp}"
            
            # Check price data (allowing for small floating point differences)
            original_close = test_data[i][4]
            loaded_close = closes[i]
            
            assert abs(original_close - loaded_close) < 1e-10, \
                f"Close price {i} not preserved: {original_close} != {loaded_close}"
        
        print("✓ Data integrity maintained throughout pipeline")
        
        # Step 8: Performance verification
        print("Step 8: Performance verification...")
        
        # Test that vectorized operations work on the full dataset
        hours = extract_hour_vectorized(timestamps)
        market_hours = is_market_hours_vectorized(timestamps)
        
        assert len(hours) == len(timestamps), "Vectorized hours should match timestamp length"
        assert len(market_hours) == len(timestamps), "Vectorized market hours should match timestamp length"
        
        # Count market hours vs non-market hours
        market_count = np.sum(market_hours)
        non_market_count = len(market_hours) - market_count
        
        print(f"✓ Vectorized operations completed:")
        print(f"  - Market hours data points: {market_count}")
        print(f"  - Non-market hours data points: {non_market_count}")
        
    print("\nEnd-to-end workflow test passed!")

if __name__ == "__main__":
    test_end_to_end_workflow()
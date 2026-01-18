"""
Integration test to verify the complete pipeline works.
"""

import os
import tempfile
from Utilities import process_symbol_data, read_from_csv
from datetime_utils import extract_hour, extract_minute

def test_integration():
    """Test the complete pipeline: process -> save -> read -> use utilities."""
    print("Testing complete integration...")
    
    # Sample data as it would come from TvDatafeed
    test_data = [
        [1704096900, 100.0, 101.0, 99.5, 100.5, 1000],  # 2024-01-01 13:45:00 IST
        [1704097200, 101.0, 102.0, 100.0, 101.5, 1100], # 2024-01-01 13:50:00 IST
        [1704097500, 102.0, 103.0, 101.0, 102.5, 1200]  # 2024-01-01 13:55:00 IST
    ]
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = temp_dir + "/"
        symbol = "INTEGRATION_TEST"
        
        # Step 1: Process and save data
        print("Step 1: Processing and saving data...")
        process_symbol_data(test_data, temp_path, symbol)
        
        # Step 2: Read data back
        print("Step 2: Reading data back...")
        data_tuple = read_from_csv(symbol, temp_path)
        
        # Step 3: Verify data structure
        print("Step 3: Verifying data structure...")
        assert len(data_tuple) == 7, f"Expected 7 elements, got {len(data_tuple)}"
        symbol_name, timestamps, opens, highs, lows, closes, volume = data_tuple
        
        assert symbol_name == symbol, f"Symbol mismatch: {symbol_name} != {symbol}"
        assert len(timestamps) == 3, f"Expected 3 timestamps, got {len(timestamps)}"
        
        # Step 4: Use datetime utilities with the loaded data
        print("Step 4: Using datetime utilities...")
        for i, timestamp in enumerate(timestamps):
            hour = extract_hour(timestamp)
            minute = extract_minute(timestamp)
            print(f"  Timestamp {timestamp}: {hour:02d}:{minute:02d}")
            
            # Verify the time extraction makes sense
            assert 0 <= hour <= 23, f"Invalid hour: {hour}"
            assert 0 <= minute <= 59, f"Invalid minute: {minute}"
        
        # Step 5: Verify data integrity
        print("Step 5: Verifying data integrity...")
        for i in range(len(test_data)):
            assert timestamps[i] == test_data[i][0], f"Timestamp {i} mismatch"
            assert opens[i] == test_data[i][1], f"Open {i} mismatch"
            assert highs[i] == test_data[i][2], f"High {i} mismatch"
            assert lows[i] == test_data[i][3], f"Low {i} mismatch"
            assert closes[i] == test_data[i][4], f"Close {i} mismatch"
            assert volume[i] == test_data[i][5], f"Volume {i} mismatch"
        
        print("✓ All data integrity checks passed")
        
        # Step 6: Test numba compatibility
        print("Step 6: Testing numba compatibility...")
        import numba
        
        @numba.jit(nopython=True)
        def simple_strategy(timestamps, closes):
            """Simple strategy using timestamps and closes."""
            results = []
            for i in range(len(timestamps)):
                hour = extract_hour(timestamps[i])
                if hour >= 13:  # Trade after 1 PM
                    results.append(closes[i])
            return results
        
        # This should compile and run without errors
        strategy_results = simple_strategy(timestamps, closes)
        print(f"✓ Numba strategy executed successfully, got {len(strategy_results)} results")
        
    print("Integration test passed!")

if __name__ == "__main__":
    test_integration()
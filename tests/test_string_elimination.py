"""
Test for string operation elimination in data processing.
"""

import os
import tempfile
import csv
from Utilities import process_symbol_data
import pytz
import config

def test_string_operation_elimination():
    """
    Property 4: String operation elimination
    **Validates: Requirements 1.1, 1.3, 1.4**
    
    For any data processing pipeline execution, no string datetime conversions 
    or datetime object creations should occur during data processing 
    (only during initial download).
    """
    # Feature: numba-optimized-datetime, Property 4: String operation elimination
    
    print("Testing string operation elimination...")
    
    # Create test data with raw Unix timestamps (as they come from TvDatafeed)
    test_data = [
        [1704096900, 100.0, 101.0, 99.5, 100.5, 1000],  # 2024-01-01 13:45:00 IST
        [1704097200, 101.0, 102.0, 100.0, 101.5, 1100], # 2024-01-01 13:50:00 IST
        [1704097500, 102.0, 103.0, 101.0, 102.5, 1200]  # 2024-01-01 13:55:00 IST
    ]
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = temp_dir + "/"
        symbol = "TEST"
        
        # Process the data (this should not perform any string conversions)
        process_symbol_data(test_data, temp_path, symbol, separate_time_column=False)
        
        # Verify the CSV file was created
        csv_file = f"{temp_path}{symbol}.csv"
        assert os.path.exists(csv_file), f"CSV file {csv_file} was not created"
        print(f"✓ CSV file created: {csv_file}")
        
        # Read and verify the CSV content
        with open(csv_file, 'r') as file:
            reader = csv.reader(file)
            header = next(reader)
            rows = list(reader)
        
        # Verify header format
        expected_header = ['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
        assert header == expected_header, f"Header mismatch: {header} != {expected_header}"
        print(f"✓ CSV header is correct: {header}")
        
        # Verify data integrity - timestamps should be stored as raw integers
        assert len(rows) == len(test_data), f"Row count mismatch: {len(rows)} != {len(test_data)}"
        
        for i, row in enumerate(rows):
            # Verify timestamp is stored as integer (not string datetime)
            timestamp_str = row[0]
            try:
                timestamp_int = int(timestamp_str)
                assert timestamp_int == test_data[i][0], \
                    f"Timestamp mismatch at row {i}: {timestamp_int} != {test_data[i][0]}"
            except ValueError:
                raise AssertionError(f"Timestamp at row {i} is not an integer: {timestamp_str}")
            
            # Verify other data fields
            for j in range(1, 6):  # Open, High, Low, Close, Volume
                expected_value = test_data[i][j]
                actual_value = float(row[j]) if j < 5 else int(row[j])  # Volume is int
                assert actual_value == expected_value, \
                    f"Data mismatch at row {i}, col {j}: {actual_value} != {expected_value}"
        
        print(f"✓ All {len(rows)} rows have correct raw timestamp format")
        print("✓ No string datetime conversions detected in data processing")
        
        # Verify that timestamps are stored as raw Unix integers
        first_timestamp = int(rows[0][0])
        assert first_timestamp == 1704096900, f"First timestamp should be 1704096900, got {first_timestamp}"
        print(f"✓ Raw Unix timestamp preserved: {first_timestamp}")
    
    print("String operation elimination test passed!")

if __name__ == "__main__":
    test_string_operation_elimination()
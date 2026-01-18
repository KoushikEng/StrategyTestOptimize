"""
Test for CSV format compliance.
"""

import os
import tempfile
import csv
from Utilities import process_symbol_data

def test_csv_format_compliance():
    """
    Property 5: CSV format compliance
    **Validates: Requirements 1.1, 1.3**
    
    For any generated CSV file, the header should be exactly 
    "timestamp,Open,High,Low,Close,Volume" and all timestamp values 
    should be stored as raw integers.
    """
    # Feature: numba-optimized-datetime, Property 5: CSV format compliance
    
    print("Testing CSV format compliance...")
    
    # Test with various data scenarios
    test_scenarios = [
        {
            "name": "Basic data",
            "data": [
                [1704096900, 100.0, 101.0, 99.5, 100.5, 1000],
                [1704097200, 101.0, 102.0, 100.0, 101.5, 1100]
            ]
        },
        {
            "name": "Single row",
            "data": [
                [1609459200, 50.0, 51.0, 49.5, 50.5, 500]
            ]
        },
        {
            "name": "Large numbers",
            "data": [
                [1577836800, 1000.0, 1001.0, 999.0, 1000.5, 10000],
                [1577837100, 1001.0, 1002.0, 1000.0, 1001.5, 11000]
            ]
        }
    ]
    
    expected_header = ['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
    
    for scenario in test_scenarios:
        print(f"\nTesting scenario: {scenario['name']}")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = temp_dir + "/"
            symbol = f"TEST_{scenario['name'].replace(' ', '_').upper()}"
            
            # Process the data
            process_symbol_data(scenario['data'], temp_path, symbol)
            
            # Verify CSV file exists
            csv_file = f"{temp_path}{symbol}.csv"
            assert os.path.exists(csv_file), f"CSV file not created for {scenario['name']}"
            
            # Read and verify CSV content
            with open(csv_file, 'r') as file:
                reader = csv.reader(file)
                header = next(reader)
                rows = list(reader)
            
            # Test header compliance
            assert header == expected_header, \
                f"Header mismatch in {scenario['name']}: {header} != {expected_header}"
            print(f"✓ Header is correct: {header}")
            
            # Test data row count
            assert len(rows) == len(scenario['data']), \
                f"Row count mismatch in {scenario['name']}: {len(rows)} != {len(scenario['data'])}"
            
            # Test timestamp format (should be raw integers)
            for i, row in enumerate(rows):
                # Verify timestamp is stored as integer string (not datetime string)
                timestamp_str = row[0]
                
                # Should be able to convert to int without error
                try:
                    timestamp_int = int(timestamp_str)
                except ValueError:
                    raise AssertionError(
                        f"Timestamp in {scenario['name']}, row {i} is not an integer: {timestamp_str}"
                    )
                
                # Should match original timestamp
                expected_timestamp = scenario['data'][i][0]
                assert timestamp_int == expected_timestamp, \
                    f"Timestamp mismatch in {scenario['name']}, row {i}: {timestamp_int} != {expected_timestamp}"
                
                # Should not contain datetime formatting characters
                invalid_chars = ['-', ':', ' ', 'T', 'Z']
                for char in invalid_chars:
                    assert char not in timestamp_str, \
                        f"Timestamp contains datetime formatting character '{char}': {timestamp_str}"
            
            print(f"✓ All {len(rows)} timestamps are raw integers")
            
            # Test that all columns have expected number of values
            for i, row in enumerate(rows):
                assert len(row) == 6, \
                    f"Row {i} in {scenario['name']} has {len(row)} columns, expected 6"
            
            print(f"✓ All rows have correct number of columns (6)")
            
            # Test data integrity for other columns
            for i, row in enumerate(rows):
                expected_row = scenario['data'][i]
                
                # Test Open, High, Low, Close (should be floats)
                for j in range(1, 5):
                    try:
                        actual_value = float(row[j])
                        expected_value = expected_row[j]
                        assert actual_value == expected_value, \
                            f"Price data mismatch in {scenario['name']}, row {i}, col {j}"
                    except ValueError:
                        raise AssertionError(f"Price data is not numeric: {row[j]}")
                
                # Test Volume (should be integer)
                try:
                    actual_volume = int(row[5])
                    expected_volume = expected_row[5]
                    assert actual_volume == expected_volume, \
                        f"Volume mismatch in {scenario['name']}, row {i}"
                except ValueError:
                    raise AssertionError(f"Volume is not integer: {row[5]}")
            
            print(f"✓ All data values are correctly formatted and preserved")
    
    print("\nCSV format compliance test passed!")

if __name__ == "__main__":
    test_csv_format_compliance()
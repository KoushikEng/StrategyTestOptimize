"""
Comprehensive demonstration of the numba-optimized datetime feature.
"""

import numpy as np
import tempfile
from datetime import datetime, timezone, timedelta
from Utilities import process_symbol_data, read_from_csv
from datetime_utils import *
from strategies.Base import Base
import numba

class DemoStrategy(Base):
    """Demonstration strategy showcasing all datetime optimization features."""
    
    def run(self, data, **kwargs):
        """Strategy using all datetime optimization features."""
        symbol, timestamps, opens, highs, lows, closes, volume = data
        
        if len(timestamps) < 2:
            return np.array([])
        
        # Use vectorized datetime utilities for maximum performance
        hours = extract_hour_vectorized(timestamps)
        market_hours_mask = is_market_hours_vectorized(timestamps)
        opening_hour_mask = is_opening_hour_vectorized(timestamps)
        closing_hour_mask = is_closing_hour_vectorized(timestamps)
        
        returns = []
        
        for i in range(1, len(closes)):
            if market_hours_mask[i]:
                # Time-based trading logic
                if opening_hour_mask[i]:
                    # Conservative trading in opening hour
                    if closes[i] > opens[i]:
                        returns.append(0.005)  # 0.5% return
                    else:
                        returns.append(-0.002)  # -0.2% return
                elif closing_hour_mask[i]:
                    # Aggressive trading in closing hour
                    price_change = (closes[i] - closes[i-1]) / closes[i-1]
                    returns.append(price_change * 2.0)  # 2x leverage
                else:
                    # Normal trading during regular hours
                    price_change = (closes[i] - closes[i-1]) / closes[i-1]
                    returns.append(price_change)
            else:
                # No trading outside market hours
                returns.append(0.0)
        
        return np.array(returns)
    
    def validate_params(self, **kwargs):
        return True
    
    @staticmethod
    def get_optimization_params():
        return {}

def comprehensive_demo():
    """Demonstrate all features of the numba-optimized datetime system."""
    
    print("=" * 60)
    print("NUMBA-OPTIMIZED DATETIME FEATURE DEMONSTRATION")
    print("=" * 60)
    
    # 1. Raw timestamp storage demonstration
    print("\n1. RAW TIMESTAMP STORAGE")
    print("-" * 30)
    
    # Create sample data with raw Unix timestamps
    sample_data = [
        [1704081300, 100.0, 101.0, 99.5, 100.5, 1000],  # 09:15 IST
        [1704082200, 100.5, 101.5, 100.0, 101.0, 1100], # 09:30 IST
        [1704096900, 101.0, 102.0, 100.5, 101.5, 1200], # 13:45 IST
        [1704101400, 101.5, 102.5, 101.0, 102.0, 1300], # 15:00 IST
        [1704103200, 102.0, 103.0, 101.5, 102.5, 1400]  # 15:30 IST
    ]
    
    print(f"Sample raw timestamps: {[row[0] for row in sample_data]}")
    
    # Convert to human-readable for demonstration
    IST = timezone(timedelta(seconds=IST_OFFSET_SECONDS))
    for i, row in enumerate(sample_data):
        dt = datetime.fromtimestamp(row[0], tz=IST)
        print(f"  {row[0]} → {dt.strftime('%Y-%m-%d %H:%M:%S IST')}")
    
    # 2. Data processing without string conversions
    print("\n2. STRING-FREE DATA PROCESSING")
    print("-" * 30)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = temp_dir + "/"
        symbol = "DEMO"
        
        # Process data (no string conversions)
        process_symbol_data(sample_data, temp_path, symbol)
        print("✓ Data processed and saved without string conversions")
        
        # Load data back
        data_tuple = read_from_csv(symbol, temp_path)
        symbol_loaded, timestamps, opens, highs, lows, closes, volume = data_tuple
        
        print(f"✓ Data loaded: {len(timestamps)} records")
        print(f"✓ Data types: timestamps={timestamps.dtype}, prices={closes.dtype}, volume={volume.dtype}")
        
        # 3. Numba-compiled utility functions
        print("\n3. NUMBA-COMPILED UTILITIES")
        print("-" * 30)
        
        # Individual functions
        sample_timestamp = timestamps[2]  # Afternoon timestamp
        print(f"Sample timestamp: {sample_timestamp}")
        print(f"  Hour: {extract_hour(sample_timestamp)}")
        print(f"  Minute: {extract_minute(sample_timestamp)}")
        print(f"  Second: {extract_second(sample_timestamp)}")
        print(f"  Day of week: {extract_day_of_week(sample_timestamp)} (0=Monday)")
        print(f"  Market hours: {is_market_hours(sample_timestamp)}")
        print(f"  Opening hour: {is_opening_hour(sample_timestamp)}")
        print(f"  Closing hour: {is_closing_hour(sample_timestamp)}")
        
        # 4. Vectorized operations
        print("\n4. VECTORIZED OPERATIONS")
        print("-" * 30)
        
        hours = extract_hour_vectorized(timestamps)
        market_mask = is_market_hours_vectorized(timestamps)
        opening_mask = is_opening_hour_vectorized(timestamps)
        closing_mask = is_closing_hour_vectorized(timestamps)
        
        print(f"All hours: {hours}")
        print(f"Market hours mask: {market_mask}")
        print(f"Opening hour mask: {opening_mask}")
        print(f"Closing hour mask: {closing_mask}")
        
        # 5. Strategy integration
        print("\n5. STRATEGY INTEGRATION")
        print("-" * 30)
        
        strategy = DemoStrategy()
        returns = strategy.run(data_tuple)
        results = strategy.process(data_tuple)
        
        returns, equity_curve, win_rate, no_of_trades = results
        
        print(f"Strategy executed successfully:")
        print(f"  Returns: {len(returns)} trades")
        print(f"  Win rate: {win_rate:.2%}")
        print(f"  Final equity: {equity_curve[-1]:.4f}")
        print(f"  Total return: {(equity_curve[-1] - 1) * 100:.2f}%")
        
        # 6. Numba compilation verification
        print("\n6. NUMBA COMPILATION")
        print("-" * 30)
        
        @numba.jit(nopython=True)
        def numba_demo_function(timestamps, closes):
            """Demo function compiled with numba."""
            total_market_return = 0.0
            market_periods = 0
            
            for i in range(len(timestamps)):
                if is_market_hours(timestamps[i]):
                    if i > 0:
                        ret = (closes[i] - closes[i-1]) / closes[i-1]
                        total_market_return += ret
                        market_periods += 1
            
            return total_market_return / market_periods if market_periods > 0 else 0.0
        
        avg_return = numba_demo_function(timestamps, closes)
        print(f"✓ Numba compilation successful")
        print(f"✓ Average market hours return: {avg_return:.4f} ({avg_return*100:.2f}%)")
        
        # 7. Performance comparison demonstration
        print("\n7. PERFORMANCE BENEFITS")
        print("-" * 30)
        
        print("✓ Raw integer timestamps (8 bytes each)")
        print("✓ No string parsing overhead")
        print("✓ Numba-compiled time extraction")
        print("✓ Vectorized operations for bulk processing")
        print("✓ Single timestamp column vs separate date/time")
        
        memory_old = len(timestamps) * 16  # 2 arrays * 8 bytes (rough estimate)
        memory_new = len(timestamps) * 8   # 1 array * 8 bytes
        memory_savings = ((memory_old - memory_new) / memory_old) * 100
        
        print(f"✓ Estimated memory savings: {memory_savings:.1f}%")
        
        # 8. Data format demonstration
        print("\n8. CSV FORMAT")
        print("-" * 30)
        
        # Show CSV content
        csv_file = f"{temp_path}{symbol}.csv"
        with open(csv_file, 'r') as f:
            lines = f.readlines()
        
        print("CSV Header:", lines[0].strip())
        print("Sample rows:")
        for i, line in enumerate(lines[1:4]):  # Show first 3 data rows
            print(f"  Row {i+1}: {line.strip()}")
        
    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)
    print("\nKey achievements:")
    print("✓ Eliminated string datetime conversions")
    print("✓ Raw Unix timestamp storage")
    print("✓ Numba-compiled utility functions")
    print("✓ Vectorized array operations")
    print("✓ Strategy integration with time-based logic")
    print("✓ Memory and performance optimizations")
    print("✓ Maintained data integrity and accuracy")

if __name__ == "__main__":
    comprehensive_demo()
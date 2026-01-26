"""
Utilities module for the strategy testing and optimization.

This module provides utility functions for downloading historical data, reading CSV files, and reading JSON files.
"""

import os
import random
import csv
import json
from typing import Dict, Optional, Tuple
import pytz
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from tvDatafeed import TvDatafeed, Interval
import numpy as np
import config
from typing import TypeAlias
from numpy.typing import NDArray
from types import ModuleType
from importlib import import_module


DataTuple: TypeAlias = Tuple[str, NDArray, NDArray, NDArray, NDArray, NDArray, NDArray]

INTERVAL_MAP = {
    "1": Interval.in_1_minute,
    "3": Interval.in_3_minute,
    "5": Interval.in_5_minute,
    "15": Interval.in_15_minute,
    "30": Interval.in_30_minute,
    "45": Interval.in_45_minute,
    "1H": Interval.in_1_hour,
    "2H": Interval.in_2_hour,
    "3H": Interval.in_3_hour,
    "4H": Interval.in_4_hour,
    "1D": Interval.in_daily,
    "1W": Interval.in_weekly,
    "1M": Interval.in_monthly
}

def get_interval(interval_str: str) -> Interval:
    return INTERVAL_MAP.get(interval_str, Interval.in_5_minute)


def get_strategy(strategy: str) -> ModuleType:
    """
    Import the strategy module from the strategies folder.
    
    Args:
        strategy (str): name of the strategy
    
    Returns:
        module: strategy module
    """
    try:
        return import_module(f'strategies.{strategy}')
    except ImportError as e:
        raise ValueError(f"Error importing the strategy '{strategy}': {e}")
    except Exception as e:
        raise e


def slippage(number: float) -> float:
    """Add random slippage to a number, simulating real-world market slippage. Slippage is a random number between -0.05 and 0.05."""
    return number + random.uniform(-0.05, 0.05)

def read_from_csv(symbol: str, path: str) -> DataTuple:
    """Read CSV into NumPy arrays with new timestamp format."""
    data = np.genfromtxt(f'{path+symbol}.csv', delimiter=',', dtype=None, names=True, encoding='utf-8')
    
    # Read timestamps as int64 (raw Unix timestamps)
    timestamps = data['timestamp'].astype(np.int64)
    
    # Read price and volume data as numba-compatible types
    opens = data['Open'].astype(np.float64)
    highs = data['High'].astype(np.float64)
    lows = data['Low'].astype(np.float64)
    closes = data['Close'].astype(np.float64)
    volume = data['Volume'].astype(np.int64)
    
    # Return updated 7-element DataTuple structure
    return symbol, timestamps, opens, highs, lows, closes, volume

def read_column_from_csv(filename: str, column_name: str) -> list[str]:
    """Read a specific column from a CSV file."""
    with open(filename, 'r') as file:
        reader = csv.DictReader(file)
        return [row[column_name].replace('-', '_') for row in reader]
    
def read_json(file_path: str) -> Optional[Dict]:
    """Read JSON data synchronously from a file."""
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as error:
        return None
    
def hist_download(symbols: list[str], interval: Interval = Interval.in_5_minute, exchange=config.EXCHANGE, TZ=config.TZ, path: str | None = None, separate_time_column: bool = True) -> None:
    """Download historical data for a list of symbols.
    
    Args:
        symbols (list[str]): List of symbols to download data for.
        interval (Interval, optional): Interval for which to download data. Defaults to Interval.in_5_minute.
        exchange (str, optional): Exchange for which to download data. Defaults to config.EXCHANGE.
        TZ (str, optional): Timezone for which to download data. Defaults to config.TZ.
        path (str, optional): Path to save the downloaded data. Defaults to None.
        separate_time_column (bool, optional): Whether to separate time column. Defaults to True.
    """
    if path is None:
        path = f"./data/{interval.value}/"
        os.makedirs(path, exist_ok=True)
    
    # Interval values
    # in_1_minute = "1"
    # in_3_minute = "3"
    # in_5_minute = "5"
    # in_15_minute = "15"
    # in_30_minute = "30"
    # in_45_minute = "45"
    # in_1_hour = "1H"
    # in_2_hour = "2H"
    # in_3_hour = "3H"
    # in_4_hour = "4H"
    # in_daily = "1D"
    # in_weekly = "1W"
    # in_monthly = "1M"

    tz = pytz.timezone(TZ)

    tv = TvDatafeed()

    symbol_retry_count: Dict[str, int] = {}
    MAX_RETRIES = 3

    t_pool = ThreadPoolExecutor(max_workers=5)

    try:
        for i in range(0, len(symbols), 5):
            temp_symbols = symbols[i: i+5] # Try to download 5 symbols at a time
            
            while temp_symbols:
                # get_hist returns a dictionary of history data for each symbol in the format {symbol: [[timestamp, open, high, low, close, volume], ...]}
                data = tv.get_hist(symbols=temp_symbols,exchange=exchange,interval=interval,n_bars=10_000, dataFrame=False)

                for symbol, d in data.items():
                    if d is None:
                        symbol_retry_count[symbol] = symbol_retry_count.get(symbol, 0) + 1
                        if symbol_retry_count[symbol] >= MAX_RETRIES:
                            print(f"Data retrieval failed for {symbol}. Skipping...") # Skip the symbol if it fails 3 times
                            temp_symbols.remove(symbol)
                            continue
                        print(f"Data retrieval failed for {symbol}. Retrying...") # Retry the symbol if it fails less than 3 times
                        continue
                    temp_symbols.remove(symbol)

                    t_pool.submit(process_symbol_data, d, path, symbol, separate_time_column, tz)
                    
                # print(len(temp_symbols))
    except Exception as e:
        print(f"Error downloading data: {e}")
    finally:
        t_pool.shutdown()

def process_symbol_data(data: list[list], path: str, symbol: str, separate_time_column: bool = False, tz: pytz.BaseTzInfo = pytz.timezone(config.TZ)) -> None:
    """Process symbol data with raw Unix timestamp storage.
    
    Args:
        data (list[list]): List of lists containing symbol data.
        path (str): Path to save the processed data.
        symbol (str): Symbol to process.
        separate_time_column (bool, optional): Deprecated parameter, kept for compatibility. Defaults to False.
        tz (pytz.BaseTzInfo, optional): Timezone for which to process data. Only used during download, not storage. Defaults to pytz.timezone(config.TZ).
    """
    try:
        # Store raw Unix timestamps without any string conversions
        # data[i][0] already contains the Unix timestamp as integer
        # No datetime string formatting or timezone conversion during storage
        
        with open(f"{path+symbol}.csv", 'w', newline='') as file:
            writer = csv.writer(file)
            # New CSV header format with single timestamp column
            writer.writerow(['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
            writer.writerows(data)  # Write all rows at once with raw timestamps
    except Exception as e:
        print(f"Error processing symbol {symbol}: {e}")

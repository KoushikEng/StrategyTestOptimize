"""
Main module for the strategy testing and optimization.

This module provides the main entry point for the strategy testing and optimization.
"""

from typing import Type
from Utilities import hist_download, read_from_csv, get_strategy
from multiprocessing import Pool, cpu_count
from multiprocessing.pool import ThreadPool
from prettytable import PrettyTable
import math
import argparse
import numpy as np
from calculate.risk_metrics import calculate_sharpe, calculate_sortino, calculate_max_drawdown
from strategies.Base import Base
from functools import partial

def convert_to_double_value_pair(data):
    result = []
    for i in range(0, len_half:=math.ceil(len(data)/2)):
        if i + 1 < len(data):
            result.append(data[i] + ['|'] + data[len_half + i])
        else:
            result.append(data[i] + ['|'])
            
    return result

def process_result(symbol, retval):
    returns, equity_curve, win_rate, no_of_trades = retval
    
    net_profit = (equity_curve[-1] - 1) * 100 if len(equity_curve) > 0 else 0.0
    sharpe = calculate_sharpe(returns)
    sortino = calculate_sortino(returns)
    max_dd = calculate_max_drawdown(returns) * 100
    
    return [symbol, net_profit, win_rate * 100, sharpe, sortino, max_dd, no_of_trades]

def run_backtest(symbols: list, strategy_name: str, interval: str = '5', download: bool = False, multiprocess: bool = False, **kwargs) -> list:
    """
    Run backtest on a list of symbols.
    
    Args:
        symbols (list): List of symbols to backtest.
        strategy_name (str): Name of the strategy class.
        interval (str, optional): Data interval. Defaults to '5'.
        download (bool, optional): Whether to download data. Defaults to False.
        multiprocess (bool, optional): Whether to use multiprocessing. Defaults to False.
        **kwargs: Strategy parameters.
        
    Returns:
        list: List of result rows [Symbol, Net Profit %, Win Rate %, Sharpe, Sortino, Max DD %, Trades]
    """
    
    # Resolve Interval
    from Utilities import get_interval
    interval_enum = get_interval(interval)
    data_path = f"./data/{interval_enum.value}/"

    if download:
        hist_download(symbols, interval=interval_enum)
        
    try:
        strategy_module = get_strategy(strategy_name)
        StrategyClass: Type[Base] = getattr(strategy_module, strategy_name)
        strategy_instance = StrategyClass()
    except (ValueError, AttributeError) as e:
        print(f"Error loading strategy '{strategy_name}': {e}")
        return []

    # Read data
    print(f"Loading data for {len(symbols)} symbols from {data_path}...")
    argss = [(s, data_path) for s in symbols]
    
    if multiprocess:
        # Use ThreadPool for IO bound reading
        with ThreadPool(processes=min(5, len(symbols))) as pool:
            data_list = pool.starmap(read_from_csv, argss)
    else:
        # Sequential execution to avoid Windows multiprocessing issues with local functions/pickling
        data_list = [read_from_csv(*args) for args in argss]
    
    print(f"Running {strategy_name} on {len(symbols)} symbols...")
    
    execution_results = []
    
    run_with_kwargs = partial(strategy_instance.process, **kwargs)
    
    if multiprocess:
        # Use Process Pool for CPU bound strategy execution
        with Pool(processes=min(cpu_count(), len(symbols))) as pool:
            execution_results = pool.map(run_with_kwargs, data_list)
    else:
        for data in data_list:
            try:
                res = run_with_kwargs(data)
                execution_results.append(res)
            except Exception as e:
                print(f"Error running strategy on {data[0]}: {e}")
                execution_results.append((np.array([1.0]), np.array([0.0]), 0.0))
        
    final_results = []
    for i, (symbol, *_) in enumerate(data_list):
        row = process_result(symbol, execution_results[i])
        final_results.append(row)
        
    return final_results

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run the strategy")
    parser.add_argument('symbols', nargs='?', type=str, help='Symbols to run')
    parser.add_argument('--download', action='store_true')
    parser.add_argument('--strategy', '-S', type=str, help='Strategy to run')
    parser.add_argument('--interval', '-I', type=str, default='5', help='Interval (1, 5, 15, 1H, 1D, etc.)')
    parser.add_argument('--multiprocess', action='store_true', help='Use multiprocessing')
    parser.add_argument('--kwargs', type=str, default='', help='Additional kwargs for strategy')

    args = parser.parse_args()

    if args.symbols:
        symbols = [s.upper() for s in args.symbols.split(',')]
    elif args.download:
        pass # If download only, symbols might be empty or come from default list
    else:
        # Default symbols if none provided
        symbols = ["SBIN", "RELIANCE", "INFY", "TCS", "HDFCBANK", "ICICIBANK", "AXISBANK", "KOTAKBANK", "LT", "ITC"]

    if args.download and not args.strategy:
        # Just download
        from Utilities import get_interval
        hist_download(symbols, interval=get_interval(args.interval))
        exit()

    if not args.strategy:
        print("Please provide a strategy name using --strategy or -S")
        exit()

    # Parse kwargs
    kwargs = {}
    if args.kwargs:
        for arg in args.kwargs.split(','):
            if '=' in arg:
                key, value = arg.split('=', 1)
                
                if ':' in key:
                    key, dtype = key.split(':', 1)
                else:
                    dtype = 'str'
                
                if dtype == 'int':
                    kwargs[key] = int(value)
                elif dtype == 'float':
                    kwargs[key] = float(value)
                else:
                    kwargs[key] = value
            else:
                print(f"Invalid argument format: {arg}. Please use key:datatype=value")

    results = run_backtest(symbols, args.strategy, args.interval, args.download, args.multiprocess, **kwargs)
    
    # Display results
    results_table = PrettyTable()
    results_table.field_names = ["Symbol", "Net Profit %", "Win Rate %", "Sharpe", "Sortino", "Max DD %", "Trades"]
    results_table.float_format = ".2"
    
    for row in results:
        results_table.add_row(row)
        
    print(results_table)
    
    if results:
        profits = [r[1] for r in results]
        print(f"\nAverage Profit: {np.mean(profits):.2f}%")
        print(f"Total Profit: {np.sum(profits):.2f}%")

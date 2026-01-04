"""
Main module for the strategy testing and optimization.

This module provides the main entry point for the strategy testing and optimization.
"""

from typing import List
from Utilities import read_json, hist_download, read_from_csv, get_strategy
from multiprocessing import Pool
from multiprocessing.pool import ThreadPool
from prettytable import PrettyTable
import math
import argparse
import numpy as np
from indicators.risk_metrics import calculate_sharpe, calculate_sortino, calculate_max_drawdown


def convert_to_double_value_pair(data):
    result = []
    for i in range(0, len_half:=math.ceil(len(data)/2)):
        if i + 1 < len(data):
            result.append(data[i] + ['|'] + data[len_half + i])
        else:
            result.append(data[i] + ['|'])
            
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('symbols', nargs='?', type=str, help='Symbols to run')
    parser.add_argument('--download', action='store_true')
    parser.add_argument('--strategy', '-S', type=str, help='Strategy to run')

    args = parser.parse_args()

    if args.symbols:
        symbols = [s.upper() for s in args.symbols.split(',')]
    elif args.download:
        pass # If download only, symbols might be empty or come from default list
    else:
        # Default symbols if none provided
        symbols = ["SBIN", "RELIANCE", "INFY", "TCS", "HDFCBANK", "ICICIBANK", "AXISBANK", "KOTAKBANK", "LT", "ITC"]

    if args.download:
        hist_download(symbols)
        if not args.strategy:
             exit()

    if not args.strategy:
        print("Please provide a strategy name using --strategy or -S")
        exit()

    try:
        strategy_module = get_strategy(args.strategy)
        # Assuming the class name is the same as the module name + matching file name
        # Only if the user follows convention: strategies/MyStrat.py -> class MyStrat
        StrategyClass = getattr(strategy_module, args.strategy)
        strategy_instance = StrategyClass()
    except (ValueError, AttributeError) as e:
        print(f"Error loading strategy '{args.strategy}': {e}")
        exit()

    # Read data first
    print(f"Loading data for {len(symbols)} symbols...")
    # Sequential execution to avoid Windows multiprocessing issues with local functions/pickling
    argss = [(s, f"./data/5/") for s in symbols]
    data_list = [read_from_csv(*args) for args in argss]
    
    print(f"Running {args.strategy} on {len(symbols)} symbols...")
    
    results_table = PrettyTable()
    results_table.field_names = ["Symbol", "Net Profit %", "Win Rate %", "Sharpe", "Sortino", "Max DD %", "Trades"]
    results_table.float_format = ".2"
    
    def process_result(symbol, retval):
        equity_curve, returns, win_rate = retval
        
        net_profit = (equity_curve[-1] - 1) * 100 if len(equity_curve) > 0 else 0.0
        sharpe = calculate_sharpe(returns)
        sortino = calculate_sortino(returns)
        max_dd = calculate_max_drawdown(returns) * 100
        total_trades = np.sum(returns != 0)
        
        return [symbol, net_profit, win_rate * 100, sharpe, sortino, max_dd, total_trades]

    final_results = []
    
    execution_results = []
    for data in data_list:
        try:
            res = strategy_instance.run(data)
            execution_results.append(res)
        except Exception as e:
            print(f"Error running strategy on {data[0]}: {e}")
            execution_results.append((np.array([1.0]), np.array([0.0]), 0.0))
        
    for i, (symbol, *_) in enumerate(data_list):
        row = process_result(symbol, execution_results[i])
        results_table.add_row(row)
        final_results.append(row)

    print(results_table)
    
    # Summary stats
    profits = [r[1] for r in final_results]
    print(f"\nAverage Profit: {np.mean(profits):.2f}%")
    print(f"Total Profit: {np.sum(profits):.2f}%")
        
    

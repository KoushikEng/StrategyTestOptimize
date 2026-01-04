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
from indicators.risk_metrics import calculate_sharpe, calculate_sortino


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

    symbols = args.symbol.split(',')
    
    # symbols = read_json('stocks_list.json')['nifty100']
    # symbols = ["HAL", "BDL", "NAUKRI", "JSWENERGY", "HUDCO", "CGPOWER", "BANKINDIA", "CONCOR", "CHOLAFIN", "TORNTPHARM", "PFC", "TRENT", "RECLTD", "BAJAJ_AUTO"]
    
    if args.symbols:
        symbols = [args.symbols.upper()]
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
    with ThreadPool() as pool:
        # pool.map expects a single argument function, using lambda to pass path
        # Assuming Data is in ./data/5/ as per default hist_download
        argss = [(s, f"./data/5/") for s in symbols]
        # We need a wrapper because read_from_csv takes 2 args
        data_list = pool.starmap(read_from_csv, argss)
    
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

    # Run strategies
    # Since strategy_instance.run might need kwargs, for now we run with defaults or empty
    # If optimization params are needed, they should be passed; for main.py we might use defaults
    
    final_results = []
    
    # Sequential execution for now to debug - switch to Pool if slow
    # Using Pool for strategy execution
    with Pool() as pool:
        # prepare args: each run takes (data, )
        # strategy_instance.run is bound method
        # We need to unpack data_list into arguments for starmap if run takes multiple args, 
        # but run takes (data, **kwargs). 
        # So we wrap it.
        
        # Wrapper to allow pickling if necessary, or just use starmap with instance method
        # map: func(item). item is data_tuple. run(data).
        
        # Note: We need to handle exceptions in strategy run
        
        def run_wrapper(data):
            try:
                return strategy_instance.run(data)
            except Exception as e:
                return (np.array([1.0]), np.array([0.0]), 0.0) # Error return

        execution_results = pool.map(run_wrapper, data_list)
        
    for i, (symbol, *_) in enumerate(data_list):
        row = process_result(symbol, execution_results[i])
        results_table.add_row(row)
        final_results.append(row)

    print(results_table)
    
    # Summary stats
    profits = [r[1] for r in final_results]
    print(f"\nAverage Profit: {np.mean(profits):.2f}%")
    print(f"Total Profit: {np.sum(profits):.2f}%")
        
    

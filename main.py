from First15minBreak import run
from First15minBreakOpps import run as oppRun
from Utilities import read_json, hist_download, read_from_csv, read_column_from_csv
from multiprocessing import Pool
from multiprocessing.pool import ThreadPool
from prettytable import PrettyTable
import math
import argparse
from functools import partial
from ConsoleAnimator import ConsoleAnimator
import numpy as np
from numba import njit

@njit
def calculate_sharpe(returns, risk_free_rate: float = 0.07) -> float:
    excess_returns = returns - risk_free_rate
    if len(excess_returns) < 2 and np.std(excess_returns) == 0:
        return 0.0
    return round(np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252), 4)

@njit
def calculate_sortino(returns, risk_free_rate: float = 0.07) -> float:
    excess_returns = returns - risk_free_rate
    downside_returns = excess_returns[excess_returns < 0]
    if len(downside_returns) == 0 or np.std(downside_returns) == 0:
        return 0.0
    return round(np.mean(excess_returns) / np.std(downside_returns) * np.sqrt(252), 4)

def convert_to_double_value_pair(data):
    result = []
    for i in range(0, len_half:=math.ceil(len(data)/2)):
        if i + 1 < len(data):
            result.append(data[i] + ['|'] + data[len_half + i])
        else:
            result.append(data[i] + ['|'])
            
    return result

if __name__ == '__main__':
    anim = ConsoleAnimator()
    parser = argparse.ArgumentParser()
    parser.add_argument('symbol', nargs='?', type=str)
    parser.add_argument('--download', action='store_true')
    parser.add_argument('kwargs', nargs='*', help="Keyword arguments in the format key=value")
    args = parser.parse_args()
    
    # print(read_column_from_csv('ind_nifty100list.csv', 'Symbol'))
    # exit()
    # symbols = read_json('stocks_list.json')['nifty100']
    symbols = ["HAL", "BDL", "NAUKRI", "JSWENERGY", "HUDCO", "CGPOWER", "BANKINDIA", "CONCOR", "CHOLAFIN", "TORNTPHARM", "PFC", "TRENT", "RECLTD", "BAJAJ_AUTO"]
    
    if args.symbol:
        symbols = [args.symbol.upper()]
    
    if args.download:
        anim.start("Downloading historical data...")
        hist_download(symbols)
        anim.done("Historical data downloaded")
        
    kwargs_dict = {}
    for arg in args.kwargs:
        if '=' in arg:
            key, value = arg.split('=', 1)
            if value == 'T' or value == 'F':
                kwargs_dict[key] = True if value == 'T' else False
                continue
            kwargs_dict[key] = value
        else:
            print(f"Invalid argument format: {arg}. Please use key=value")
    
    # symbols.remove("YESBANK")
    # symbols.remove("IDEA")
    
    anim.start("Reading CSV files...")
    with ThreadPool() as pool:
        argss = pool.map(read_from_csv, symbols)
    
    anim.done("CSV files read")
    
    run_with_kwargs = partial(run, **kwargs_dict)
    
    anim.start("Running backtests...")
    with Pool() as pool:
        # Just pass args, since kwargs are already bound
        results = pool.starmap(run_with_kwargs, argss)
    anim.done("Backtesting complete")
    
    results = [[r[0], round(np.sum(r[1]), 2), r[2], calculate_sharpe(r[1]), calculate_sortino(r[1])] for r in results]

    len_results = len(results)
    if len_results == 1:
        print(f"{results[0][0]} Net P/L: {results[0][1]}, wins: {results[0][2]}, sharpe: {results[0][3]}, sortino: {results[0][4]}")
        exit()

    weights = [1, 2]
    sorted_results = sorted(results, key=lambda x: weights[0] * -x[2] + weights[1] * -x[3])[:50]
    
    table_headers = ['Symbol', 'Net P/L', 'Win pct (%)', 'Sharpe', 'sortino']

    if len_results <= 20:
        table = PrettyTable(table_headers)
        table.add_rows(sorted_results)
    else:
        table = PrettyTable(table_headers + ['|'] + [col + ' c2' for col in table_headers])
        table.add_rows(convert_to_double_value_pair(sorted_results))

    print(table)

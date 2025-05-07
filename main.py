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



def convert_to_double_value_pair(data):
    result = []
    for i in range(0, len_half:=math.ceil(len(data)/2)):
        if i + 1 < len(data):
            result.append(data[i] + ('|',) + data[len_half + i])
        else:
            result.append(data[i] + ('|',))
            
    return result

if __name__ == '__main__':
    anim = ConsoleAnimator()
    parser = argparse.ArgumentParser()
    parser.add_argument('symbol', nargs='?', type=str)
    parser.add_argument('--download', action='store_true')
    parser.add_argument('kwargs', nargs=argparse.REMAINDER, help="Keyword arguments in the format key=value")
    args = parser.parse_args()
    
    # print(read_column_from_csv('ind_nifty100list.csv', 'Symbol'))
    # exit()
    # symbols = read_json('stocks_list.json')['nifty100']
    symbols = ["HAL", "BDL", "NAUKRI", "JSWENERGY", "HUDCO", "CGPOWER", "BANKINDIA", "CONCOR", "CHOLAFIN", "TORNTPHARM", "PFC"]
    
    if args.symbol:
        symbols = [args.symbol.upper()]
    
    if args.download:
        anim.start("Downloading historical data...")
        hist_download(symbols)
        anim.done("Historical data downloaded")
        
    kwargs_dict = {}
    for item in args.kwargs:
        try:
            key, value = item.split("=", 1)
            if value == 'T' or value == 'F':
                kwargs_dict[key] = True if value == 'T' else False
                continue
            
            kwargs_dict[key] = value
        except ValueError:
            print(f"Invalid argument format: {item}. Please use key=value.")
            exit()
    
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
    
    results = [[r[0], np.round(np.sum(r[1]), 2), r[2]] for r in results]

    len_results = len(results)
    if len_results == 1:
        print(f"{results[0][0]} Net P/L: {results[0][1]}, wins: {results[0][2]}")
        exit()

    weights = [1, 400]
    sorted_results = sorted(results, key=lambda x: weights[0] * -x[1] + weights[1] * -x[2])
    
    table_headers = ['Symbol', 'Net P/L', 'Win pct (%)']

    if len_results <= 20:
        table = PrettyTable(table_headers)
        table.add_rows(sorted_results)
    else:
        table = PrettyTable(table_headers + ['|'] + [col + ' c2' for col in table_headers])
        table.add_rows(convert_to_double_value_pair(sorted_results))

    print(table)

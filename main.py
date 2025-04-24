from First15minBreak import read_from_csv, run
from First15minBreakOpps import run as oppRun
from Utilities import read_json, hist_download, read_column_from_csv
from multiprocessing import Pool
from prettytable import PrettyTable
import math



def convert_to_double_value_pair(data):
    result = []
    for i in range(0, len_half:=math.ceil(len(data)/2)):
        if i + 1 < len(data):
            result.append(data[i] + ('|',) + data[len_half + i])
        else:
            result.append(data[i] + ('|',))
            
    return result

if __name__ == '__main__':
    # print(read_column_from_csv('nifty200list.csv', 'Symbol'))
    # symbols = read_json('stocks_list.json')['nifty200']
    symbols = ["HAL", "BDL", "NAUKRI", "JSWENERGY", "HUDCO", "CGPOWER", "BANKINDIA", "CONCOR", "CHOLAFIN", "TORNTPHARM"]
    # hist_download(symbols)
    # symbols.remove("YESBANK")
    # symbols.remove("IDEA")
    print("Reading csvs")
    with Pool() as pool:
        argss = pool.map(read_from_csv, symbols)

    print("testing")
    # print(symbols, argss)
    with Pool() as pool:
        results = pool.starmap(run, argss)

    # print(results)

    table = PrettyTable(['Symbol', 'Net P/L', 'Win pct (%)', '|', 'Symbol (col2)', 'Net P/L (col2)', 'Win pct (%) (col2)'])

    weights = [1, 400]  # Weights for the 2nd and 3rd items in the child lists

    # Sort based on the weighted sum of the 2nd and 3rd items
    sorted_lists = sorted(results, key=lambda x: weights[0] * -x[1] + weights[1] * -x[2])
    table.add_rows(convert_to_double_value_pair(sorted_lists))

    print(table)

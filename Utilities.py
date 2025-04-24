import random
import csv
import json
from typing import List, Optional
import pytz
from datetime import datetime
from tvDatafeed import TvDatafeed, Interval

def slippage(number):
    return number + random.uniform(-0.05, 0.05)

def read_column_from_csv(filename, column_name):
    with open(filename, 'r') as file:
        reader = csv.DictReader(file)
        return [row[column_name].replace('-', '_') for row in reader]
    
def read_json(file_path: str) -> Optional[dict]:
    """Read JSON data synchronously from a file."""
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as error:
        return None
    
def hist_download(symbols, exchange="NSE", TZ="Asia/Kolkata", path="hist\\5min\\"):
    temp_symbols = list(symbols)
    tz = pytz.timezone(TZ)

    tv = TvDatafeed()

    while temp_symbols:
        dfs = tv.get_hist(symbols=temp_symbols,exchange=exchange,interval=Interval.in_5_minute,n_bars=10000, dataFrame=False)

        for symbol, df in dfs.items():
            if df is None:
                print(f"Data retrieval failed for {symbol}. Skipping...")
                continue  # Move to the next symbol
            temp_symbols.remove(symbol)

            for i in range(len(df)):
                dt = datetime.fromtimestamp(df[i][0], tz=tz)
                date = dt.date().strftime('%Y-%m-%d')
                time = dt.time().strftime('%H:%M:%S')
                df[i][0] = date
                df[i].insert(1, time)
            
            with open(f"{path+symbol}_5min.csv", 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['date', 'time', 'Open', 'High', 'Low', 'Close', 'Volume'])  # Write header
                writer.writerows(df)  # Write all rows at once
                continue

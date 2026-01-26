# Project Usage Guide

## Overview

This guide covers how to run backtests, optimize strategies, and use the StrategyTestOptimize project through both CLI and programmatic interfaces.

## Project Structure

```
StrategyTestOptimize/
├── main.py                 # CLI interface and backtesting engine
├── Utilities.py            # Data utilities with raw timestamp support
├── datetime_utils.py       # Numba-optimized time functions
├── config.py              # Configuration settings
├── strategies/            # Strategy implementations
│   ├── Base/              # Enhanced strategy framework
│   └── SimpleMACross.py   # Example strategy
├── indicators/            # Technical indicator functions
├── data/                  # Historical data storage
└── tests/                 # Test files
```

## Data Management

### Downloading Historical Data

```bash
# Download data for specific symbols
python main.py SBIN,RELIANCE,INFY --download --interval 5

# Download with different intervals
python main.py SBIN --download --interval 1H
python main.py SBIN --download --interval 1D
```

**Data Format:**
- Raw Unix timestamps (int64) for numba optimization
- CSV format: `timestamp,Open,High,Low,Close,Volume`
- Stored in `./data/{interval}/` directories

### Data Loading

```python
from Utilities import read_from_csv

# Load data (returns DataTuple with raw timestamps)
data = read_from_csv("SBIN", "./data/5/")
symbol, timestamps, opens, highs, lows, closes, volume = data

# timestamps are raw Unix integers, not datetime objects
print(f"First timestamp: {timestamps[0]}")  # e.g., 1704081300
```

## Running Backtests

### CLI Interface

```bash
# Basic backtest
python main.py SBIN --strategy SimpleMACross --interval 5

# Multiple symbols
python main.py SBIN,RELIANCE,INFY --strategy SimpleMACross

# With parameters
python main.py SBIN --strategy SimpleMACross --kwargs "fast_period:int=10,slow_period:int=20"

# Different intervals
python main.py SBIN --strategy SimpleMACross --interval 1H
```

### Programmatic Interface

```python
from main import run_backtest
from Utilities import read_from_csv
from strategies.SimpleMACross import SimpleMACross

# Load data
data = read_from_csv("SBIN", "./data/5/")

# Create strategy instance
strategy = SimpleMACross()

# Run backtest
results = strategy.process(data, fast_period=10, slow_period=20)
returns, equity_curve, win_rate, total_trades = results

print(f"Total trades: {total_trades}")
print(f"Win rate: {win_rate:.2%}")
print(f"Final return: {(equity_curve[-1] - 1) * 100:.2f}%")
```

## Strategy Development

### Creating a New Strategy

```python
from strategies.Base import Base
from indicators.vectorized import SMA
from datetime_utils import is_market_hours

class MyStrategy(Base):
    def init(self):
        # Get parameters with defaults
        fast_period = getattr(self, 'fast_period', 10)
        slow_period = getattr(self, 'slow_period', 20)
        
        # Register indicators (calculated once)
        self.sma_fast = self.I(SMA, self.data.Close, fast_period)
        self.sma_slow = self.I(SMA, self.data.Close, slow_period)
    
    def next(self):
        # Time-based filtering using raw timestamps
        current_timestamp = self.data.timestamps[-1]
        
        if is_market_hours(current_timestamp):
            # Golden cross
            if (self.sma_fast[-1] > self.sma_slow[-1] and 
                self.sma_fast[-2] <= self.sma_slow[-2]):
                if not self.position['is_in_position']:
                    self.buy()
            
            # Death cross
            elif (self.sma_fast[-1] < self.sma_slow[-1] and 
                  self.sma_fast[-2] >= self.sma_slow[-2]):
                if self.position['is_in_position']:
                    self.sell()
    
    def validate_params(self, **kwargs):
        fast = kwargs.get('fast_period', 10)
        slow = kwargs.get('slow_period', 20)
        return fast < slow and fast > 0
    
    @staticmethod
    def get_optimization_params():
        return {
            'fast_period': (5, 20),
            'slow_period': (20, 50)
        }
```

### Time-based Logic

```python
from datetime_utils import extract_hour, is_opening_hour, is_closing_hour

def next(self):
    timestamp = self.data.timestamps[-1]
    
    # Extract time components (numba-optimized)
    hour = extract_hour(timestamp)
    
    # Use time-based conditions
    if is_opening_hour(timestamp):
        # Opening hour strategy
        pass
    elif is_closing_hour(timestamp):
        # Closing hour strategy
        pass
    elif hour >= 11 and hour <= 14:
        # Mid-day strategy
        pass
```

## Parameter Optimization

### CLI Optimization

```bash
# Basic optimization (uses get_optimization_params())
python optimize.py SBIN --strategy MyStrategy --interval 5

# Custom parameter ranges
python optimize.py SBIN --strategy MyStrategy --params "fast_period:5:20,slow_period:20:50"
```

### Programmatic Optimization

```python
from multiprocessing import Pool
from itertools import product
import numpy as np

def optimize_strategy(symbol, strategy_class, param_ranges):
    """Optimize strategy parameters."""
    data = read_from_csv(symbol, "./data/5/")
    
    # Generate parameter combinations
    param_names = list(param_ranges.keys())
    param_values = [range(min_val, max_val + 1) for min_val, max_val in param_ranges.values()]
    param_combinations = list(product(*param_values))
    
    best_return = -np.inf
    best_params = None
    
    for params in param_combinations:
        param_dict = dict(zip(param_names, params))
        
        # Create strategy instance with parameters
        strategy = strategy_class()
        for key, value in param_dict.items():
            setattr(strategy, key, value)
        
        # Run backtest
        try:
            results = strategy.process(data)
            returns, equity_curve, win_rate, total_trades = results
            
            if len(equity_curve) > 0:
                final_return = equity_curve[-1] - 1
                if final_return > best_return:
                    best_return = final_return
                    best_params = param_dict
        except Exception as e:
            continue  # Skip invalid parameter combinations
    
    return best_params, best_return

# Usage
from strategies.MyStrategy import MyStrategy

best_params, best_return = optimize_strategy(
    "SBIN", 
    MyStrategy, 
    {'fast_period': (5, 20), 'slow_period': (20, 50)}
)

print(f"Best parameters: {best_params}")
print(f"Best return: {best_return:.2%}")
```

## Performance Analysis

### Basic Metrics

```python
def analyze_performance(returns, equity_curve):
    """Calculate performance metrics."""
    if len(returns) == 0:
        return {}
    
    total_return = equity_curve[-1] - 1
    win_rate = np.sum(returns > 0) / len(returns)
    avg_return = np.mean(returns)
    max_drawdown = np.max(np.maximum.accumulate(equity_curve) - equity_curve)
    
    # Sharpe ratio (assuming daily returns)
    sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
    
    return {
        'total_return': total_return,
        'win_rate': win_rate,
        'avg_return': avg_return,
        'max_drawdown': max_drawdown,
        'sharpe_ratio': sharpe,
        'total_trades': len(returns)
    }

# Usage
results = strategy.process(data)
returns, equity_curve, win_rate, total_trades = results
metrics = analyze_performance(returns, equity_curve)

for key, value in metrics.items():
    print(f"{key}: {value:.4f}")
```

### Risk Metrics

```python
from indicators.risk_metrics import calculate_sharpe, calculate_sortino, calculate_max_drawdown

# Use built-in risk metrics
sharpe = calculate_sharpe(returns)
sortino = calculate_sortino(returns)
max_dd = calculate_max_drawdown(returns)

print(f"Sharpe: {sharpe:.2f}")
print(f"Sortino: {sortino:.2f}")
print(f"Max Drawdown: {max_dd:.2%}")
```

## Configuration

### config.py Settings

```python
# Exchange and timezone settings
EXCHANGE = "NSE"
TZ = "Asia/Kolkata"

# Data download settings
DEFAULT_INTERVAL = "5"
MAX_BARS = 10000

# Optimization settings
OPTIMIZATION_WORKERS = 4
```

### Environment Variables

```bash
# Set custom data path
export DATA_PATH="./custom_data/"

# Set custom timezone
export TIMEZONE="Asia/Kolkata"
```

## CLI Reference

### Main Commands

```bash
# Download data
python main.py SYMBOLS --download [--interval INTERVAL]

# Run backtest
python main.py SYMBOLS --strategy STRATEGY [--interval INTERVAL] [--kwargs PARAMS]

# Combined download and backtest
python main.py SYMBOLS --download --strategy STRATEGY --interval INTERVAL
```

### Parameter Format

```bash
# Integer parameters
--kwargs "fast_period:int=10,slow_period:int=20"

# Float parameters
--kwargs "threshold:float=0.02,stop_loss:float=0.05"

# String parameters
--kwargs "signal_type:str=crossover"
```

### Examples

```bash
# Download 5-minute data for multiple symbols
python main.py SBIN,RELIANCE,INFY --download --interval 5

# Run strategy with custom parameters
python main.py SBIN --strategy SimpleMACross --kwargs "fast_period:int=8,slow_period:int=21"

# Test on hourly data
python main.py SBIN --strategy SimpleMACross --interval 1H

# Multiple symbols with same strategy
python main.py SBIN,RELIANCE,INFY,TCS --strategy SimpleMACross
```

## Best Practices

### Data Management
- Download data once, reuse for multiple backtests
- Use appropriate intervals for your strategy timeframe
- Monitor data quality and handle missing data

### Strategy Development
- Start with simple strategies and add complexity gradually
- Use time-based filtering for intraday strategies
- Validate parameters before optimization
- Test on multiple symbols and time periods

### Performance Optimization
- Use numba-compiled indicators when possible
- Register indicators in `init()`, not `next()`
- Minimize complex calculations in `next()` method
- Use vectorized operations for bulk analysis

### Risk Management
- Always validate strategy parameters
- Test strategies on out-of-sample data
- Monitor drawdowns and risk metrics
- Use position sizing and stop-losses appropriately

This guide provides everything needed to effectively use the StrategyTestOptimize project for backtesting and strategy development.
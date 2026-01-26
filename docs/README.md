# Enhanced Strategy Framework Documentation

## Overview

The Enhanced Strategy Framework provides a clean, intuitive interface for developing trading strategies with automatic look-ahead prevention, efficient indicator management, and built-in position tracking.

## Quick Start

```python
from strategies.Base import Base
from indicators.vectorized import SMA
from datetime_utils import is_market_hours

class MyStrategy(Base):
    def init(self):
        self.sma_fast = self.I(SMA, self.data.Close, 10)
        self.sma_slow = self.I(SMA, self.data.Close, 20)
    
    def next(self):
        # Time-based filtering using raw timestamps
        if is_market_hours(self.data.timestamps[-1]):
            if (self.sma_fast[-1] > self.sma_slow[-1] and 
                self.sma_fast[-2] <= self.sma_slow[-2]):
                self.buy()
            elif (self.sma_fast[-1] < self.sma_slow[-1] and 
                  self.sma_fast[-2] >= self.sma_slow[-2]):
                self.sell()
    
    def validate_params(self, **kwargs):
        return True
    
    @staticmethod
    def get_optimization_params():
        return {'fast_period': (5, 20), 'slow_period': (20, 50)}
```

## Key Features

- **Clean Interface**: Simple `init()` and `next()` methods
- **Efficient Indicators**: Pre-calculated once, sliced dynamically
- **Look-ahead Prevention**: Automatic data capping at current index
- **Position Management**: Built-in `buy()` and `sell()` methods
- **Raw Timestamps**: Numba-optimized integer timestamps
- **Composite Indicators**: Support for multi-value indicators

## Project Structure

```
StrategyTestOptimize/
├── main.py                 # CLI interface and backtesting
├── Utilities.py            # Data loading with raw timestamps
├── datetime_utils.py       # Numba-optimized time functions
├── strategies/Base/        # Enhanced strategy framework
├── indicators/             # Technical indicators
└── data/                   # Historical data storage
```

## Documentation

- **[Project Usage Guide](project-usage.md)** - Running backtests and optimization
- **[Strategy Development](strategy-development.md)** - Writing strategies
- **[API Reference](api-reference.md)** - Complete method documentation
- **[Migration Guide](migration-guide.md)** - Upgrading existing strategies

## Performance Benefits

| Feature | Legacy | Enhanced | Improvement |
|---------|--------|----------|-------------|
| Indicator Calculation | Every bar | Once | 10-100x faster |
| Data Access | Manual slicing | Automatic | Safer, cleaner |
| Position Tracking | Manual | Built-in | Less code |
| Look-ahead Prevention | Manual | Automatic | 100% reliable |

## Data Format

The framework uses raw Unix timestamps for maximum numba performance:

```python
# DataTuple format: (symbol, timestamps, opens, highs, lows, closes, volume)
# timestamps: np.int64 Unix timestamps (no datetime objects)
# prices: np.float64 for numba compatibility
# volume: np.int64 for numba compatibility
```

## Time-based Operations

Use `datetime_utils.py` for time-based logic:

```python
from datetime_utils import extract_hour, is_market_hours, is_opening_hour

def next(self):
    timestamp = self.data.timestamps[-1]
    
    if is_market_hours(timestamp):
        hour = extract_hour(timestamp)
        if hour == 9:  # Opening hour
            # Opening logic
            pass
```

## Getting Started

1. **[Read Project Usage Guide](project-usage.md)** - Learn to run backtests
2. **[Check Strategy Development Guide](strategy-development.md)** - Write your first strategy
3. **[Review API Reference](api-reference.md)** - Understand the methods
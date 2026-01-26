# Enhanced Strategy Framework Documentation

## Overview

The Enhanced Strategy Framework provides a clean, intuitive interface for developing trading strategies inspired by backtesting.py. It replaces complex `run()` methods with simple `init()` and `next()` methods while maintaining high performance through efficient indicator management and automatic look-ahead prevention.

## Quick Start

```python
from strategies.Base import Base
from indicators.vectorized import SMA, RSI

class MyStrategy(Base):
    def init(self):
        # Pre-calculate indicators once during initialization
        self.sma_fast = self.I(SMA, self.data.Close, 10)
        self.sma_slow = self.I(SMA, self.data.Close, 20)
        self.rsi = self.I(RSI, self.data.Close, 14)
    
    def next(self):
        # Execute strategy logic for each bar
        if (self.sma_fast[-1] > self.sma_slow[-1] and 
            self.sma_fast[-2] <= self.sma_slow[-2] and
            self.rsi[-1] < 70):
            self.buy()
        
        elif (self.sma_fast[-1] < self.sma_slow[-1] and 
              self.sma_fast[-2] >= self.sma_slow[-2]):
            self.sell()
    
    def validate_params(self, **kwargs):
        return True
    
    @staticmethod
    def get_optimization_params():
        return {
            'fast_period': (5, 20),
            'slow_period': (20, 50)
        }
```

## Key Features

### ✅ **Clean Interface**
- Simple `init()` and `next()` methods
- No complex loops or data management
- Focus on strategy logic, not infrastructure

### ✅ **Efficient Indicators**
- Pre-calculated once during initialization
- Dynamic slicing to current bar index
- No recalculation overhead during execution

### ✅ **Look-ahead Prevention**
- Automatic data capping at current index
- Built-in protection against future data leakage
- Safe array access with bounds checking

### ✅ **Position Management**
- Built-in `buy()` and `sell()` methods
- Automatic trade tracking and return calculation
- Position state management

### ✅ **Array-like Access**
- Natural `indicator[-1]` syntax for current bar
- Slice support: `indicator[1:10]`, `indicator[-5:]`
- Full numpy-style indexing

### ✅ **Composite Indicators**
- Support for multi-value indicators (Bollinger Bands, MACD, etc.)
- Named tuple, tuple, list, and dictionary returns
- Natural component access by name or index

## Architecture

The framework consists of several key components:

```
strategies/Base/
├── Base.py              # Main strategy base class
├── IndicatorWrapper.py  # Array-like indicator access
├── PositionManager.py   # Trade and position tracking
├── DataAccessor.py      # Clean OHLCV data interface
└── StrategyContext.py   # Execution state management
```

## Documentation Structure

- **[Strategy Development Guide](strategy-development.md)** - Complete guide to writing strategies
- **[Indicator System](indicator-system.md)** - Working with indicators and composite indicators
- **[Position Management](position-management.md)** - Trading operations and position tracking
- **[Data Access](data-access.md)** - Accessing market data and timestamps
- **[API Reference](api-reference.md)** - Complete class and method documentation
- **[Examples](examples/)** - Strategy examples and patterns
- **[Migration Guide](migration-guide.md)** - Upgrading from legacy run() method

## Performance Benefits

| Feature | Legacy Approach | Enhanced Approach | Improvement |
|---------|----------------|-------------------|-------------|
| Indicator Calculation | Every bar | Once during init | ~10-100x faster |
| Data Access | Manual slicing | Automatic slicing | Safer, cleaner |
| Position Tracking | Manual implementation | Built-in | Less code, fewer bugs |
| Look-ahead Prevention | Manual checking | Automatic | 100% reliable |
| Code Complexity | High (loops, state) | Low (logic only) | ~50-80% less code |

## Compatibility

### ✅ **Backward Compatible**
- Existing strategies continue to work unchanged
- Legacy `run()` method still supported
- Same `process()` method interface and output format

### ✅ **Numba Compatible**
- Works with numba-compiled indicator functions
- Maintains existing performance optimizations
- Optional numba acceleration where applicable

### ✅ **Data Format Compatible**
- Uses existing DataTuple format
- Works with current data pipeline
- Preserves timestamp handling and type specifications

## Getting Started

1. **[Read the Strategy Development Guide](strategy-development.md)** for comprehensive tutorial
2. **[Check out Examples](examples/)** for common patterns and use cases
3. **[Review API Reference](api-reference.md)** for detailed method documentation
4. **[See Migration Guide](migration-guide.md)** if upgrading existing strategies

## Support

For questions, issues, or contributions, please refer to the main project repository or documentation.
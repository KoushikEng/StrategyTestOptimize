# Strategy Development Guide

## Basic Strategy Structure

```python
from strategies.Base import Base
from indicators.vectorized import SMA
from datetime_utils import is_market_hours

class MyStrategy(Base):
    def init(self):
        # Register indicators (calculated once)
        self.sma_fast = self.I(SMA, self.data.Close, 10)
        self.sma_slow = self.I(SMA, self.data.Close, 20)
    
    def next(self):
        # Strategy logic for current bar
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

## Data Access

### OHLCV Data (Raw Timestamps)

```python
def next(self):
    # Current bar data
    current_close = self.data.Close[-1]
    current_volume = self.data.Volume[-1]
    current_timestamp = self.data.timestamps[-1]  # Raw Unix timestamp
    
    # Previous bar data
    prev_close = self.data.Close[-2]
    
    # Historical ranges
    last_10_closes = self.data.Close[-10:]
    volume_avg = np.mean(self.data.Volume[-20:])
```

### Time-based Logic (Numba-optimized)

```python
from datetime_utils import extract_hour, is_market_hours, is_opening_hour

def next(self):
    timestamp = self.data.timestamps[-1]
    
    # Fast time extraction (numba-compiled)
    if is_market_hours(timestamp):
        hour = extract_hour(timestamp)
        
        if is_opening_hour(timestamp):
            # Opening hour logic
            pass
        elif hour >= 15:  # Closing hour
            # Closing hour logic
            pass
```

## Indicator Usage

### Simple Indicators

```python
def init(self):
    self.sma = self.I(SMA, self.data.Close, 20)
    self.rsi = self.I(RSI, self.data.Close, 14)

def next(self):
    if self.sma[-1] > self.sma[-2] and self.rsi[-1] < 70:
        self.buy()
```

### Composite Indicators

```python
def init(self):
    # Named tuple return (e.g., Bollinger Bands)
    self.bb = self.I(BollingerBands, self.data.Close, 20, 2)
    
    # Tuple return (e.g., MACD)
    self.macd = self.I(MACD, self.data.Close, 12, 26, 9)

def next(self):
    # Access by field name
    if self.data.Close[-1] > self.bb.upper[-1]:
        self.sell()
    
    # Access by index
    if self.macd[0][-1] > self.macd[1][-1]:  # MACD line > Signal line
        self.buy()
```

### Array Slicing

```python
def next(self):
    # Single values
    current = self.sma[-1]
    previous = self.sma[-2]
    
    # Slices (automatic look-ahead prevention)
    last_5 = self.sma[-5:]
    range_data = self.sma[10:20]
    recent_trend = np.mean(self.sma[-10:])
```

## Position Management

```python
def next(self):
    # Check position status
    if not self.position['is_in_position']:
        if buy_condition:
            self.buy()  # Default size = 1.0
            # self.buy(size=2.0)  # Custom size
    else:
        # Access position info
        entry_price = self.position['entry_price']
        current_price = self.data.Close[-1]
        unrealized_pnl = (current_price - entry_price) / entry_price
        
        if sell_condition or unrealized_pnl < -0.05:  # 5% stop loss
            self.sell()
```

## Common Patterns

### Moving Average Crossover

```python
class MACrossStrategy(Base):
    def init(self):
        fast_period = getattr(self, 'fast_period', 10)
        slow_period = getattr(self, 'slow_period', 20)
        
        self.sma_fast = self.I(SMA, self.data.Close, fast_period)
        self.sma_slow = self.I(SMA, self.data.Close, slow_period)
    
    def next(self):
        if (self.sma_fast[-1] > self.sma_slow[-1] and 
            self.sma_fast[-2] <= self.sma_slow[-2]):
            if not self.position['is_in_position']:
                self.buy()
        elif (self.sma_fast[-1] < self.sma_slow[-1] and 
              self.sma_fast[-2] >= self.sma_slow[-2]):
            if self.position['is_in_position']:
                self.sell()
```

### RSI Mean Reversion

```python
class RSIStrategy(Base):
    def init(self):
        self.rsi = self.I(RSI, self.data.Close, 14)
        self.sma = self.I(SMA, self.data.Close, 50)
    
    def next(self):
        # Only trade when above long-term trend
        if self.data.Close[-1] > self.sma[-1]:
            if self.rsi[-1] < 30 and not self.position['is_in_position']:
                self.buy()
            elif self.rsi[-1] > 70 and self.position['is_in_position']:
                self.sell()
```

### Time-based Strategy

```python
from datetime_utils import extract_hour, is_market_hours

class TimeBasedStrategy(Base):
    def init(self):
        self.sma = self.I(SMA, self.data.Close, 20)
        self.volume_sma = self.I(SMA, self.data.Volume, 20)
    
    def next(self):
        timestamp = self.data.timestamps[-1]
        
        if is_market_hours(timestamp):
            hour = extract_hour(timestamp)
            high_volume = self.data.Volume[-1] > self.volume_sma[-1] * 1.5
            
            if hour == 9 and high_volume:  # Opening with volume
                if self.data.Close[-1] > self.sma[-1]:
                    self.buy()
            elif hour >= 15:  # Closing hour
                if self.position['is_in_position']:
                    self.sell()
```

## Parameter Optimization

```python
def init(self):
    # Extract parameters with defaults
    fast_period = getattr(self, 'fast_period', 10)
    slow_period = getattr(self, 'slow_period', 20)
    rsi_oversold = getattr(self, 'rsi_oversold', 30)
    
    self.sma_fast = self.I(SMA, self.data.Close, fast_period)
    self.sma_slow = self.I(SMA, self.data.Close, slow_period)
    self.rsi = self.I(RSI, self.data.Close, 14)

def validate_params(self, **kwargs):
    fast = kwargs.get('fast_period', 10)
    slow = kwargs.get('slow_period', 20)
    oversold = kwargs.get('rsi_oversold', 30)
    
    return (fast < slow and fast > 0 and 
            0 < oversold < 50)

@staticmethod
def get_optimization_params():
    return {
        'fast_period': (5, 20),
        'slow_period': (20, 50),
        'rsi_oversold': (20, 35)
    }
```

## Best Practices

### Efficient Indicator Usage
- Register all indicators in `init()`, never in `next()`
- Reuse indicators when possible
- Use numba-compiled indicator functions

### Clean Logic Structure
```python
def next(self):
    # 1. Time-based filtering
    if not is_market_hours(self.data.timestamps[-1]):
        return
    
    # 2. Entry conditions
    if not self.position['is_in_position']:
        if self._should_buy():
            self.buy()
    
    # 3. Exit conditions
    else:
        if self._should_sell():
            self.sell()

def _should_buy(self):
    return (self.sma_fast[-1] > self.sma_slow[-1] and 
            self.rsi[-1] < 70)

def _should_sell(self):
    return (self.sma_fast[-1] < self.sma_slow[-1] or 
            self.rsi[-1] > 80)
```

### Error Handling
```python
def next(self):
    try:
        if len(self.sma) < 2:  # Insufficient data
            return
        
        if np.isnan(self.sma[-1]):  # Invalid values
            return
        
        # Strategy logic
        
    except Exception as e:
        print(f"Strategy error at bar {self._context.get_current_index()}: {e}")
```

This guide covers the essential patterns for developing strategies with the enhanced framework, focusing on the actual implementation with raw timestamps and numba optimization.
# Strategy Development Guide

## Introduction

This guide covers everything you need to know about developing trading strategies using the Enhanced Strategy Framework. The framework provides a clean, intuitive interface that eliminates boilerplate code and focuses on strategy logic.

## Basic Strategy Structure

Every strategy inherits from the `Base` class and implements three key methods:

```python
from strategies.Base import Base

class MyStrategy(Base):
    def init(self):
        """Initialize indicators and strategy parameters."""
        # Register indicators here
        pass
    
    def next(self):
        """Process the current bar."""
        # Strategy logic here
        pass
    
    def validate_params(self, **kwargs):
        """Validate strategy parameters."""
        return True
    
    @staticmethod
    def get_optimization_params():
        """Define parameter ranges for optimization."""
        return {}
```

## The `init()` Method

The `init()` method is called once before processing any bars. Use it to:

### 1. Register Indicators

```python
def init(self):
    # Simple indicators
    self.sma20 = self.I(SMA, self.data.Close, 20)
    self.rsi = self.I(RSI, self.data.Close, 14)
    
    # Composite indicators
    self.bb = self.I(BollingerBands, self.data.Close, 20, 2)
    self.macd = self.I(MACD, self.data.Close, 12, 26, 9)
```

### 2. Initialize Strategy Variables

```python
def init(self):
    self.sma = self.I(SMA, self.data.Close, 20)
    
    # Strategy-specific variables
    self.entry_threshold = 0.02
    self.stop_loss = 0.05
    self.last_signal = None
```

### 3. Access Strategy Parameters

```python
def init(self):
    # Parameters passed via kwargs to process()
    fast_period = getattr(self, 'fast_period', 10)
    slow_period = getattr(self, 'slow_period', 20)
    
    self.sma_fast = self.I(SMA, self.data.Close, fast_period)
    self.sma_slow = self.I(SMA, self.data.Close, slow_period)
```

## The `next()` Method

The `next()` method is called for each bar in the dataset. Use it to:

### 1. Implement Entry Logic

```python
def next(self):
    # Moving average crossover entry
    if (self.sma_fast[-1] > self.sma_slow[-1] and 
        self.sma_fast[-2] <= self.sma_slow[-2]):
        if not self.position['is_in_position']:
            self.buy()
```

### 2. Implement Exit Logic

```python
def next(self):
    # RSI overbought exit
    if self.position['is_in_position'] and self.rsi[-1] > 70:
        self.sell()
```

### 3. Access Current and Historical Data

```python
def next(self):
    # Current bar data
    current_close = self.data.Close[-1]
    current_volume = self.data.Volume[-1]
    
    # Previous bar data
    prev_close = self.data.Close[-2]
    prev_high = self.data.High[-2]
    
    # Historical data ranges
    recent_closes = self.data.Close[-10:]  # Last 10 bars
    volume_avg = np.mean(self.data.Volume[-20:])  # 20-bar volume average
```

## Data Access

### OHLCV Data

Access market data through `self.data`:

```python
def next(self):
    # Price data
    open_price = self.data.Open[-1]
    high_price = self.data.High[-1]
    low_price = self.data.Low[-1]
    close_price = self.data.Close[-1]
    volume = self.data.Volume[-1]
    
    # Timestamp data (Unix timestamp)
    timestamp = self.data.timestamps[-1]
```

### Array Slicing

All data supports numpy-style slicing:

```python
def next(self):
    # Single values
    current = self.data.Close[-1]
    previous = self.data.Close[-2]
    
    # Ranges
    last_5 = self.data.Close[-5:]
    range_data = self.data.Close[10:20]
    every_other = self.data.Close[::2]
```

### Time-based Logic

Use datetime utilities for time-based strategies:

```python
from datetime_utils import extract_hour, is_market_hours

def next(self):
    current_timestamp = self.data.timestamps[-1]
    
    # Time-based conditions
    if is_market_hours(current_timestamp):
        hour = extract_hour(current_timestamp)
        
        if hour == 9:  # Opening hour
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
    self.ema = self.I(EMA, self.data.Close, 12)
    self.rsi = self.I(RSI, self.data.Close, 14)

def next(self):
    # Current values
    sma_current = self.sma[-1]
    ema_current = self.ema[-1]
    
    # Previous values
    sma_prev = self.sma[-2]
    
    # Historical ranges
    sma_last_10 = self.sma[-10:]
```

### Composite Indicators

#### Named Tuple Returns (e.g., Bollinger Bands)

```python
def init(self):
    # Assuming BB returns namedtuple(middle, upper, lower)
    self.bb = self.I(BollingerBands, self.data.Close, 20, 2)

def next(self):
    # Access by field name
    middle = self.bb.middle[-1]
    upper = self.bb.upper[-1]
    lower = self.bb.lower[-1]
    
    # Trading logic
    if self.data.Close[-1] > upper:
        self.sell()  # Price above upper band
    elif self.data.Close[-1] < lower:
        self.buy()   # Price below lower band
```

#### Tuple/List Returns (e.g., MACD)

```python
def init(self):
    # Assuming MACD returns (macd_line, signal_line, histogram)
    self.macd = self.I(MACD, self.data.Close, 12, 26, 9)

def next(self):
    # Access by index
    macd_line = self.macd[0][-1]
    signal_line = self.macd[1][-1]
    histogram = self.macd[2][-1]
    
    # MACD crossover
    if macd_line > signal_line and self.macd[0][-2] <= self.macd[1][-2]:
        self.buy()
```

#### Dictionary Returns (e.g., Stochastic)

```python
def init(self):
    # Assuming Stochastic returns {'%K': k_values, '%D': d_values}
    self.stoch = self.I(Stochastic, self.data.High, self.data.Low, self.data.Close, 14, 3)

def next(self):
    # Access by key
    k_value = self.stoch['%K'][-1]
    d_value = self.stoch['%D'][-1]
    
    # Oversold/overbought conditions
    if k_value < 20 and d_value < 20:
        self.buy()  # Oversold
    elif k_value > 80 and d_value > 80:
        self.sell()  # Overbought
```

## Position Management

### Opening Positions

```python
def next(self):
    # Simple buy
    if buy_condition:
        self.buy()  # Default size = 1.0
    
    # Buy with specific size
    if strong_buy_condition:
        self.buy(size=2.0)  # Double position size
```

### Closing Positions

```python
def next(self):
    # Close entire position
    if exit_condition:
        self.sell()
    
    # Partial close (if supported in future versions)
    # self.sell(size=0.5)  # Close half position
```

### Position Information

```python
def next(self):
    # Check position status
    pos_info = self.position
    
    if pos_info['is_in_position']:
        entry_price = pos_info['entry_price']
        position_size = pos_info['position_size']
        entry_index = pos_info['entry_index']
        
        # Calculate unrealized P&L
        current_price = self.data.Close[-1]
        unrealized_pnl = (current_price - entry_price) / entry_price
        
        # Exit based on P&L
        if unrealized_pnl > 0.10:  # 10% profit
            self.sell()
        elif unrealized_pnl < -0.05:  # 5% loss
            self.sell()
```

## Common Patterns

### Moving Average Crossover

```python
class MACrossStrategy(Base):
    def init(self):
        self.sma_fast = self.I(SMA, self.data.Close, 10)
        self.sma_slow = self.I(SMA, self.data.Close, 20)
    
    def next(self):
        # Golden cross - buy signal
        if (self.sma_fast[-1] > self.sma_slow[-1] and 
            self.sma_fast[-2] <= self.sma_slow[-2]):
            if not self.position['is_in_position']:
                self.buy()
        
        # Death cross - sell signal
        elif (self.sma_fast[-1] < self.sma_slow[-1] and 
              self.sma_fast[-2] >= self.sma_slow[-2]):
            if self.position['is_in_position']:
                self.sell()
```

### RSI Mean Reversion

```python
class RSIMeanReversion(Base):
    def init(self):
        self.rsi = self.I(RSI, self.data.Close, 14)
        self.sma = self.I(SMA, self.data.Close, 50)
    
    def next(self):
        # Only trade when price is above long-term trend
        if self.data.Close[-1] > self.sma[-1]:
            # Buy oversold
            if self.rsi[-1] < 30 and not self.position['is_in_position']:
                self.buy()
            
            # Sell overbought
            elif self.rsi[-1] > 70 and self.position['is_in_position']:
                self.sell()
```

### Bollinger Band Squeeze

```python
class BBSqueezeStrategy(Base):
    def init(self):
        self.bb = self.I(BollingerBands, self.data.Close, 20, 2)
        self.volume_sma = self.I(SMA, self.data.Volume, 20)
    
    def next(self):
        # Calculate band width
        band_width = (self.bb.upper[-1] - self.bb.lower[-1]) / self.bb.middle[-1]
        avg_band_width = np.mean([(self.bb.upper[i] - self.bb.lower[i]) / self.bb.middle[i] 
                                  for i in range(-20, 0)])
        
        # High volume breakout from squeeze
        if (band_width < avg_band_width * 0.5 and  # Squeeze condition
            self.data.Volume[-1] > self.volume_sma[-1] * 1.5):  # High volume
            
            if self.data.Close[-1] > self.bb.upper[-1]:
                self.buy()  # Upward breakout
            elif self.data.Close[-1] < self.bb.lower[-1]:
                self.sell()  # Downward breakout
```

## Parameter Optimization

### Define Optimization Parameters

```python
@staticmethod
def get_optimization_params():
    return {
        'fast_period': (5, 20),      # Range: 5 to 20
        'slow_period': (20, 50),     # Range: 20 to 50
        'rsi_period': (10, 20),      # Range: 10 to 20
        'rsi_oversold': (20, 35),    # Range: 20 to 35
        'rsi_overbought': (65, 80)   # Range: 65 to 80
    }
```

### Use Parameters in Strategy

```python
def init(self):
    # Get parameters with defaults
    fast_period = 10
    slow_period = 20
    rsi_period = 14
    
    self.rsi_oversold = 30
    self.rsi_overbought = 70

    self.sma_fast = self.I(SMA, self.data.Close, fast_period)
    self.sma_slow = self.I(SMA, self.data.Close, slow_period)
    self.rsi = self.I(RSI, self.data.Close, rsi_period)

def next(self):
    
    if self.rsi[-1] < self.rsi_oversold:
        self.buy()
    elif self.rsi[-1] > self.rsi_overbought:
        self.sell()
```

## Best Practices

### 1. **Efficient Indicator Usage**
- Register all indicators in `init()`, not in `next()`
- Reuse indicators when possible
- Use vectorized indicator functions for best performance

### 2. **Clean Logic Structure**
```python
def next(self):
    # 1. Calculate derived values
    price_change = (self.data.Close[-1] - self.data.Close[-2]) / self.data.Close[-2]
    
    # 2. Check entry conditions
    if not self.position['is_in_position']:
        if self._should_buy():
            self.buy()
    
    # 3. Check exit conditions
    else:
        if self._should_sell():
            self.sell()

def _should_buy(self):
    """Helper method for buy conditions."""
    return (self.sma_fast[-1] > self.sma_slow[-1] and 
            self.rsi[-1] < 70)

def _should_sell(self):
    """Helper method for sell conditions."""
    return (self.sma_fast[-1] < self.sma_slow[-1] or 
            self.rsi[-1] > 80)
```

### 3. **Error Handling**
```python
def next(self):
    try:
        # Strategy logic
        if len(self.sma) < 2:  # Not enough data
            return
        
        # Rest of strategy logic
        
    except Exception as e:
        # Log error but don't crash
        print(f"Strategy error at bar {self._context.get_current_index()}: {e}")
```

### 4. **Parameter Validation**
```python
def validate_params(self, **kwargs):
    fast_period = kwargs.get('fast_period', 10)
    slow_period = kwargs.get('slow_period', 20)
    
    if fast_period >= slow_period:
        return False  # Fast period must be less than slow period
    
    if fast_period < 1 or slow_period < 1:
        return False  # Periods must be positive
    
    return True
```

## Debugging and Testing

### Print Current State

```python
def next(self):
    # Debug current bar
    current_bar = self._context.get_current_index()
    
    if current_bar % 100 == 0:  # Every 100 bars
        print(f"Bar {current_bar}: Close={self.data.Close[-1]:.2f}, "
              f"SMA={self.sma[-1]:.2f}, RSI={self.rsi[-1]:.2f}")
    
    # Strategy logic...
```

### Validate Indicator Values

```python
def next(self):
    # Check for NaN values
    if np.isnan(self.sma[-1]) or np.isnan(self.rsi[-1]):
        return  # Skip this bar
    
    # Strategy logic...
```

This comprehensive guide covers all aspects of strategy development using the Enhanced Strategy Framework. For more examples and advanced patterns, see the [Examples](examples/) directory.
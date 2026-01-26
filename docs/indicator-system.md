# Indicator System

## Overview

The Enhanced Strategy Framework provides a powerful indicator system that pre-calculates indicators once during initialization and provides efficient, safe access during strategy execution. The system supports both simple single-value indicators and complex multi-value indicators.

## Basic Indicator Usage

### Registering Indicators

Use the `I()` method in your strategy's `init()` method to register indicators:

```python
def init(self):
    # Simple indicators
    self.sma20 = self.I(SMA, self.data.Close, 20)
    self.ema12 = self.I(EMA, self.data.Close, 12)
    self.rsi = self.I(RSI, self.data.Close, 14)
    
    # Indicators with multiple parameters
    self.stoch = self.I(Stochastic, self.data.High, self.data.Low, self.data.Close, 14, 3)
```

### Accessing Indicator Values

Once registered, indicators provide array-like access with automatic look-ahead prevention:

```python
def next(self):
    # Current bar values
    current_sma = self.sma20[-1]
    current_rsi = self.rsi[-1]
    
    # Previous bar values
    prev_sma = self.sma20[-2]
    prev_rsi = self.rsi[-2]
    
    # Historical ranges
    last_5_sma = self.sma20[-5:]
    sma_range = self.sma20[10:20]
```

## Indicator Types

### 1. Simple Indicators

Simple indicators return a single numpy array:

```python
# Example indicator functions
def SMA(data, period):
    """Simple Moving Average"""
    return np.convolve(data, np.ones(period)/period, mode='valid')

def RSI(data, period):
    """Relative Strength Index"""
    # RSI calculation logic
    return rsi_values

def EMA(data, period):
    """Exponential Moving Average"""
    # EMA calculation logic
    return ema_values
```

**Usage in Strategy:**
```python
def init(self):
    self.sma = self.I(SMA, self.data.Close, 20)
    self.rsi = self.I(RSI, self.data.Close, 14)

def next(self):
    if self.sma[-1] > self.sma[-2] and self.rsi[-1] < 70:
        self.buy()
```

### 2. Composite Indicators

Composite indicators return multiple arrays in various formats:

#### Named Tuple Returns

```python
from collections import namedtuple

BBands = namedtuple('BBands', ['middle', 'upper', 'lower'])

def BollingerBands(data, period, std_dev):
    """Bollinger Bands returning named tuple"""
    middle = SMA(data, period)
    std = np.std(data, period)
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    
    return BBands(middle, upper, lower)
```

**Usage in Strategy:**
```python
def init(self):
    self.bb = self.I(BollingerBands, self.data.Close, 20, 2)

def next(self):
    # Access by field name
    if self.data.Close[-1] > self.bb.upper[-1]:
        self.sell()  # Price above upper band
    elif self.data.Close[-1] < self.bb.lower[-1]:
        self.buy()   # Price below lower band
    
    # Check band squeeze
    band_width = self.bb.upper[-1] - self.bb.lower[-1]
    avg_width = np.mean(self.bb.upper[-20:] - self.bb.lower[-20:])
    
    if band_width < avg_width * 0.5:
        # Bollinger Band squeeze detected
        pass
```

#### Tuple/List Returns

```python
def MACD(data, fast_period, slow_period, signal_period):
    """MACD returning tuple of (macd_line, signal_line, histogram)"""
    ema_fast = EMA(data, fast_period)
    ema_slow = EMA(data, slow_period)
    macd_line = ema_fast - ema_slow
    signal_line = EMA(macd_line, signal_period)
    histogram = macd_line - signal_line
    
    return (macd_line, signal_line, histogram)
```

**Usage in Strategy:**
```python
def init(self):
    self.macd = self.I(MACD, self.data.Close, 12, 26, 9)

def next(self):
    # Access by index
    macd_line = self.macd[0][-1]
    signal_line = self.macd[1][-1]
    histogram = self.macd[2][-1]
    
    # MACD crossover
    if (macd_line > signal_line and 
        self.macd[0][-2] <= self.macd[1][-2]):
        self.buy()
    
    # MACD divergence
    if (histogram > 0 and self.macd[2][-2] <= 0):
        # Bullish divergence
        pass
```

#### Dictionary Returns

```python
def Stochastic(high, low, close, k_period, d_period):
    """Stochastic returning dictionary"""
    # Stochastic calculation
    k_values = calculate_stoch_k(high, low, close, k_period)
    d_values = SMA(k_values, d_period)
    
    return {
        '%K': k_values,
        '%D': d_values
    }
```

**Usage in Strategy:**
```python
def init(self):
    self.stoch = self.I(Stochastic, self.data.High, self.data.Low, self.data.Close, 14, 3)

def next(self):
    # Access by key
    k_value = self.stoch['%K'][-1]
    d_value = self.stoch['%D'][-1]
    
    # Stochastic signals
    if k_value < 20 and d_value < 20:
        self.buy()  # Oversold
    elif k_value > 80 and d_value > 80:
        self.sell()  # Overbought
    
    # Stochastic crossover
    if (k_value > d_value and 
        self.stoch['%K'][-2] <= self.stoch['%D'][-2]):
        # %K crossed above %D
        pass
```

## Advanced Indicator Patterns

### Multi-Timeframe Indicators

```python
def init(self):
    # Different timeframe data would need to be prepared separately
    # This is a conceptual example
    self.sma_daily = self.I(SMA, self.daily_closes, 20)
    self.sma_hourly = self.I(SMA, self.data.Close, 20)

def next(self):
    # Align timeframes and compare
    if self.sma_hourly[-1] > self.sma_daily[-1]:
        # Short-term above long-term trend
        pass
```

### Custom Composite Indicators

```python
def TrendStrength(high, low, close, volume, period):
    """Custom indicator combining price and volume"""
    price_momentum = (close - SMA(close, period)) / SMA(close, period)
    volume_ratio = volume / SMA(volume, period)
    trend_strength = price_momentum * volume_ratio
    
    return {
        'strength': trend_strength,
        'price_momentum': price_momentum,
        'volume_ratio': volume_ratio
    }
```

**Usage:**
```python
def init(self):
    self.trend = self.I(TrendStrength, 
                       self.data.High, self.data.Low, 
                       self.data.Close, self.data.Volume, 20)

def next(self):
    strength = self.trend['strength'][-1]
    price_mom = self.trend['price_momentum'][-1]
    vol_ratio = self.trend['volume_ratio'][-1]
    
    if strength > 0.1 and vol_ratio > 1.5:
        self.buy()  # Strong trend with high volume
```

### Indicator Combinations

```python
def init(self):
    # Multiple indicators for confluence
    self.sma_fast = self.I(SMA, self.data.Close, 10)
    self.sma_slow = self.I(SMA, self.data.Close, 20)
    self.rsi = self.I(RSI, self.data.Close, 14)
    self.bb = self.I(BollingerBands, self.data.Close, 20, 2)
    self.volume_sma = self.I(SMA, self.data.Volume, 20)

def next(self):
    # Multi-indicator confluence
    ma_bullish = self.sma_fast[-1] > self.sma_slow[-1]
    rsi_not_overbought = self.rsi[-1] < 70
    price_near_lower_bb = self.data.Close[-1] < self.bb.lower[-1] * 1.02
    high_volume = self.data.Volume[-1] > self.volume_sma[-1] * 1.5
    
    if ma_bullish and rsi_not_overbought and price_near_lower_bb and high_volume:
        self.buy()  # All conditions aligned
```

## Indicator Caching and Performance

### Automatic Caching

The framework automatically caches indicator calculations:

```python
def init(self):
    # These will be calculated once and cached
    self.sma1 = self.I(SMA, self.data.Close, 20)
    self.sma2 = self.I(SMA, self.data.Close, 20)  # Reuses cached result
    
    # Different parameters = different cache entry
    self.sma3 = self.I(SMA, self.data.Close, 21)  # New calculation
```

### Cache Key Generation

Cache keys are generated based on:
- Function name
- Function arguments (including array content hashes)
- Keyword arguments

```python
# These create different cache entries:
self.sma_close = self.I(SMA, self.data.Close, 20)
self.sma_high = self.I(SMA, self.data.High, 20)    # Different input array
self.sma_21 = self.I(SMA, self.data.Close, 21)     # Different period

# These reuse the same cache entry:
self.sma_a = self.I(SMA, self.data.Close, 20)
self.sma_b = self.I(SMA, self.data.Close, 20)      # Same parameters
```

### Performance Tips

1. **Register indicators in `init()`, not `next()`:**
```python
# Good
def init(self):
    self.sma = self.I(SMA, self.data.Close, 20)

def next(self):
    if self.sma[-1] > self.sma[-2]:
        self.buy()

# Bad - recalculates every bar
def next(self):
    sma = self.I(SMA, self.data.Close, 20)  # Don't do this!
    if sma[-1] > sma[-2]:
        self.buy()
```

2. **Reuse indicators when possible:**
```python
def init(self):
    self.sma20 = self.I(SMA, self.data.Close, 20)
    # Reuse for multiple purposes
    
def next(self):
    # Use same indicator for multiple conditions
    sma_current = self.sma20[-1]
    sma_prev = self.sma20[-2]
    sma_avg = np.mean(self.sma20[-10:])
```

3. **Use vectorized indicator functions:**
```python
# Prefer vectorized implementations
def SMA_vectorized(data, period):
    return np.convolve(data, np.ones(period)/period, mode='valid')

# Over loop-based implementations
def SMA_slow(data, period):
    result = []
    for i in range(period-1, len(data)):
        result.append(np.mean(data[i-period+1:i+1]))
    return np.array(result)
```

## Error Handling

### Common Indicator Errors

```python
def init(self):
    try:
        self.sma = self.I(SMA, self.data.Close, 20)
    except ValueError as e:
        print(f"SMA calculation failed: {e}")
        # Handle error or use default
    except RuntimeError as e:
        print(f"Indicator registration failed: {e}")
```

### Validation

```python
def next(self):
    # Check for sufficient data
    if len(self.sma) < 2:
        return  # Not enough data for comparison
    
    # Check for NaN values
    if np.isnan(self.sma[-1]):
        return  # Skip this bar
    
    # Strategy logic
    if self.sma[-1] > self.sma[-2]:
        self.buy()
```

### Debugging Indicators

```python
def init(self):
    self.sma = self.I(SMA, self.data.Close, 20)
    
    # Debug indicator values
    print(f"SMA length: {len(self.sma.values)}")
    print(f"First 5 SMA values: {self.sma.values[:5]}")
    print(f"Last 5 SMA values: {self.sma.values[-5:]}")

def next(self):
    current_bar = self._context.get_current_index()
    
    if current_bar % 100 == 0:  # Every 100 bars
        print(f"Bar {current_bar}: SMA={self.sma[-1]:.2f}, Close={self.data.Close[-1]:.2f}")
```

## Best Practices

### 1. Indicator Organization

```python
def init(self):
    # Group related indicators
    # Trend indicators
    self.sma_fast = self.I(SMA, self.data.Close, 10)
    self.sma_slow = self.I(SMA, self.data.Close, 20)
    self.ema = self.I(EMA, self.data.Close, 12)
    
    # Momentum indicators
    self.rsi = self.I(RSI, self.data.Close, 14)
    self.macd = self.I(MACD, self.data.Close, 12, 26, 9)
    
    # Volatility indicators
    self.bb = self.I(BollingerBands, self.data.Close, 20, 2)
    self.atr = self.I(ATR, self.data.High, self.data.Low, self.data.Close, 14)
```

### 2. Parameter Management

```python
def init(self):
    # Use parameters for flexibility
    sma_period = getattr(self, 'sma_period', 20)
    rsi_period = getattr(self, 'rsi_period', 14)
    
    self.sma = self.I(SMA, self.data.Close, sma_period)
    self.rsi = self.I(RSI, self.data.Close, rsi_period)
```

### 3. Indicator Validation

```python
def validate_params(self, **kwargs):
    sma_period = kwargs.get('sma_period', 20)
    rsi_period = kwargs.get('rsi_period', 14)
    
    if sma_period < 1 or rsi_period < 1:
        return False
    
    if sma_period > len(self.data.Close) // 2:
        return False  # Period too large for dataset
    
    return True
```

This comprehensive guide covers all aspects of the indicator system in the Enhanced Strategy Framework. The system provides flexibility, performance, and safety while maintaining a clean, intuitive interface.
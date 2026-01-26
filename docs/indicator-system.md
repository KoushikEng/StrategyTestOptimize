# Indicator System

## Basic Usage

```python
def init(self):
    # Simple indicators
    self.sma = self.I(SMA, self.data.Close, 20)
    self.rsi = self.I(RSI, self.data.Close, 14)
    
    # Composite indicators
    self.bb = self.I(BollingerBands, self.data.Close, 20, 2)
    self.macd = self.I(MACD, self.data.Close, 12, 26, 9)

def next(self):
    # Array-like access with automatic look-ahead prevention
    if self.sma[-1] > self.sma[-2]:
        self.buy()
```

## Composite Indicators

### Named Tuple Returns (Bollinger Bands)

```python
def init(self):
    self.bb = self.I(BollingerBands, self.data.Close, 20, 2)

def next(self):
    # Access by field name
    if self.data.Close[-1] > self.bb.upper[-1]:
        self.sell()
    elif self.data.Close[-1] < self.bb.lower[-1]:
        self.buy()
```

### Tuple Returns (MACD)

```python
def init(self):
    self.macd = self.I(MACD, self.data.Close, 12, 26, 9)

def next(self):
    # Access by index: (macd_line, signal_line, histogram)
    if self.macd[0][-1] > self.macd[1][-1]:  # MACD > Signal
        self.buy()
```

### Dictionary Returns (Stochastic)

```python
def init(self):
    self.stoch = self.I(Stochastic, self.data.High, self.data.Low, self.data.Close, 14, 3)

def next(self):
    # Access by key
    if self.stoch['%K'][-1] < 20 and self.stoch['%D'][-1] < 20:
        self.buy()  # Oversold
```

## Array Access Patterns

```python
def next(self):
    # Single values
    current = self.sma[-1]
    previous = self.sma[-2]
    
    # Slices (automatic look-ahead prevention)
    last_5 = self.sma[-5:]
    range_data = self.sma[10:20]
    
    # Use in calculations
    trend = np.mean(self.sma[-10:])
    volatility = np.std(self.data.Close[-20:])
```

## Performance Features

- **Pre-calculated once** during `init()` - no recalculation overhead
- **Automatic caching** - same parameters reuse cached results
- **Dynamic slicing** - efficient `[:current_index]` operations
- **Numba compatible** - works with numba-compiled indicator functions

## Best Practices

```python
def init(self):
    # Good - register in init()
    self.sma = self.I(SMA, self.data.Close, 20)
    
    # Reuse indicators
    self.sma_current = self.sma  # Same reference

def next(self):
    # Good - use registered indicators
    if self.sma[-1] > self.sma[-2]:
        self.buy()
    
    # Bad - don't register in next()
    # sma = self.I(SMA, self.data.Close, 20)  # Recalculates every bar!
```
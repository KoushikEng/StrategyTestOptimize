# API Reference

## Core Classes

### Base Class

**Location:** `strategies/Base/Base.py`

The main base class for all trading strategies.

#### Constructor

```python
def __init__(self):
```

Initializes the strategy with:
- `_context`: StrategyContext instance for execution state
- `_position_manager`: PositionManager instance for trade tracking
- `_indicators`: Dictionary for caching registered indicators
- `data`: DataAccessor instance (set during execution)

#### Abstract Methods

##### `init()`

```python
@abstractmethod
def init(self):
    """Initialize strategy indicators and parameters."""
```

Called once before processing any bars. Use to register indicators and initialize strategy variables.

**Usage:**
```python
def init(self):
    self.sma = self.I(SMA, self.data.Close, 20)
    self.rsi = self.I(RSI, self.data.Close, 14)
```

##### `next()`

```python
@abstractmethod
def next(self):
    """Process the current bar."""
```

Called for each bar in the dataset. Implement your strategy logic here.

**Usage:**
```python
def next(self):
    if self.sma[-1] > self.sma[-2]:
        self.buy()
```

##### `validate_params(**kwargs)`

```python
@abstractmethod
def validate_params(self, **kwargs) -> bool:
```

Validate strategy parameters before execution.

**Parameters:**
- `**kwargs`: Strategy parameters to validate

**Returns:**
- `bool`: True if parameters are valid, False otherwise

##### `get_optimization_params()`

```python
@staticmethod
@abstractmethod
def get_optimization_params():
```

Define parameter ranges for optimization.

**Returns:**
- `Dict[str, Tuple[float, float]]`: Parameter name to (min, max) range mapping

#### Core Methods

##### `I(func, *args, **kwargs)`

```python
def I(self, func: Callable, *args, **kwargs) -> Union[IndicatorWrapper, CompositeIndicatorWrapper]:
```

Register and calculate an indicator.

**Parameters:**
- `func`: Indicator calculation function
- `*args`: Arguments to pass to the indicator function
- `**kwargs`: Keyword arguments to pass to the indicator function

**Returns:**
- `IndicatorWrapper`: For single-array indicators
- `CompositeIndicatorWrapper`: For multi-array indicators (tuples, namedtuples, dicts)

**Usage:**
```python
# Simple indicator
self.sma = self.I(SMA, self.data.Close, 20)

# Composite indicator
self.bb = self.I(BollingerBands, self.data.Close, 20, 2)
```

##### `buy(size=1.0)`

```python
def buy(self, size: float = 1.0):
```

Open a long position.

**Parameters:**
- `size`: Position size (default: 1.0)

**Raises:**
- `ValueError`: If already in position
- `RuntimeError`: If called before data is set

##### `sell(size=None)`

```python
def sell(self, size: float = None):
```

Close current position.

**Parameters:**
- `size`: Amount to close (currently unused, closes entire position)

**Returns:**
- `float`: Trade return percentage

**Raises:**
- `ValueError`: If no position to close
- `RuntimeError`: If called before data is set

##### `position` (property)

```python
@property
def position(self) -> dict:
```

Get current position information.

**Returns:**
- `dict`: Position information with keys:
  - `is_in_position`: bool
  - `position_size`: float
  - `entry_price`: float
  - `entry_index`: int

#### Execution Methods

##### `process(data, **kwargs)`

```python
def process(self, data: DataTuple, **kwargs) -> Tuple[NDArray, NDArray, float, int]:
```

Main execution method maintaining backward compatibility.

**Parameters:**
- `data`: DataTuple (symbol, timestamps, opens, highs, lows, closes, volume)
- `**kwargs`: Strategy parameters

**Returns:**
- `Tuple`: (returns, equity_curve, win_rate, total_trades)

---

### IndicatorWrapper Class

**Location:** `strategies/Base/IndicatorWrapper.py`

Provides array-like access to pre-calculated indicator values with automatic look-ahead prevention.

#### Constructor

```python
def __init__(self, values: np.ndarray, context: StrategyContext):
```

**Parameters:**
- `values`: Pre-calculated indicator values
- `context`: StrategyContext for current index tracking

#### Methods

##### `__getitem__(key)`

```python
def __getitem__(self, key):
```

Access indicator values with negative indexing and slice support.

**Parameters:**
- `key`: int or slice for accessing values

**Returns:**
- `float`: For single index access
- `np.ndarray`: For slice access

**Usage:**
```python
current = indicator[-1]        # Current bar
previous = indicator[-2]       # Previous bar
last_5 = indicator[-5:]        # Last 5 bars
range_data = indicator[1:10]   # Specific range
```

##### `__len__()`

```python
def __len__(self) -> int:
```

Return the length up to current index.

##### `values` (property)

```python
@property
def values(self) -> np.ndarray:
```

Get values up to current index to prevent look-ahead bias.

**Returns:**
- `np.ndarray`: Copy of values up to current index

---

### CompositeIndicatorWrapper Class

**Location:** `strategies/Base/Base.py`

Wrapper for indicators that return multiple arrays (e.g., Bollinger Bands, MACD).

#### Constructor

```python
def __init__(self, result: Union[tuple, list, dict], context: StrategyContext, key: str):
```

**Parameters:**
- `result`: Multi-array result from indicator function
- `context`: StrategyContext for current index tracking
- `key`: Unique identifier for caching

#### Methods

##### `__getattr__(name)`

```python
def __getattr__(self, name: str) -> IndicatorWrapper:
```

Access indicator components by name (for namedtuples and dicts).

**Usage:**
```python
# For Bollinger Bands namedtuple(middle, upper, lower)
middle = bb.middle[-1]
upper = bb.upper[-1]
lower = bb.lower[-1]
```

##### `__getitem__(index)`

```python
def __getitem__(self, index: Union[int, str]) -> IndicatorWrapper:
```

Access indicator components by index or key.

**Usage:**
```python
# For MACD tuple (macd_line, signal_line, histogram)
macd_line = macd[0][-1]
signal_line = macd[1][-1]

# For Stochastic dict {'%K': k_values, '%D': d_values}
k_value = stoch['%K'][-1]
```

##### `components` (property)

```python
@property
def components(self) -> dict:
```

Get all available components.

---

### DataAccessor Class

**Location:** `strategies/Base/DataAccessor.py`

Provides clean access to OHLCV market data with automatic slicing.

#### Constructor

```python
def __init__(self, data: DataTuple, context: StrategyContext):
```

**Parameters:**
- `data`: DataTuple (symbol, timestamps, opens, highs, lows, closes, volume)
- `context`: StrategyContext for current index tracking

#### Properties

All properties return `IndicatorWrapper` instances with automatic look-ahead prevention:

- `Open`: Opening prices
- `High`: High prices  
- `Low`: Low prices
- `Close`: Closing prices
- `Volume`: Volume data
- `timestamps`: Unix timestamps

**Usage:**
```python
current_close = self.data.Close[-1]
prev_high = self.data.High[-2]
last_10_volumes = self.data.Volume[-10:]
```

---

### PositionManager Class

**Location:** `strategies/Base/PositionManager.py`

Handles position tracking and trade execution.

#### Constructor

```python
def __init__(self):
```

Initializes with empty position state and trade history.

#### Methods

##### `open_position(price, size, index)`

```python
def open_position(self, price: float, size: float, index: int):
```

Open a new position.

**Parameters:**
- `price`: Entry price
- `size`: Position size
- `index`: Bar index of entry

**Raises:**
- `ValueError`: If already in position

##### `close_position(price, index)`

```python
def close_position(self, price: float, index: int) -> float:
```

Close current position.

**Parameters:**
- `price`: Exit price
- `index`: Bar index of exit

**Returns:**
- `float`: Trade return percentage

**Raises:**
- `ValueError`: If no position to close

##### `is_in_position()`

```python
def is_in_position(self) -> bool:
```

Check if currently in a position.

##### `get_current_position_info()`

```python
def get_current_position_info(self) -> dict:
```

Get current position information.

**Returns:**
- `dict`: Position details

##### `get_trade_returns()`

```python
def get_trade_returns(self) -> np.ndarray:
```

Get all completed trade returns.

##### `get_trade_count()`

```python
def get_trade_count(self) -> int:
```

Get total number of completed trades.

---

### StrategyContext Class

**Location:** `strategies/Base/StrategyContext.py`

Manages execution state and prevents look-ahead bias.

#### Constructor

```python
def __init__(self):
```

Initializes with current index = 0 and data length = 0.

#### Methods

##### `update_index(index)`

```python
def update_index(self, index: int):
```

Update the current bar index.

**Parameters:**
- `index`: New current bar index

**Raises:**
- `IndexError`: If index is out of bounds

##### `get_current_index()`

```python
def get_current_index(self) -> int:
```

Get the current bar index.

##### `set_data_length(length)`

```python
def set_data_length(self, length: int):
```

Set the total data length.

**Parameters:**
- `length`: Total number of bars in dataset

---

## Data Types

### DataTuple

```python
DataTuple = Tuple[str, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]
```

Format: `(symbol, timestamps, opens, highs, lows, closes, volume)`

- `symbol`: str - Symbol name
- `timestamps`: np.ndarray[np.int64] - Unix timestamps
- `opens`: np.ndarray[np.float64] - Opening prices
- `highs`: np.ndarray[np.float64] - High prices
- `lows`: np.ndarray[np.float64] - Low prices
- `closes`: np.ndarray[np.float64] - Closing prices
- `volume`: np.ndarray[np.int64] - Volume data

### StrategyResults

```python
@dataclass
class StrategyResults:
    returns: np.ndarray      # Individual trade returns
    equity_curve: np.ndarray # Cumulative equity curve
    win_rate: float          # Percentage of winning trades
    total_trades: int        # Total number of trades
```

## Error Handling

### Common Exceptions

#### `TypeError`
- Raised when indicator function is not callable
- Raised when invalid index types are used

#### `ValueError`
- Raised when indicator arrays have wrong length
- Raised when trying to open position while already in position
- Raised when trying to close position when not in position
- Raised when indicator function returns empty results

#### `RuntimeError`
- Raised when trying to register indicators before data is set
- Raised when indicator calculation fails

#### `IndexError`
- Raised when accessing invalid array indices
- Raised when trying to access future data (look-ahead prevention)
- Raised when context index is out of bounds

### Error Messages

All error messages are descriptive and include context:

```python
# Example error messages
"Index -5 would access data before start of series"
"Index 100 would access future data (current bar: 50)"
"Indicator length 95 doesn't match data length 100"
"Already in position. Close current position before opening new one."
"Failed to register indicator SMA: Invalid period parameter"
```

## Performance Considerations

### Indicator Caching

- Indicators are calculated once during `init()` and cached
- Same indicator calls with identical parameters reuse cached results
- Caching key includes function name, arguments, and array content hashes

### Memory Usage

- `IndicatorWrapper.values` returns copies to prevent modification
- Slice operations return copies of underlying arrays
- Full indicator arrays are stored in memory for fast access

### Look-ahead Prevention

- All data access is automatically bounded by current index
- No performance penalty for safety checks
- Slice operations are optimized for common patterns

### Numba Compatibility

- Framework works with numba-compiled indicator functions
- Core execution loop can be numba-optimized
- Type-stable operations throughout the framework
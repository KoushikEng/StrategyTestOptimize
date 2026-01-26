# Strategy Examples

This directory contains comprehensive examples demonstrating various patterns and techniques using the Enhanced Strategy Framework.

## Basic Examples

### [Simple Moving Average Crossover](simple-ma-crossover.py)
- Basic trend-following strategy
- Demonstrates `init()` and `next()` methods
- Shows position management with `buy()` and `sell()`

### [RSI Mean Reversion](rsi-mean-reversion.py)
- Counter-trend strategy using RSI
- Demonstrates indicator access patterns
- Shows conditional logic and position checking

### [Bollinger Band Strategy](bollinger-bands.py)
- Uses composite indicators (named tuple returns)
- Demonstrates accessing multiple indicator components
- Shows volatility-based trading logic

## Intermediate Examples

### [Multi-Indicator Confluence](multi-indicator-confluence.py)
- Combines multiple indicators for signal confirmation
- Demonstrates indicator caching and reuse
- Shows complex conditional logic

### [MACD with Volume Confirmation](macd-volume.py)
- Uses tuple-return indicators (MACD)
- Incorporates volume analysis
- Demonstrates array slicing and historical analysis

### [Stochastic Oscillator Strategy](stochastic-strategy.py)
- Uses dictionary-return indicators
- Shows overbought/oversold conditions
- Demonstrates key-based indicator access

## Advanced Examples

### [Time-Based Trading](time-based-trading.py)
- Incorporates time-of-day logic
- Uses datetime utilities for market hours
- Shows session-based trading patterns

### [Multi-Timeframe Analysis](multi-timeframe.py)
- Conceptual multi-timeframe approach
- Shows data alignment techniques
- Demonstrates complex indicator combinations

### [Custom Indicator Strategy](custom-indicator.py)
- Creates and uses custom composite indicators
- Shows advanced indicator patterns
- Demonstrates performance optimization

## Pattern Examples

### [Breakout Strategy](breakout-strategy.py)
- Range breakout detection
- Volume confirmation
- Dynamic stop-loss management

### [Trend Following with Filters](trend-following-filtered.py)
- Multiple trend confirmation methods
- Risk management techniques
- Parameter optimization examples

### [Mean Reversion with Momentum](mean-reversion-momentum.py)
- Combines mean reversion and momentum
- Shows indicator combination techniques
- Demonstrates risk-adjusted position sizing

## Testing and Debugging Examples

### [Strategy Debugging](debugging-example.py)
- Error handling patterns
- Debugging techniques
- Performance monitoring

### [Parameter Validation](parameter-validation.py)
- Comprehensive parameter checking
- Input validation patterns
- Error recovery strategies

## Usage

Each example is a complete, runnable strategy that demonstrates specific concepts and patterns. To use an example:

1. Copy the strategy file to your strategies directory
2. Import and run using your backtesting framework
3. Modify parameters and logic as needed

## Example Structure

All examples follow this consistent structure:

```python
from strategies.Base import Base
from indicators.vectorized import SMA, RSI  # Your indicator imports

class ExampleStrategy(Base):
    def init(self):
        """Initialize indicators and parameters."""
        # Indicator registration
        # Parameter setup
        pass
    
    def next(self):
        """Execute strategy logic for current bar."""
        # Entry conditions
        # Exit conditions
        # Position management
        pass
    
    def validate_params(self, **kwargs):
        """Validate strategy parameters."""
        # Parameter validation logic
        return True
    
    @staticmethod
    def get_optimization_params():
        """Define optimization parameter ranges."""
        return {
            'param1': (min_val, max_val),
            'param2': (min_val, max_val)
        }
```

## Learning Path

1. **Start with Basic Examples** - Understand the fundamental concepts
2. **Study Intermediate Examples** - Learn indicator combinations and patterns
3. **Explore Advanced Examples** - Master complex techniques and optimizations
4. **Review Pattern Examples** - See real-world trading strategies
5. **Check Testing Examples** - Learn debugging and validation techniques

Each example includes detailed comments explaining the logic, best practices, and potential improvements.
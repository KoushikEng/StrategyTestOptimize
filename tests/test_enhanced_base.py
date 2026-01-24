"""
Tests for the enhanced Base strategy class.
"""

import pytest
from hypothesis import given, strategies as st, assume
import numpy as np
from strategies.Base import Base, IndicatorWrapper
from Utilities import DataTuple


class SimpleTestStrategy(Base):
    """Simple test strategy for testing the enhanced Base class."""
    
    def __init__(self):
        super().__init__()
        self.sma_short = None
        self.sma_long = None
    
    def init(self):
        """Initialize indicators."""
        # Simple moving averages
        def sma(prices, period):
            result = np.convolve(prices, np.ones(period)/period, mode='same')
            # Fix the edges by using available data
            for i in range(min(period-1, len(prices))):
                if i == 0:
                    result[i] = prices[i]
                else:
                    result[i] = np.mean(prices[:i+1])
            return result
        
        closes = self.get_full_data_array('close')
        self.sma_short = self.I(sma, closes, 5)
        self.sma_long = self.I(sma, closes, 10)
    
    def next(self):
        """Process current bar."""
        # Simple crossover strategy
        if len(self) < 10:  # Need enough data for long SMA
            return
        
        if not self.position['in_position']:
            # Buy when short SMA crosses above long SMA
            if self.sma_short[-1] > self.sma_long[-1] and self.sma_short[-2] <= self.sma_long[-2]:
                self.buy()
        else:
            # Sell when short SMA crosses below long SMA
            if self.sma_short[-1] < self.sma_long[-1] and self.sma_short[-2] >= self.sma_long[-2]:
                self.sell()
    
    def __len__(self):
        """Return current data length."""
        return self._context.get_current_index() + 1
    
    def validate_params(self, **kwargs) -> bool:
        return True
    
    @staticmethod
    def get_optimization_params():
        return {"short_period": (3, 10), "long_period": (10, 30)}


class TestEnhancedBaseClass:
    """Tests for the enhanced Base class functionality."""
    
    def test_basic_strategy_execution(self):
        """Test basic strategy execution with init() and next() methods."""
        # Create test data
        data_length = 50
        symbol = "TEST"
        timestamps = np.arange(1600000000, 1600000000 + data_length, dtype=np.int64)
        
        # Create trending price data for crossover testing
        base_price = 100.0
        trend = np.linspace(0, 10, data_length)
        noise = np.random.normal(0, 0.5, data_length)
        closes = base_price + trend + noise
        
        opens = closes - 0.1
        highs = closes + 0.2
        lows = closes - 0.2
        volume = np.full(data_length, 1000, dtype=np.int64)
        
        data_tuple = (symbol, timestamps, opens, highs, lows, closes, volume)
        
        # Test strategy
        strategy = SimpleTestStrategy()
        results = strategy._execute_strategy(data_tuple)
        
        # Verify results structure
        assert isinstance(results.returns, np.ndarray)
        assert isinstance(results.equity_curve, np.ndarray)
        assert isinstance(results.win_rate, float)
        assert isinstance(results.total_trades, int)
        
        # Verify process() method compatibility
        returns, equity_curve, win_rate, total_trades = strategy.process(data_tuple)
        assert np.array_equal(returns, results.returns)
        assert np.array_equal(equity_curve, results.equity_curve)
        assert win_rate == results.win_rate
        assert total_trades == results.total_trades
    
    def test_indicator_registration_and_caching(self):
        """Test indicator registration and caching functionality."""
        # Create test data
        data_length = 20
        symbol = "TEST"
        timestamps = np.arange(1600000000, 1600000000 + data_length, dtype=np.int64)
        closes = np.arange(100, 100 + data_length, dtype=np.float64)
        opens = closes - 1
        highs = closes + 1
        lows = closes - 1
        volume = np.full(data_length, 1000, dtype=np.int64)
        
        data_tuple = (symbol, timestamps, opens, highs, lows, closes, volume)
        
        class IndicatorTestStrategy(Base):
            def init(self):
                def simple_sma(prices, period):
                    return np.convolve(prices, np.ones(period)/period, mode='same')
                
                closes = self.get_full_data_array('close')
                # Register same indicator twice - should be cached
                self.sma1 = self.I(simple_sma, closes, 5)
                self.sma2 = self.I(simple_sma, closes, 5)  # Same parameters, should be cached
                self.sma3 = self.I(simple_sma, closes, 10)  # Different parameters
            
            def next(self):
                pass
            
            def validate_params(self, **kwargs):
                return True
            
            @staticmethod
            def get_optimization_params():
                return {}
        
        strategy = IndicatorTestStrategy()
        strategy._execute_strategy(data_tuple)
        
        # Verify indicators are registered
        assert len(strategy._indicators) == 2  # Two unique indicators (period 5 and 10)
        assert isinstance(strategy.sma1, IndicatorWrapper)
        assert isinstance(strategy.sma2, IndicatorWrapper)
        assert isinstance(strategy.sma3, IndicatorWrapper)
        
        # Verify caching - same parameters should return same object
        assert strategy.sma1 is strategy.sma2
        assert strategy.sma1 is not strategy.sma3
    
    def test_position_management_integration(self):
        """Test position management integration with buy/sell methods."""
        # Create test data
        data_length = 10
        symbol = "TEST"
        timestamps = np.arange(1600000000, 1600000000 + data_length, dtype=np.int64)
        closes = np.array([100, 101, 102, 103, 104, 105, 106, 107, 108, 109], dtype=np.float64)
        opens = closes - 0.5
        highs = closes + 0.5
        lows = closes - 0.5
        volume = np.full(data_length, 1000, dtype=np.int64)
        
        data_tuple = (symbol, timestamps, opens, highs, lows, closes, volume)
        
        class PositionTestStrategy(Base):
            def init(self):
                pass
            
            def next(self):
                current_idx = self._context.get_current_index()
                
                if current_idx == 2 and not self.position['in_position']:
                    self.buy(1.0)  # Buy at index 2 (price 102)
                elif current_idx == 5 and self.position['in_position']:
                    self.sell()  # Sell at index 5 (price 105)
            
            def validate_params(self, **kwargs):
                return True
            
            @staticmethod
            def get_optimization_params():
                return {}
        
        strategy = PositionTestStrategy()
        results = strategy._execute_strategy(data_tuple)
        
        # Verify trade was executed
        assert results.total_trades == 1
        assert len(results.returns) == 1
        
        # Verify return calculation: (105 - 102) / 102 ≈ 0.0294
        expected_return = (105.0 - 102.0) / 102.0
        assert abs(results.returns[0] - expected_return) < 1e-6
    
    def test_error_handling(self):
        """Test error handling in the enhanced Base class."""
        
        class ErrorTestStrategy(Base):
            def init(self):
                pass
            
            def next(self):
                pass
            
            def validate_params(self, **kwargs):
                return True
            
            @staticmethod
            def get_optimization_params():
                return {}
        
        strategy = ErrorTestStrategy()
        
        # Test buy without data
        with pytest.raises(RuntimeError, match="Cannot execute trades before data is set"):
            strategy.buy()
        
        # Test sell without data
        with pytest.raises(RuntimeError, match="Cannot execute trades before data is set"):
            strategy.sell()
        
        # Test indicator registration without data
        with pytest.raises(RuntimeError, match="Cannot register indicators before data is set"):
            strategy.I(lambda x: x)
    
    def test_legacy_run_method_compatibility(self):
        """Test that the legacy run() method still works for backward compatibility."""
        # Create test data
        data_length = 20
        symbol = "TEST"
        timestamps = np.arange(1600000000, 1600000000 + data_length, dtype=np.int64)
        closes = np.linspace(100, 110, data_length)
        opens = closes - 0.5
        highs = closes + 0.5
        lows = closes - 0.5
        volume = np.full(data_length, 1000, dtype=np.int64)
        
        data_tuple = (symbol, timestamps, opens, highs, lows, closes, volume)
        
        strategy = SimpleTestStrategy()
        
        # Test legacy run() method
        bar_returns = strategy.run(data_tuple)
        
        # Should return array of returns per bar
        assert isinstance(bar_returns, np.ndarray)
        assert len(bar_returns) == data_length


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
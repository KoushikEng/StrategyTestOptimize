"""
Property-based tests for strategy execution order and return aggregation.
"""

import pytest
from hypothesis import given, strategies as st, assume
import numpy as np
from strategies.Base import Base
from Utilities import DataTuple


class ExecutionOrderTestStrategy(Base):
    """Test strategy for execution order testing."""
    
    def __init__(self):
        super().__init__()
        self.init_called = False
        self.next_calls = []
        self.bar_indices = []
    
    def init(self):
        """Track init() call."""
        self.init_called = True
    
    def next(self):
        """Track next() calls and current bar index."""
        current_idx = self._context.get_current_index()
        self.next_calls.append(current_idx)
        self.bar_indices.append(current_idx)
    
    def validate_params(self, **kwargs):
        return True
    
    @staticmethod
    def get_optimization_params():
        return {}


class TestStrategyExecutionOrder:
    """Property-based tests for strategy execution order."""
    
    @given(
        data_length=st.integers(min_value=10, max_value=100)
    )
    def test_strategy_execution_order_property(self, data_length):
        """
        **Feature: strategy-base-enhancement, Property 1: Strategy Execution Order**
        
        For any strategy and dataset, the execution engine should call init() exactly once 
        before processing any bars, then call next() exactly once for each bar in sequential order.
        
        **Validates: Requirements 1.3, 1.4, 8.3**
        """
        # Create test data
        symbol = "TEST"
        timestamps = np.arange(1600000000, 1600000000 + data_length, dtype=np.int64)
        closes = np.random.uniform(100, 200, data_length).astype(np.float64)
        opens = closes - np.random.uniform(0, 2, data_length)
        highs = closes + np.random.uniform(0, 3, data_length)
        lows = closes - np.random.uniform(0, 2, data_length)
        volume = np.random.randint(1000, 10000, data_length, dtype=np.int64)
        
        data_tuple = (symbol, timestamps, opens, highs, lows, closes, volume)
        
        strategy = ExecutionOrderTestStrategy()
        results = strategy._execute_strategy(data_tuple)
        
        # Property: init() should be called exactly once
        assert strategy.init_called, "init() should be called"
        
        # Property: next() should be called exactly once for each bar
        assert len(strategy.next_calls) == data_length, f"next() should be called {data_length} times, got {len(strategy.next_calls)}"
        
        # Property: next() should be called in sequential order (0, 1, 2, ..., data_length-1)
        expected_sequence = list(range(data_length))
        assert strategy.next_calls == expected_sequence, f"next() calls should be in order {expected_sequence}, got {strategy.next_calls}"
        
        # Property: Bar indices should be sequential
        assert strategy.bar_indices == expected_sequence, f"Bar indices should be sequential {expected_sequence}, got {strategy.bar_indices}"
    
    @given(
        data_length=st.integers(min_value=20, max_value=50),
        trade_bars=st.lists(st.integers(min_value=5, max_value=45), min_size=2, max_size=6)
    )
    def test_return_aggregation_consistency_property(self, data_length, trade_bars):
        """
        **Feature: strategy-base-enhancement, Property 8: Return Aggregation Consistency**
        
        For any strategy execution, the engine should collect all position returns and produce 
        output in the same format as the current process() method: (returns, equity_curve, win_rate, no_of_trades).
        
        **Validates: Requirements 8.4, 8.5**
        """
        # Filter and sort trade bars to ensure they're valid and unique
        unique_trade_bars = sorted(list(set([bar for bar in trade_bars if 1 <= bar < data_length - 1])))
        assume(len(unique_trade_bars) >= 2 and len(unique_trade_bars) % 2 == 0)  # Need even number for buy/sell pairs
        
        # Create test data with predictable prices for return calculation
        symbol = "TEST"
        timestamps = np.arange(1600000000, 1600000000 + data_length, dtype=np.int64)
        closes = np.linspace(100, 150, data_length).astype(np.float64)  # Predictable upward trend
        opens = closes - 0.5
        highs = closes + 1
        lows = closes - 1
        volume = np.full(data_length, 1000, dtype=np.int64)
        
        data_tuple = (symbol, timestamps, opens, highs, lows, closes, volume)
        
        class ReturnTestStrategy(Base):
            def __init__(self):
                super().__init__()
                self.trade_bars = unique_trade_bars
                self.trade_index = 0
                self.expected_returns = []
            
            def init(self):
                pass
            
            def next(self):
                current_idx = self._context.get_current_index()
                
                if self.trade_index < len(self.trade_bars):
                    if current_idx == self.trade_bars[self.trade_index]:
                        if not self.position['in_position']:
                            # Buy
                            entry_price = self.data.Close[-1]
                            self.buy(1.0)
                            self.entry_price = entry_price
                        else:
                            # Sell
                            exit_price = self.data.Close[-1]
                            expected_return = (exit_price - self.entry_price) / self.entry_price
                            self.expected_returns.append(expected_return)
                            self.sell()
                        
                        self.trade_index += 1
            
            def validate_params(self, **kwargs):
                return True
            
            @staticmethod
            def get_optimization_params():
                return {}
        
        strategy = ReturnTestStrategy()
        results = strategy._execute_strategy(data_tuple)
        
        # Property: Number of trades should match expected
        expected_trades = len(unique_trade_bars) // 2
        assert results.total_trades == expected_trades, f"Expected {expected_trades} trades, got {results.total_trades}"
        
        # Property: Returns array should have correct length
        assert len(results.returns) == expected_trades, f"Returns array should have {expected_trades} elements, got {len(results.returns)}"
        
        # Property: Returns should match expected calculations
        for i, (expected, actual) in enumerate(zip(strategy.expected_returns, results.returns)):
            assert abs(expected - actual) < 1e-10, f"Trade {i}: expected return {expected}, got {actual}"
        
        # Property: Equity curve should be cumulative product of (1 + returns)
        if expected_trades > 0:
            expected_equity = np.cumprod(1 + results.returns)
            np.testing.assert_array_almost_equal(results.equity_curve, expected_equity, decimal=10)
        
        # Property: Win rate should be calculated correctly
        if expected_trades > 0:
            expected_win_rate = np.sum(results.returns > 0) / expected_trades
            assert abs(results.win_rate - expected_win_rate) < 1e-10, f"Expected win rate {expected_win_rate}, got {results.win_rate}"
        else:
            assert results.win_rate == 0.0, "Win rate should be 0 when no trades"
        
        # Property: process() method should return same results
        # Create a new strategy instance for process() test to ensure independence
        strategy2 = ReturnTestStrategy()
        returns, equity_curve, win_rate, total_trades = strategy2.process(data_tuple)
        
        # The results should be the same since it's the same strategy logic
        assert len(returns) == len(results.returns), f"Process method returns length mismatch: {len(returns)} vs {len(results.returns)}"
        if len(returns) > 0:
            np.testing.assert_array_almost_equal(returns, results.returns, decimal=10)
            np.testing.assert_array_almost_equal(equity_curve, results.equity_curve, decimal=10)
        assert win_rate == results.win_rate
        assert total_trades == results.total_trades
    
    def test_execution_context_management(self):
        """Test that execution context is properly managed throughout strategy execution."""
        data_length = 30
        symbol = "TEST"
        timestamps = np.arange(1600000000, 1600000000 + data_length, dtype=np.int64)
        closes = np.arange(100, 130, dtype=np.float64)
        opens = closes - 1
        highs = closes + 1
        lows = closes - 1
        volume = np.full(data_length, 1000, dtype=np.int64)
        
        data_tuple = (symbol, timestamps, opens, highs, lows, closes, volume)
        
        class ContextTestStrategy(Base):
            def __init__(self):
                super().__init__()
                self.context_states = []
            
            def init(self):
                # During init, context should be at index 0
                self.init_context_index = self._context.get_current_index()
            
            def next(self):
                # Record context state during each next() call
                current_idx = self._context.get_current_index()
                data_length = self._context._data_length
                self.context_states.append({
                    'index': current_idx,
                    'data_length': data_length,
                    'close_price': self.data.Close[-1]
                })
            
            def validate_params(self, **kwargs):
                return True
            
            @staticmethod
            def get_optimization_params():
                return {}
        
        strategy = ContextTestStrategy()
        strategy._execute_strategy(data_tuple)
        
        # Property: Context should be properly initialized
        assert strategy.init_context_index == 0, f"Init context index should be 0, got {strategy.init_context_index}"
        
        # Property: Context should progress through all indices
        assert len(strategy.context_states) == data_length, f"Should have {data_length} context states, got {len(strategy.context_states)}"
        
        for i, state in enumerate(strategy.context_states):
            assert state['index'] == i, f"Context index at step {i} should be {i}, got {state['index']}"
            assert state['data_length'] == data_length, f"Data length should be {data_length}, got {state['data_length']}"
            assert state['close_price'] == closes[i], f"Close price at index {i} should be {closes[i]}, got {state['close_price']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
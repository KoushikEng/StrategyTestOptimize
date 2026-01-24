"""
Property-based tests for PositionManager state tracking.
"""

import pytest
from hypothesis import given, strategies as st, assume
import numpy as np
from strategies.Base import PositionManager, TradeRecord


class TestPositionManagerProperties:
    """Property-based tests for PositionManager."""
    
    @given(
        trades=st.lists(
            st.tuples(
                st.floats(min_value=1.0, max_value=1000.0),  # entry_price
                st.floats(min_value=1.0, max_value=1000.0),  # exit_price
                st.floats(min_value=0.1, max_value=10.0),    # position_size
                st.integers(min_value=0, max_value=1000),    # entry_index
                st.integers(min_value=1, max_value=1001)     # exit_index (must be > entry_index)
            ),
            min_size=1,
            max_size=50
        )
    )
    def test_position_state_tracking_property(self, trades):
        """
        **Feature: strategy-base-enhancement, Property 6: Position State Tracking**
        
        For any sequence of position operations, the Position_Manager should correctly 
        track position state, record entry/exit data, and calculate returns accurately.
        
        **Validates: Requirements 4.3, 4.4, 4.5**
        """
        manager = PositionManager()
        expected_returns = []
        
        for entry_price, exit_price, position_size, entry_index, exit_index in trades:
            # Ensure exit_index > entry_index
            if exit_index <= entry_index:
                exit_index = entry_index + 1
            
            # Property: Should start with no position
            assert not manager.is_in_position(), "Should start with no position"
            
            # Property: Opening position should update state correctly
            manager.open_position(entry_price, position_size, entry_index)
            assert manager.is_in_position(), "Should be in position after opening"
            
            position_info = manager.get_current_position_info()
            assert position_info['in_position'] == True
            assert position_info['position_size'] == position_size
            assert position_info['entry_price'] == entry_price
            assert position_info['entry_index'] == entry_index
            
            # Property: Closing position should calculate return correctly
            expected_return = (exit_price - entry_price) / entry_price
            actual_return = manager.close_position(exit_price, exit_index)
            
            assert abs(actual_return - expected_return) < 1e-10, f"Return calculation incorrect: expected {expected_return}, got {actual_return}"
            expected_returns.append(expected_return)
            
            # Property: Should not be in position after closing
            assert not manager.is_in_position(), "Should not be in position after closing"
            
            # Property: Trade should be recorded correctly
            assert manager.get_trade_count() == len(expected_returns), "Trade count should match number of completed trades"
        
        # Property: All returns should be recorded correctly
        recorded_returns = manager.get_trade_returns()
        assert len(recorded_returns) == len(expected_returns), "Number of recorded returns should match"
        
        for i, (expected, actual) in enumerate(zip(expected_returns, recorded_returns)):
            assert abs(expected - actual) < 1e-10, f"Trade {i} return mismatch: expected {expected}, got {actual}"
        
        # Property: Trade records should contain correct information
        for i, trade in enumerate(manager.trades):
            entry_price, exit_price, position_size, entry_index, exit_index = trades[i]
            if exit_index <= entry_index:
                exit_index = entry_index + 1
            
            assert trade.entry_price == entry_price
            assert trade.exit_price == exit_price
            assert trade.position_size == position_size
            assert trade.entry_index == entry_index
            assert trade.exit_index == exit_index
            assert abs(trade.return_pct - expected_returns[i]) < 1e-10
    
    @given(
        entry_price=st.floats(min_value=1.0, max_value=1000.0),
        position_size=st.floats(min_value=0.1, max_value=10.0),
        entry_index=st.integers(min_value=0, max_value=1000)
    )
    def test_position_state_consistency_property(self, entry_price, position_size, entry_index):
        """
        Property test for position state consistency throughout operations.
        """
        manager = PositionManager()
        
        # Property: Initial state should be consistent
        assert not manager.is_in_position()
        assert manager.position_size == 0.0
        assert manager.entry_price == 0.0
        assert manager.entry_index == -1
        assert manager.get_trade_count() == 0
        
        # Property: After opening position, state should be consistent
        manager.open_position(entry_price, position_size, entry_index)
        
        assert manager.is_in_position()
        assert manager.position_size == position_size
        assert manager.entry_price == entry_price
        assert manager.entry_index == entry_index
        
        position_info = manager.get_current_position_info()
        assert position_info['in_position'] == True
        assert position_info['position_size'] == position_size
        assert position_info['entry_price'] == entry_price
        assert position_info['entry_index'] == entry_index


class TestPositionManagerErrorConditions:
    """Unit tests for PositionManager error conditions."""
    
    def test_open_position_when_already_in_position(self):
        """Test opening position when already in position raises error."""
        manager = PositionManager()
        manager.open_position(100.0, 1.0, 0)
        
        with pytest.raises(ValueError, match="Already in position"):
            manager.open_position(110.0, 1.0, 1)
    
    def test_close_position_when_not_in_position(self):
        """Test closing position when not in position raises error."""
        manager = PositionManager()
        
        with pytest.raises(ValueError, match="No position to close"):
            manager.close_position(100.0, 1)
    
    def test_invalid_position_parameters(self):
        """Test invalid parameters for position operations."""
        manager = PositionManager()
        
        # Test invalid position size
        with pytest.raises(ValueError, match="Position size must be positive"):
            manager.open_position(100.0, 0.0, 0)
        
        with pytest.raises(ValueError, match="Position size must be positive"):
            manager.open_position(100.0, -1.0, 0)
        
        # Test invalid entry price
        with pytest.raises(ValueError, match="Entry price must be positive"):
            manager.open_position(0.0, 1.0, 0)
        
        with pytest.raises(ValueError, match="Entry price must be positive"):
            manager.open_position(-100.0, 1.0, 0)
        
        # Test invalid entry index
        with pytest.raises(ValueError, match="Entry index must be non-negative"):
            manager.open_position(100.0, 1.0, -1)
    
    def test_invalid_close_parameters(self):
        """Test invalid parameters for closing position."""
        manager = PositionManager()
        manager.open_position(100.0, 1.0, 5)
        
        # Test invalid exit price
        with pytest.raises(ValueError, match="Exit price must be positive"):
            manager.close_position(0.0, 10)
        
        with pytest.raises(ValueError, match="Exit price must be positive"):
            manager.close_position(-50.0, 10)
        
        # Test invalid exit index
        with pytest.raises(ValueError, match="Exit index must be non-negative"):
            manager.close_position(110.0, -1)
        
        # Test exit index before entry index
        with pytest.raises(ValueError, match="Exit index .* must be after entry index"):
            manager.close_position(110.0, 5)  # Same as entry index
        
        with pytest.raises(ValueError, match="Exit index .* must be after entry index"):
            manager.close_position(110.0, 3)  # Before entry index
    
    def test_return_calculation_accuracy(self):
        """Test that return calculations are accurate."""
        manager = PositionManager()
        
        # Test profitable trade
        manager.open_position(100.0, 1.0, 0)
        return_pct = manager.close_position(110.0, 1)
        expected = (110.0 - 100.0) / 100.0  # 10% gain
        assert abs(return_pct - expected) < 1e-10
        
        # Test losing trade
        manager.open_position(100.0, 1.0, 2)
        return_pct = manager.close_position(90.0, 3)
        expected = (90.0 - 100.0) / 100.0  # 10% loss
        assert abs(return_pct - expected) < 1e-10
        
        # Verify both trades are recorded
        assert manager.get_trade_count() == 2
        returns = manager.get_trade_returns()
        assert len(returns) == 2
        assert abs(returns[0] - 0.1) < 1e-10  # 10% gain
        assert abs(returns[1] - (-0.1)) < 1e-10  # 10% loss


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
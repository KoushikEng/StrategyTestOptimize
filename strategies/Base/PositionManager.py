from dataclasses import dataclass
import numpy as np


@dataclass
class TradeRecord:
    """Record of a completed trade."""
    entry_price: float
    exit_price: float
    entry_index: int
    exit_index: int
    return_pct: float
    position_size: float

class PositionManager:
    """Handles position tracking and trade execution."""
    
    def __init__(self):
        self.position_size = 0.0
        self.entry_price = 0.0
        self.entry_index = -1
        self.trades = []  # List of TradeRecord objects
    
    def open_position(self, price: float, size: float, index: int):
        """Open a new position."""
        if self.is_in_position():
            raise ValueError("Already in position. Close current position before opening new one.")
        
        if size <= 0:
            raise ValueError(f"Position size must be positive, got {size}")
        if price <= 0:
            raise ValueError(f"Entry price must be positive, got {price}")
        if index < 0:
            raise ValueError(f"Entry index must be non-negative, got {index}")
        
        self.position_size = size
        self.entry_price = price
        self.entry_index = index
    
    def close_position(self, price: float, index: int) -> float:
        """Close current position and return the trade return."""
        if not self.is_in_position():
            raise ValueError("No position to close")
        
        if price <= 0:
            raise ValueError(f"Exit price must be positive, got {price}")
        if index < 0:
            raise ValueError(f"Exit index must be non-negative, got {index}")
        if index <= self.entry_index:
            raise ValueError(f"Exit index {index} must be after entry index {self.entry_index}")
        
        # Calculate return percentage
        trade_return = (price - self.entry_price) / self.entry_price
        
        # Create trade record
        trade_record = TradeRecord(
            entry_price=self.entry_price,
            exit_price=price,
            entry_index=self.entry_index,
            exit_index=index,
            return_pct=trade_return,
            position_size=self.position_size
        )
        self.trades.append(trade_record)
        
        # Reset position state
        self.position_size = 0.0
        self.entry_price = 0.0
        self.entry_index = -1
        
        return trade_return
    
    def is_in_position(self) -> bool:
        """Check if currently in a position."""
        return self.position_size != 0.0
    
    def get_current_position_info(self) -> dict:
        """Get information about current position."""
        return {
            'in_position': self.is_in_position(),
            'position_size': self.position_size,
            'entry_price': self.entry_price,
            'entry_index': self.entry_index
        }
    
    def get_trade_returns(self) -> np.ndarray:
        """Get array of all trade returns."""
        return np.array([trade.return_pct for trade in self.trades])
    
    def get_trade_count(self) -> int:
        """Get total number of completed trades."""
        return len(self.trades)

"""
Strategy Specification Schema

Defines the JSON schema for representing trading strategies in a machine-readable format.
This is the "contract" between the Translator Agent and the Compiler.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any, Literal
from enum import Enum


class IndicatorType:
    """Supported indicator types (Standard Library).
    New types can be added dynamically as strings.
    """
    SMA = "sma"
    EMA = "ema"
    RSI = "rsi"
    MACD = "macd"
    BOLLINGER = "bollinger"
    ATR = "atr"
    STOCH = "stochastic"
    ADX = "adx"
    VWAP = "vwap"
    SUPERTREND = "supertrend"


class Indicator(BaseModel):
    """Definition of an indicator used in the strategy."""
    name: str = Field(..., description="Identifier for this indicator instance, e.g., 'fast_ema'")
    type: str = Field(..., description="Type of indicator (e.g. 'sma', 'keltner_channel')")
    params: Dict[str, Any] = Field(default_factory=dict, description="Indicator parameters, e.g., {'period': 14}")
    
    @field_validator('name')
    @classmethod
    def name_must_be_valid_identifier(cls, v: str) -> str:
        if not v.isidentifier():
            raise ValueError(f"Indicator name '{v}' must be a valid Python identifier")
        return v


class Condition(BaseModel):
    """A single condition for entry or exit."""
    expression: str = Field(..., description="Condition expression, e.g., 'fast_ema > slow_ema'")
    description: Optional[str] = Field(None, description="Human-readable description")
    position_type: Optional[Literal["long", "short"]] = Field(None, description="Specific position type for this condition (overrides strategy-level position_type)")


class RiskManagement(BaseModel):
    """Risk management rules."""
    stop_loss: Optional[str] = Field(None, description="Stop loss rule, e.g., '1.5 * atr' or '0.02' for 2%")
    take_profit: Optional[str] = Field(None, description="Take profit rule")
    trailing_stop: Optional[str] = Field(None, description="Trailing stop rule")
    max_position_size: Optional[float] = Field(None, description="Maximum position size as fraction of capital")


class StrategySpec(BaseModel):
    """
    Complete specification of a trading strategy.
    
    This is the core "language" that bridges natural language descriptions
    to executable Python code.
    """
    
    name: str = Field(..., description="Strategy name, must be valid Python class name")
    description: Optional[str] = Field(None, description="Strategy description")
    
    # Indicators
    indicators: List[Indicator] = Field(default_factory=list, description="List of indicators used")
    
    # Entry/Exit Logic
    entry_conditions: List[Condition] = Field(..., description="Conditions for entering a position (ALL must be true)")
    exit_conditions: List[Condition] = Field(..., description="Conditions for exiting a position (ANY can trigger)")
    
    # Position Type
    position_type: Literal["long", "short", "both"] = Field(default="long", description="Position type")
    
    # Risk Management
    risk_management: Optional[RiskManagement] = Field(None, description="Risk management rules")
    
    # Optimization Parameters (bounds for each tunable parameter)
    optimization_params: Dict[str, tuple] = Field(
        default_factory=dict, 
        description="Parameters to optimize with (min, max) bounds, e.g., {'period': (5, 50)}"
    )
    
    @field_validator('name')
    @classmethod
    def name_must_be_valid_class_name(cls, v: str) -> str:
        if not v.isidentifier() or not v[0].isupper():
            raise ValueError(f"Strategy name '{v}' must be a valid Python class name (PascalCase)")
        return v


# Example Usage / Testing
if __name__ == "__main__":
    # Example: RSI Mean Reversion Strategy
    example_spec = StrategySpec(
        name="RsiMeanReversion",
        description="Buy when RSI is oversold, sell when overbought",
        indicators=[
            Indicator(name="rsi", type=IndicatorType.RSI, params={"period": 14})
        ],
        entry_conditions=[
            Condition(expression="rsi < 30", description="RSI oversold")
        ],
        exit_conditions=[
            Condition(expression="rsi > 70", description="RSI overbought")
        ],
        position_type="long",
        optimization_params={
            "rsi_period": (7, 21),
            "oversold_threshold": (20, 35),
            "overbought_threshold": (65, 80)
        }
    )
    
    print("Example Strategy Spec:")
    print(example_spec.model_dump_json(indent=2))

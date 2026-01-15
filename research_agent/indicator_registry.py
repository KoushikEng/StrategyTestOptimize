"""
Indicator Signature Registry

Central source-of-truth for indicator function signatures.
The Compiler uses this to generate correct argument lists.
The Librarian appends new entries when creating indicators.
"""

from collections import namedtuple

# Signature describes how to call an indicator function
# - args: list of positional argument names (e.g., ["closes"] or ["highs", "lows", "closes"])
# - defaults: dict of parameter names to default values (e.g., {"period": 14})
Signature = namedtuple("Signature", ["args", "defaults"])

# Built-in indicator signatures
# Key = indicator type (matches StrategySpec.indicators[].type)
# Value = Signature(args, defaults)
INDICATOR_SIGNATURES = {
    # ---- Primitives (core.py) ----
    "sma": Signature(args=["closes"], defaults={"period": 14}),
    "ema": Signature(args=["closes"], defaults={"period": 14}),
    "atr": Signature(args=["highs", "lows", "closes"], defaults={"period": 14}),
    "rsi": Signature(args=["closes"], defaults={"period": 14}),

    # ---- Trend (trend.py) ----
    "adx": Signature(args=["highs", "lows", "closes"], defaults={"period": 14}),
    "supertrend": Signature(args=["highs", "lows", "closes"], defaults={"period": 10, "multiplier": 3.0}),
    "ichimoku": Signature(args=["highs", "lows", "closes"], defaults={}),

    # ---- Momentum (momentum.py) ----
    "macd": Signature(args=["closes"], defaults={"fast": 12, "slow": 26, "signal": 9}),

    # ---- Volatility (volatility.py) ----
    "bollinger": Signature(args=["closes"], defaults={"period": 20, "std_dev": 2.0}),

    # ---- Volume (volume.py) ----
    "vwap": Signature(args=["highs", "lows", "closes", "volume"], defaults={}),
}


def register_indicator(name: str, args: list[str], defaults: dict) -> None:
    """
    Register a new indicator signature.
    Called by the Librarian after generating indicator code.
    """
    INDICATOR_SIGNATURES[name] = Signature(args=args, defaults=defaults)


def get_signature(name: str) -> Signature | None:
    """
    Get the signature for an indicator by name.
    Returns None if not found.
    """
    return INDICATOR_SIGNATURES.get(name)

"""
Indicator Signature Registry

Central source-of-truth for indicator function signatures.
Signatures are loaded from source files on startup (persistent).
The Librarian writes SIGNATURE comments in source files.
"""

import re
from collections import namedtuple
from pathlib import Path
from typing import Dict

# Signature describes how to call an indicator function
# - args: list of positional argument names (e.g., ["closes"] or ["highs", "lows", "closes"])
# - defaults: dict of parameter names to default values (e.g., {"period": 14})
Signature = namedtuple("Signature", ["args", "defaults"])

# Registry dict - populated on first access
# Key = indicator type (matches StrategySpec.indicators[].type)
# Value = Signature(args, defaults)
_INDICATOR_SIGNATURES: Dict[str, Signature] = {}
_loaded = False

# Path to indicator source files
INDICATORS_DIR = Path(__file__).parent.parent / "calculate" / "indicators"

# Fallback signatures for built-in indicators (in case comments are missing)
_BUILTIN_SIGNATURES = {
    "sma": Signature(args=["closes"], defaults={"period": 14}),
    "ema": Signature(args=["closes"], defaults={"period": 14}),
    "atr": Signature(args=["highs", "lows", "closes"], defaults={"period": 14}),
    "rsi": Signature(args=["closes"], defaults={"period": 14}),
    "adx": Signature(args=["highs", "lows", "closes"], defaults={"period": 14}),
    "supertrend": Signature(args=["highs", "lows", "closes"], defaults={"period": 10, "multiplier": 3.0}),
    "ichimoku": Signature(args=["highs", "lows", "closes"], defaults={}),
    "macd": Signature(args=["closes"], defaults={"fast": 12, "slow": 26, "signal": 9}),
    "bollinger_bands": Signature(args=["closes"], defaults={"period": 20, "num_std": 2.0}),
    "vwap": Signature(args=["highs", "lows", "closes", "volume"], defaults={}),
}


def _load_signatures_from_files() -> None:
    """
    Scan indicator source files and extract SIGNATURE comments.
    Expected format (right after def line):
        def calculate_xxx(...):
            # SIGNATURE: args=["closes"] defaults={"period": 14}
    """
    global _INDICATOR_SIGNATURES, _loaded
    
    # Start with builtins as fallback
    _INDICATOR_SIGNATURES = dict(_BUILTIN_SIGNATURES)
    
    if not INDICATORS_DIR.exists():
        print(f"[Registry] Indicators directory not found: {INDICATORS_DIR}")
        _loaded = True
        return
    
    # Pattern to match function definition followed by signature comment
    # Matches: def calculate_NAME(...):
    #              # SIGNATURE: args=[...] defaults={...}
    pattern = re.compile(
        r'def\s+calculate_(\w+)\s*\([^)]*\).*?:\s*\n'
        r'\s*#\s*SIGNATURE:\s*args=(\[.*?\])\s*defaults=(\{.*?\})',
        re.MULTILINE
    )
    
    for py_file in INDICATORS_DIR.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
            
        try:
            content = py_file.read_text(encoding="utf-8")
            
            for match in pattern.finditer(content):
                name = match.group(1)
                try:
                    args = eval(match.group(2))
                    defaults = eval(match.group(3))
                    _INDICATOR_SIGNATURES[name] = Signature(args=args, defaults=defaults)
                except Exception as e:
                    print(f"[Registry] Failed to parse signature for '{name}': {e}")
                    
        except Exception as e:
            print(f"[Registry] Error reading {py_file}: {e}")
    
    _loaded = True
    print(f"[Registry] Loaded {len(_INDICATOR_SIGNATURES)} signatures")


def _ensure_loaded() -> None:
    """Ensure signatures are loaded from files."""
    global _loaded
    if not _loaded:
        _load_signatures_from_files()


def register_indicator(name: str, args: list[str], defaults: dict) -> None:
    """
    Register a new indicator signature (runtime only).
    The Librarian should write SIGNATURE comment to source file for persistence.
    """
    _ensure_loaded()
    _INDICATOR_SIGNATURES[name] = Signature(args=args, defaults=defaults)


def get_signature(name: str) -> Signature | None:
    """
    Get the signature for an indicator by name.
    Returns None if not found.
    """
    _ensure_loaded()
    return _INDICATOR_SIGNATURES.get(name)


def refresh_registry() -> None:
    """Force re-scan of source files."""
    global _loaded
    _loaded = False
    _ensure_loaded()


def list_signatures() -> dict[str, Signature]:
    """Return all registered signatures (for debugging)."""
    _ensure_loaded()
    return dict(_INDICATOR_SIGNATURES)

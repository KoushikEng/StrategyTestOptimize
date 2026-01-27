"""
Indicator registration and import management.
"""

import sys
import importlib
from typing import List, Set, Optional
from research_agent.schema import Indicator
from .exceptions import IndicatorNotFoundError


class IndicatorManager:
    """Manages indicator imports and registrations."""
    
    def __init__(self):
        self.indicators_package = "calculate.indicators"
    
    def get_indicator_function_name(self, indicator_type: str) -> str:
        """Get the function name for an indicator type."""
        func_name = f"calculate_{indicator_type}"
        
        if self._try_import_indicator(func_name):
            return func_name
        
        # Try to invoke Librarian if indicator not found
        print(f"⚠️ Indicator '{indicator_type}' not found. Invoking Librarian...")
        try:
            add_indicator_func = self._get_librarian()
            if add_indicator_func:
                new_category = add_indicator_func(indicator_type)
                if new_category and self._try_import_indicator(func_name, new_category):
                    print(f"✅ New indicator function '{func_name}' added successfully")
                    return func_name
            else:
                print("❌ Librarian not available")
        except Exception as e:
            print(f"❌ Librarian error: {e}")
        
        raise IndicatorNotFoundError(indicator_type)
    
    def _try_import_indicator(self, func_name: str, new_category: Optional[str] = None) -> bool:
        """Try to import an indicator function."""
        try:
            if new_category and self.indicators_package in sys.modules:
                # Reload modules if new category was added
                submod = f"{self.indicators_package}.{new_category}"
                if submod in sys.modules:
                    importlib.reload(sys.modules[submod])
                importlib.reload(sys.modules[self.indicators_package])
            else:
                importlib.import_module(self.indicators_package)
            
            module = sys.modules[self.indicators_package]
            return hasattr(module, func_name)
        except ImportError as e:
            print(f"[compiler] ImportError: {e}")
            return False
    
    def _get_librarian(self):
        """Lazy import of librarian to avoid LLM initialization during testing."""
        try:
            from research_agent.librarian import add_indicator
            return add_indicator
        except Exception as e:
            print(f"Warning: Could not import librarian: {e}")
            return None
    
    def generate_imports(self, indicators: List[Indicator]) -> str:
        """Generate import statements for indicators."""
        if not indicators:
            return ""
        
        needed_funcs = set()
        for indicator in indicators:
            func_name = self.get_indicator_function_name(indicator.type)
            needed_funcs.add(func_name)
        
        if needed_funcs:
            return f"from calculate.indicators import {', '.join(sorted(needed_funcs))}"
        
        return ""
    
    def generate_registrations(self, indicators: List[Indicator]) -> str:
        """Generate indicator registration calls using self.I() pattern."""
        if not indicators:
            return ""
        
        lines = []
        
        for indicator in indicators:
            func_name = self.get_indicator_function_name(indicator.type)
            args = self._build_indicator_args(indicator, func_name)
            lines.append(f"        self.{indicator.name} = self.I({func_name}, {args})")
        
        return "\n".join(lines)
    
    def _build_indicator_args(self, indicator: Indicator, func_name: str) -> str:
        """Build arguments for indicator registration."""
        try:
            from research_agent.indicator_registry import get_signature
            sig = get_signature(indicator.type)
            
            if sig:
                arg_parts = []
                
                # Add data sources based on signature
                for arg in sig.args:
                    if arg == 'closes':
                        arg_parts.append('self.data.Close')
                    elif arg == 'opens':
                        arg_parts.append('self.data.Open')
                    elif arg == 'highs':
                        arg_parts.append('self.data.High')
                    elif arg == 'lows':
                        arg_parts.append('self.data.Low')
                    elif arg == 'volume':
                        arg_parts.append('self.data.Volume')
                    else:
                        arg_parts.append(arg)
                
                # Add parameters with defaults
                for param_name, default_value in sig.defaults.items():
                    value = indicator.params.get(param_name, default_value)
                    arg_parts.append(f"{param_name}={value}")
                
                return ", ".join(arg_parts)
            else:
                # Fallback for unregistered indicators
                print(f"⚠️ No signature found for '{indicator.type}', using generic fallback")
                if 'period' in indicator.params:
                    return f"self.data.Close, period={indicator.params['period']}"
                else:
                    return "self.data.Close"
                    
        except ImportError:
            # Fallback if indicator_registry is not available
            if 'period' in indicator.params:
                return f"self.data.Close, period={indicator.params['period']}"
            else:
                return "self.data.Close"
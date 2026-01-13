import sys
import importlib


try:
    # Reload to capture new additions
    if "calculate.indicators" in sys.modules:
        importlib.reload(sys.modules["calculate.indicators"])
    else:
        importlib.import_module("calculate.indicators")
        
    module = sys.modules["calculate.indicators"]
    print(f"module: {module}, 'calculate_keltner_channel': {hasattr(module, 'calculate_keltner_channel')}")
except ImportError:
    print("Module not found")

import sys
import importlib

PACKAGE_NAME = "calculate.indicators"

SUBMODULE_TO_ADD = "core"

def try_import(func):
    try:
        modules = [mod for mod in sys.modules.keys() if mod.startswith(PACKAGE_NAME)]
        print("\nModules:", modules, end="\n\n")
        # Reload to capture new additions
        if PACKAGE_NAME in sys.modules:
            print(f"Reloading {PACKAGE_NAME} package")

            # importlib.reload(sys.modules[PACKAGE_NAME])  # This will not work, because it will try to import the new function from submodules before reloading them
            
            mod = f"{PACKAGE_NAME}.{SUBMODULE_TO_ADD}"
            if mod in sys.modules:
                print(f"First reloading submodule: {mod}")
                importlib.reload(sys.modules[mod])

            print(f"At last reloading package (the main module): {PACKAGE_NAME}")
            importlib.reload(sys.modules[PACKAGE_NAME])
        else:
            print(f"Importing {PACKAGE_NAME} package")
            importlib.import_module(PACKAGE_NAME)
            
        module = sys.modules[PACKAGE_NAME]
        print(f"'{func}' in {module.__name__}: {hasattr(module, func)}")
    except ImportError as e:
        print(e)

def add_indicator():
    try:
        from research_agent.tools import write_file
        write_file(f"calculate/indicators/{SUBMODULE_TO_ADD}.py", """
def calculate_new_ind():
    return 1
""", 'a')
        print(f"\nIndicator added to {SUBMODULE_TO_ADD}.py")
        write_file(f"calculate/indicators/__init__.py", f"""\nfrom .{SUBMODULE_TO_ADD} import calculate_new_ind\n""", 'a')
        print("Indicator added to __init__.py")
    except Exception as e:
        print(f"Error adding indicator: {e}")

if __name__ == "__main__":
    try_import("calculate_new_ind")
    add_indicator()
    try_import("calculate_new_ind")

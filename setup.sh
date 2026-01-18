#!/bin/bash

echo "=== StrategyTestOptimize Setup Script ==="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
major_version=$(echo $python_version | cut -d. -f1)
minor_version=$(echo $python_version | cut -d. -f2)

if [ "$major_version" -lt 3 ] || ([ "$major_version" -eq 3 ] && [ "$minor_version" -lt 9 ]); then
    echo "❌ ERROR: Python version $python_version detected. Python 3.9+ is required."
    echo "Please upgrade Python and try again."
    exit 1
fi

echo "✅ Python version $python_version is compatible"
echo ""

# Check if pygmo is installed
echo "Checking for PyGmo installation..."
python -c "import pygmo" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ ERROR: PyGmo is not installed!"
    echo ""
    echo "PyGmo is required for optimization algorithms."
    echo "💡 HINT: If you haven't activated the conda environment, try:"
    echo "   conda activate pygmo_env"
    echo "   then run this setup script again."
    echo ""
    echo "If PyGmo is not installed in your environment, install it with:"
    echo "   conda install -c conda-forge pygmo"
    exit 1
fi

echo "✅ PyGmo is installed and available"
echo ""

# Install tvdatafeed from GitHub
echo "Installing tvdatafeed from GitHub repository..."
pip install --upgrade --no-cache-dir git+https://github.com/koushikeng/tvdatafeed.git
if [ $? -ne 0 ]; then
    echo "❌ ERROR: Failed to install tvdatafeed"
    exit 1
fi

echo "✅ tvdatafeed installed successfully"
echo ""

# Install requirements from requirements.txt
echo "Installing Python dependencies from requirements.txt..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ ERROR: Failed to install requirements from requirements.txt"
    exit 1
fi

echo "✅ All Python dependencies installed successfully"
echo ""

# Verify critical imports
echo "Verifying critical package imports..."
python -c "
import sys
packages = ['numpy', 'numba', 'pygmo', 'langchain_core', 'langgraph', 'pydantic']
failed = []

for pkg in packages:
    try:
        __import__(pkg)
        print(f'✅ {pkg}')
    except ImportError:
        print(f'❌ {pkg}')
        failed.append(pkg)

if failed:
    print(f'\\n❌ Failed to import: {failed}')
    sys.exit(1)
else:
    print('\\n✅ All critical packages verified successfully')
"

if [ $? -ne 0 ]; then
    echo "❌ Package verification failed"
    exit 1
fi

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Set up your API keys in research_agent/.env:"
echo "   - OPENROUTER_API_KEY"
echo ""
echo "2. Test the installation:"
echo "   python main.py --help"
echo ""
echo "3. Generate your first strategy:"
echo "   python -m research_agent.master \"Buy when RSI < 30\" --symbol SBIN --interval 15"
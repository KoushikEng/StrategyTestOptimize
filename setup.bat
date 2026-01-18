@echo off
echo === StrategyTestOptimize Setup Script ===
echo.

REM Check Python version
echo Checking Python version...
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set python_version=%%i
echo Python version: %python_version%

REM Extract major and minor version numbers
for /f "tokens=1,2 delims=." %%a in ("%python_version%") do (
    set major_version=%%a
    set minor_version=%%b
)

REM Check if version is 3.9+
if %major_version% LSS 3 (
    echo ❌ ERROR: Python version %python_version% detected. Python 3.9+ is required.
    echo Please upgrade Python and try again.
    pause
    exit /b 1
)

if %major_version% EQU 3 if %minor_version% LSS 9 (
    echo ❌ ERROR: Python version %python_version% detected. Python 3.9+ is required.
    echo Please upgrade Python and try again.
    pause
    exit /b 1
)

echo ✅ Python version %python_version% is compatible
echo.

REM Check if pygmo is installed
echo Checking for PyGmo installation...
python -c "import pygmo" 2>nul
if errorlevel 1 (
    echo ❌ ERROR: PyGmo is not installed!
    echo.
    echo PyGmo is required for optimization algorithms.
    echo 💡 HINT: If you haven't activated the conda environment, try:
    echo    conda activate pygmo_env
    echo    then run this setup script again.
    echo.
    echo If PyGmo is not installed in your environment, install it with:
    echo    conda install -c conda-forge pygmo
    pause
    exit /b 1
)

echo ✅ PyGmo is installed and available
echo.

REM Install tvdatafeed from GitHub
echo Installing tvdatafeed from GitHub repository...
pip install --upgrade --no-cache-dir git+https://github.com/koushikeng/tvdatafeed.git
if errorlevel 1 (
    echo ❌ ERROR: Failed to install tvdatafeed
    pause
    exit /b 1
)

echo ✅ tvdatafeed installed successfully
echo.

REM Install requirements from requirements.txt
echo Installing Python dependencies from requirements.txt...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ ERROR: Failed to install requirements from requirements.txt
    pause
    exit /b 1
)

echo ✅ All Python dependencies installed successfully
echo.

REM Verify critical imports
echo Verifying critical package imports...
python -c "import sys; packages = ['numpy', 'numba', 'pygmo', 'langchain_core', 'langgraph', 'pydantic']; failed = []; [print(f'✅ {pkg}') if not failed.append(pkg) and __import__(pkg) else print(f'❌ {pkg}') for pkg in packages]; print(f'\n❌ Failed to import: {failed}') if failed else print('\n✅ All critical packages verified successfully'); sys.exit(1) if failed else None"

if errorlevel 1 (
    echo ❌ Package verification failed
    pause
    exit /b 1
)

echo.
echo 🎉 Setup completed successfully!
echo.
echo Next steps:
echo 1. Set up your API keys in research_agent\.env:
echo    - OPENROUTER_API_KEY
echo.
echo 2. Test the installation:
echo    python main.py --help
echo.
echo 3. Generate your first strategy:
echo    python -m research_agent.master "Buy when RSI < 30" --symbol SBIN --interval 15
echo.
pause
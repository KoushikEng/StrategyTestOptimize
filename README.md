# StrategyTestOptimize

**A Closed-Loop AI Research Agent System for Trading Strategies.**

This project allows you to autonomously generate, backtest, and optimize trading strategies using LLMs (Large Language Models) and a high-performance deterministic engine.

## Key Features

1.  **AI Research Agent**: Generates trading strategies from plain English descriptions (e.g., "Create a mean reversion strategy using RSI").
2.  **Deterministic Engine**: Fast backtesting using `numpy` and `numba` (no hallucinated results).
3.  **Robust Optimization**: Uses **PyGmo** (Differential Evolution) for Walk-Forward Analysis to find stable parameters.
4.  **Self-Correction**: The AI Agent ("Repair Node") automatically fixes code errors and improves strategies rejected by quality checks.
5.  **Quality Gates**: A hostile "Reviewer" agent rejects strategies with poor metrics (e.g., too few trades, overfitting).

## Installation

1.  **Prerequisites**:
    -   Anaconda or Miniconda installed.
    -   An API Key for **Google Gemini** (`GOOGLE_API_KEY`) or **OpenAI** (`OPENAI_API_KEY`).

2.  **Environment Setup**:
    The project relies on a specific Conda environment named `pygmo_env`.

    ```bash
    # Create and activate the environment (assuming requirements are handled manually or via existing env)
    # If starting from scratch, you'd typically need: python=3.9 numpy pandas numba pygmo
    conda activate pygmo_env
    
    # Install Python dependencies
    pip install langgraph langchain langchain-google-genai langchain-openai prettytable tvdatafeed
    ```

3.  **Set API Keys**:
    ```bash
    # Windows PowerShell
    $env:GOOGLE_API_KEY="your-api-key-here"
    ```

## Usage

### 1. The Research Agent (Recommended)
Let the AI build the strategy for you.

```bash
# Syntax: python -m research_agent.master "Your strategy description" [options]

python -m research_agent.master "Buy when RSI < 30 and Close > EMA(200). Sell when RSI > 70." --symbol SBIN --interval 15 --download --optimize
```

-   `--symbol`: The stock symbol to test (e.g., SBIN, RELIANCE).
-   `--interval`: Timeframe (e.g., 5, 15, 1H, 1D).
-   `--download`: Downloads historical data if missing.
-   `--optimize`: Runs parameter optimization if the strategy passes review.

### 2. Manual Backtesting
Run a specific strategy file located in `strategies/`.

```bash
python main.py SBIN --strategy RsiMeanReversion --interval 15
```

### 3. Manual Optimization
Tune parameters for an existing strategy using robust Walk-Forward Analysis.

```bash
python optimize.py SBIN --strategy RsiMeanReversion --interval 15 --pop 40 --gen 50
```

### 4. API Usage (Python)
Use the system as a library in your own scripts.

```python
from main import run_backtest
from optimize import run_optimization

# Backtest
results = run_backtest(
    symbols=['SBIN'], 
    strategy_name='RsiMeanReversion', 
    interval='15'
)

# Optimize
best_params = run_optimization(
    symbol='SBIN', 
    strategy_name='RsiMeanReversion', 
    interval='15'
)
```

## Project Structure

-   `research_agent/`: The AI Agents (Translator, Compiler, Reviewer, Repair).
-   `strategies/`: Folder where generated strategy Python files are saved.
-   `data/`: Historical CSV data storage.
-   `AGENTS_readme.md`: detailed internal documentation for developers/agents.

## License
MIT

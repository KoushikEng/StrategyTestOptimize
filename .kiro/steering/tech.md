# Technology Stack

## Core Dependencies
- **Python 3.9+** (Conda environment: `pygmo_env`)
- **NumPy/Numba**: High-performance numerical computing and JIT compilation
- **PyGmo**: Differential Evolution optimization algorithms
- **LangGraph**: AI agent orchestration and workflow management
- **LangChain**: LLM integration (Google Gemini, OpenAI)

## Required Environment Setup
```bash
# Activate the specific Conda environment
conda activate pygmo_env

# Install Python dependencies
pip install langgraph langchain langchain-google-genai langchain-openai prettytable tvdatafeed
```

## API Keys Required
- `GOOGLE_API_KEY` for Google Gemini
- `OPENAI_API_KEY` for OpenAI (alternative)

## Common Commands

### Research Agent (Recommended)
```bash
# Generate strategy from description
python -m research_agent.master "Buy when RSI < 30 and Close > EMA(200). Sell when RSI > 70." --symbol SBIN --interval 15 --download --optimize
```

### Manual Backtesting
```bash
# Test existing strategy
python main.py SBIN --strategy RsiMeanReversion --interval 15

# With custom parameters
python main.py SBIN --strategy MyStrategy --interval 15 --kwargs "param1:int=20,param2:float=0.5"
```

### Optimization
```bash
# Optimize strategy parameters
python optimize.py SBIN --strategy RsiMeanReversion --interval 15 --pop 40 --gen 50
```

### Data Management
```bash
# Download historical data
python main.py --download --interval 15
```

## Architecture Principles
- **Deterministic Execution**: Core engine operates without LLMs for reproducible results
- **Schema-Driven**: LLMs output structured JSON, not direct Python code
- **Sandboxed Compilation**: JSON specs are compiled to Python via templates
- **Multi-processing**: Parallel execution for backtesting multiple symbols
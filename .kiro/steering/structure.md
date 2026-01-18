# Project Structure

## Directory Organization

### Core Execution Layer (Deterministic)
- **`main.py`**: Primary backtesting engine and CLI entry point
- **`optimize.py`**: Parameter optimization using PyGmo differential evolution
- **`Utilities.py`**: Data loading, interval parsing, and utility functions
- **`config.py`**: Global configuration (exchange, timezone)

### AI Research Layer (Agentic)
- **`research_agent/`**: Complete AI agent system
  - `master.py`: CLI orchestrator and main entry point
  - `graph.py`: LangGraph workflow definition
  - `state.py`: Shared state management across agents
  - `translator.py`: Natural language → JSON spec conversion
  - `compiler.py`: JSON spec → Python code generation (deterministic)
  - `reviewer.py`: Quality gatekeeper with strict rejection criteria
  - `repair.py`: Self-healing agent for error correction
  - `optimizer.py`: Wrapper around core optimization engine
  - `schema.py`: Pydantic models for strategy specifications

### Strategy Implementation
- **`strategies/`**: Generated and manual strategy files
  - `Base.py`: Abstract base class defining strategy interface
  - Generated files follow naming convention: `{StrategyName}.py`

### Technical Indicators & Calculations
- **`calculate/`**: Numerical computation modules
  - `indicators/`: Technical indicator implementations (Numba-optimized)
  - `risk_metrics.py`: Sharpe, Sortino, drawdown calculations

### Data & Testing
- **`data/{interval}/`**: Historical CSV data organized by timeframe
- **`tests/`**: Unit tests for indicators and core functionality

### Workflow Documentation
- **`.agent/workflows/`**: Agent-specific workflow guides
- **`AGENTS_readme.md`**: Comprehensive developer documentation for AI agents

## File Naming Conventions
- Strategy classes: PascalCase (e.g., `RsiMeanReversion`)
- Python modules: snake_case
- Data files: `{SYMBOL}.csv` in interval-specific directories
- Generated strategies: Match class name exactly

## Key Interfaces
- All strategies must inherit from `Base` class
- Required methods: `run()`, `validate_params()`, `get_optimization_params()`
- Data format: Standardized tuple structure from `Utilities.read_from_csv()`

## Import Patterns
- Core engine imports from root level
- Research agents use relative imports within `research_agent/`
- Strategy files import from `calculate/` for indicators
- Cross-layer communication via standardized interfaces only
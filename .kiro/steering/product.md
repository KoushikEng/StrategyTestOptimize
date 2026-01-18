---
inclusion: always
---

# Product Overview

**StrategyTestOptimize** is a closed-loop AI research agent system for autonomous trading strategy research and evaluation.

## Core Purpose
Generate, backtest, and optimize trading strategies using LLMs with a deterministic execution engine. The system takes plain English descriptions (e.g., "Create a mean reversion strategy using RSI, buy when RSI > 30 and sell when below") and produces fully tested, optimized Python trading strategies.

## Architecture Principles

### Separation of Concerns
- **AI Layer**: Natural language processing and strategy generation (research_agent/)
- **Deterministic Layer**: Mathematical computations and backtesting (main.py, calculate/)
- **Never mix LLM operations with numerical calculations**

### Data Flow Pattern
1. Natural language → JSON specification (via LLMs)
2. JSON specification → Python code (via deterministic templates)
3. Python code → Backtesting results (via numpy/numba)
4. Results → Optimization (via PyGmo)

## Key Components

### AI Research Agent (`research_agent/`)
- Converts natural language to structured JSON specifications
- Uses LangGraph for workflow orchestration
- Implements self-correction and quality gates
- **Never generates Python code directly** - only JSON specs

### Deterministic Engine
- Fast backtesting using numpy/numba (no hallucinated results)
- All strategies inherit from `Base` class in `strategies/Base.py`
- Standardized data format from `Utilities.read_from_csv()`

### Quality Assurance
- Hostile reviewer agent rejects poor strategies
- Automated error detection and repair
- Walk-Forward Analysis prevents overfitting

## Development Guidelines

### When Working with Strategies
- All new strategies must inherit from `strategies.Base`
- Implement required methods: `run()`, `validate_params()`, `get_optimization_params()`
- Use technical indicators from `calculate/indicators/`
- Follow PascalCase naming (e.g., `RsiMeanReversion`)

### When Working with Indicators
- Add new indicators to appropriate module in `calculate/indicators/`
- Use Numba decorators for performance optimization
- Follow existing patterns for parameter validation

### When Working with Research Agents
- Modify JSON schemas in `research_agent/schema.py`
- Update templates in `research_agent/compiler.py`
- Test changes through `research_agent/master.py` CLI

## Testing Strategy
- Unit tests for all indicators in `tests/`
- Integration tests via actual backtesting
- Quality gates prevent deployment of untested strategies

## Performance Requirements
- Backtesting must be deterministic and reproducible
- Optimization should leverage multiprocessing
- Memory efficiency for large datasets (15-minute intervals)
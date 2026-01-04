# Copilot instructions for StrategyTestOptimize

Purpose: help an AI coding agent become productive quickly in this repo (Python backtests and optimizer).

- **Big picture**: This repository implements an intraday breakout backtesting engine and a parameter optimizer.
  - Data ingestion and storage: historical 5-minute CSVs are stored under hist\5min\ as files named SYMBOL_5min.csv and produced by Utilities.hist_download.
  - Strategy logic: [First15minBreak.py](First15minBreak.py) contains the core `run(*args, **kwargs)` backtest for one symbol and returns (symbol, returns_array, win_pct).
  - Performance primitives: [numba_calculations.py](numba_calculations.py) contains @njit functions used by strategies; prefer editing these for speed-sensitive changes.
  - Vectorized alternatives: [vectorized_calculations.py](vectorized_calculations.py) has NumPy-vectorized versions used for prototyping or non-numba runs.
  - Orchestration & UI: [main.py](main.py) reads symbols (via `Utilities.read_from_csv`), uses ThreadPool/Pool to run `First15minBreak.run` in parallel, and prints a PrettyTable of results.
  - Optimization: [optimize.py](optimize.py) wraps the strategy in a pygmo NSGA-II problem with walk-forward and Monte‑Carlo robustness checks.

- **Key integration points & external deps**
  - tvDatafeed: used in `Utilities.hist_download` to fetch historical bars. Requires local credentials and network access.
  - pygmo: used for multi-objective optimization in `optimize.py`.
  - numba: many functions are compiled with @njit — changes to signatures or Python-only code in those functions must be numba-compatible.
  - Output: per-symbol debugging output is written to results/{symbol}_debug.txt and tables printed to stdout by `main.py`.

- **Project-specific conventions / patterns**
  - Data shapes: functions expect NumPy arrays (dates, times, opens, highs, lows, closes, volume). `Utilities.read_from_csv` returns (symbol, dates, times, opens, highs, lows, closes, volume).
  - Time-windowing: strategies group by unique dates (np.unique(dates)) and use index masks; assume 75 candles/day (5-minute intraday) in some code paths.
  - Parameter passing: experiment parameters are passed as kwargs (e.g., `sl_multi`, `tp_multi`, `ema`, `ema_slope`); `optimize.py` builds dictionaries via get_params_dict(params).
  - Performance split: compute-heavy math lives in Numba functions (edit here for speed). Use vectorized_calculations for simpler, readable alternatives.
  - Debug flags: `DEBUG = True` in strategies writes verbose per-day logs to results; many functions accept `trail` or parameter flags via kwargs.

- **How to run / developer workflows (observed in code)**
  - Backtest a list of default symbols (example):
    - python main.py
  - Backtest a single symbol:
    - python main.py SBIN
  - Download fresh data (creates hist\5min\SYMBOL_5min.csv):
    - python main.py --download
  - Pass tuning params via key=value pairs (examples):
    - python main.py SBIN sl_multi=1.6 tp_multi=3.0 ema=20 trail=T
  - Run optimizer (uses pygmo):
    - python optimize.py SBIN

- **Editing guidance for AI agents**
  - Prefer local, surgical edits. Changing a numba @njit function requires keeping Numba-safe types and avoiding Python stdlib constructs that Numba doesn't support.
  - When adding new parameters, ensure they are read from kwargs consistently in [First15minBreak.py](First15minBreak.py) and propagated to `optimize.py`'s `get_params_dict`.
  - Keep I/O confined to `Utilities.py` and `results/` to avoid scattering file-format logic.
  - For performance investigations, compare behavior between numba_calculations (compiled) and vectorized_calculations (numpy) before sweeping changes.

- **Files to inspect for related changes**
  - [Utilities.py](Utilities.py) — CSV schema and hist download
  - [First15minBreak.py](First15minBreak.py) — strategy run() and trade logic
  - [numba_calculations.py](numba_calculations.py) — performance-critical indicators
  - [optimize.py](optimize.py) — how parameters are optimized and evaluated
  - [main.py](main.py) — process orchestration, use of Pool/ThreadPool, CLI interface

- **Common pitfalls observed**
  - File paths use Windows-style separators (hist\5min\). Normalize carefully if adding cross-platform code.
  - Many functions assume no missing data — validate CSV reading when adding robustness fixes.
  - Numba functions return numpy arrays with NaNs in front; downstream code sometimes indexes expecting valid numeric values — preserve array lengths.

Please review this draft and tell me which parts need more detail (examples, line-level references, or policy for editing numba code). I will iterate based on your feedback.

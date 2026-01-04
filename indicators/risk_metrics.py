from numpy.typing import NDArray
from numba import njit
import numpy as np

RISK_FREE_RATE = 0.07 # Risk free rate for Indian market

# --- Risk Metrics Calculation ---
@njit
def calculate_sharpe(returns: NDArray, risk_free_rate: float = RISK_FREE_RATE) -> float:
    excess_returns = returns - risk_free_rate
    if len(excess_returns) < 2 and np.std(excess_returns) == 0:
        return 0.0
    return np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)

@njit
def calculate_sortino(returns: NDArray, risk_free_rate: float = RISK_FREE_RATE) -> float:
    excess_returns = returns - risk_free_rate
    downside_returns = excess_returns[excess_returns < 0]
    if len(downside_returns) == 0 or np.std(downside_returns) == 0:
        return 0.0
    return np.mean(excess_returns) / np.std(downside_returns) * np.sqrt(252)

def calculate_max_drawdown(returns: NDArray) -> float:
    if len(returns) == 0:
        return 0.0
        
    cumulative = np.cumprod(1 + returns)
    peak = np.maximum.accumulate(cumulative)
    drawdown = (cumulative - peak) / peak
    return np.min(drawdown) if len(drawdown) > 0 else 0.0
from typing import Any, Dict, List, Tuple, TypeAlias
import pygmo as pg
from First15minBreak import run
import numpy as np
import argparse
import time
from Utilities import read_from_csv
from ConsoleAnimator import ConsoleAnimator
from numba import njit
from numpy.typing import NDArray

parser = argparse.ArgumentParser()
parser.add_argument('symbol', type=str)
parser.add_argument('--trail', action='store_true')
args = parser.parse_args()

anim = ConsoleAnimator()

RISK_FREE_RATE = 0.07

DataTuple: TypeAlias = Tuple[str, NDArray, NDArray, NDArray, NDArray, NDArray, NDArray, NDArray]

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

def walk_forward_split(data: DataTuple, train_size=3375, test_size=375):
    for start in range(0, len(data[1]) - train_size - test_size + 1, test_size):
        train = [data[0], *[np.array(d[start:start+train_size]) for d in data[1:]]]
        test = [data[0], *[np.array(d[start+train_size:start+train_size+test_size]) for d in data[1:]]]
        yield train, test


def nearest_multiple(n, multiple):
    return round(n/multiple) * multiple

def get_data_split(data: DataTuple, split=0.3):
    start = nearest_multiple(len(data[1])*split, 75)
    return [data[0], *[np.array(d[-start:]) for d in data[1:]]]

def get_params_dict(params: List[float]):
    if args.trail:
        sl_multi, tp_multi, ema, ema_slope, atr, avg_vol, vol_multi, trail_multi = params
    else:
        sl_multi, tp_multi, ema, ema_slope, atr, avg_vol, vol_multi = params
    
    params_dict = {"ema": ema, "ema_slope": ema_slope, "atr": atr, "avg_vol": avg_vol, "vol_multi": vol_multi, "sl_multi": sl_multi, "tp_multi": tp_multi}
    return params_dict.update({"trail_multi": trail_multi, "trail": True}) if args.trail else params_dict 

# --- Modified BreakoutProblem for NSGA-II ---
class RobustBreakoutProblem:
    def __init__(self, data: DataTuple):
        self.data = data
        
    def evaluate_single_run(self, params: List[float]):
        return run(*self.data, **get_params_dict(params))

    def fitness(self, params: List[float]) -> List[float]:
        _, returns, win_pct = self.evaluate_single_run(params)
        sl_multi = params[0]
        tp_multi = params[1]
        
        # New objectives: Maximize Sharpe, Sortino, Win%, Minimize Drawdown
        sharpe = calculate_sharpe(returns)
        sortino = calculate_sortino(returns)
        drawdown = calculate_max_drawdown(returns)
        sharpe = calculate_sharpe(returns)
        if abs(sharpe) > 100:  # Impossible in reality
            print("KILLER PARAMS:", params)
            return [1e6, 1e6, 1e6, 1e6, 1e6, 1e6]  # Force NSGA-II to reject
        
        return [-sharpe, -sortino, -win_pct, drawdown, sl_multi, -tp_multi]  # Pygmo minimizes

    def get_bounds(self) -> Tuple[List[float], List[float]]:
        # sl_multi, tp_multi, ema, ema_slope, atr, avg_vol, vol_multi, trail_multi
        
        return ([0.7, 1.3, 9, 9, 9, 9, 1.3] + ([0.4] if args.trail else []), 
                [3.0, 3.5, 35, 35, 35, 35, 2.5] + ([2.0] if args.trail else []))

    def get_nobj(self) -> int:
        return 6  # Sharpe, Sortino, Win%, Drawdown, sl_multi, tp_multi

# --- Main Optimization Flow ---
def optimize_single_period(data: DataTuple) -> List:
    prob = pg.problem(RobustBreakoutProblem(data))
    algo = pg.algorithm(pg.nsga2(gen=300))
    # algo.set_verbosity(1)
    pop = pg.population(prob, size=120)
    pop = algo.evolve(pop)
    
    # Select solution with highest Sharpe (first objective)
    # pareto_f = pop.get_f()
    # best_idx = np.argmax([-f[0] for f in pareto_f])  # Index of max Sharpe
    return pop.get_x()

# --- Walk-Forward Analysis ---
def walk_forward_optimize(data: DataTuple, train_size: int = 3000, test_size: int = 750) -> Tuple[List[Dict], NDArray]:
    results = []
    for train_data, test_data in walk_forward_split(data, train_size, test_size):
        # Optimize on train_data
        pareto_x = optimize_single_period(train_data)
        
        for params in pareto_x:
            # Test on OOS
            _, oos_returns, _ = RobustBreakoutProblem(test_data).evaluate_single_run(params)
            oos_sharpe = calculate_sharpe(oos_returns)
            oos_sortino = calculate_sortino(oos_returns)
            oos_drawdown = calculate_max_drawdown(oos_returns)

            results.append({
                "params": params,
                "oos_sharpe": oos_sharpe,
                "oos_sortino": oos_sortino,
                "drawdown": oos_drawdown,
            })

    return results

def perturb_params(params: List[float], noise=0.1) -> List[float]:
    # Perturb params by ±10%
    return [p * np.random.uniform(1 - noise, 1 + noise) for p in params]

# --- Monte Carlo Parametric Robustness Check ---
def monte_carlo_test(data: DataTuple, base_params: List[float], base_sharpe: float, n_simulations: int = 100) -> Dict:
    sharpe_results = []
    sharpe_drops = []
    baseline_sharpe = base_sharpe
    
    for _ in range(n_simulations):
        # Perturb params by ±10%
        perturbed_params = perturb_params(base_params)
        _, returns, _ = RobustBreakoutProblem(data).evaluate_single_run(perturbed_params)
        sharpe = calculate_sharpe(returns)
        sharpe_results.append(sharpe)
        sharpe_drops.append((baseline_sharpe - sharpe) / baseline_sharpe)

    return {
        "mean_sharpe": np.mean(sharpe_results),
        "std_sharpe": np.std(sharpe_results),
        "worst_sharpe": np.min(sharpe_results),
        "best_sharpe": np.max(sharpe_results),
        "sharpe_drops": sharpe_drops
    }

# --- Monte Carlo Filtering ---
def select_robust_params(wfa_results: List[Dict], 
                         data: DataTuple,
                         top_n: int = 20,
                         n_simulations: int = 100) -> List[float]:
    """
    Steps:
    1. Take top `top_n` params by OOS Sharpe.
    2. Perturb each and test stability.
    3. Return the param set with the least performance drop.
    """
    # Sort by OOS Sharpe (descending)
    top_candidates = sorted(wfa_results, key=lambda x: -x["oos_sharpe"])[:top_n]
    
    best_param = None
    best_sharpe_results = None
    best_avg_sharpe = -np.inf
    
    for candidate in top_candidates:
        param = candidate["params"]
        sharpe = candidate["oos_sharpe"]
        sharpe_results = monte_carlo_test(data, param, sharpe, n_simulations)
        
        # Score = Avg Sharpe after perturbation
        avg_sharpe = sharpe_results["mean_sharpe"]
        if avg_sharpe > best_avg_sharpe:
            best_avg_sharpe = avg_sharpe
            best_param = param
            best_sharpe_results = sharpe_results
    
    return best_param, best_sharpe_results

if __name__ == "__main__":
    SYMBOL = args.symbol.upper()
    data = read_from_csv(SYMBOL)
    
    t1 = time.time()
    
    # --- Stage 1: Walk-Forward Optimization ---
    print("Running Walk-Forward Optimization...")
    wfa_results = walk_forward_optimize(data)
    oos_sharpes = [s["oos_sharpe"] for s in wfa_results]
    oos_sharpes_mean = np.mean(oos_sharpes)
    oos_sharpes_std = np.std(oos_sharpes)
    
    # Viability Check 1: OOS Sharpe Consistency
    if oos_sharpes_mean < 1.0:
        print("\n❌ REJECTED: OOS Sharpe Mean =", oos_sharpes_mean, " < 1.0 ", 
              "(Strategy is overfit)")
        exit()
    else:
        print(f"\n✅ OOS Sharpe Mean = {oos_sharpes_mean:.2f} (±{oos_sharpes_std:.2f})")
    
    # --- Stage 2: Monte Carlo Robustness Filter ---
    print("\nSelecting Robust Params via Monte Carlo...")
    robust_params, robust_sharpe_results = select_robust_params(wfa_results, data)
    sharpe_drops = robust_sharpe_results["sharpe_drops"]
    mean_sharpe_drops = np.mean(sharpe_drops)
    std_sharpe_drops = np.std(sharpe_drops)
    print(f"Robust Sharpe: {robust_sharpe_results['mean_sharpe']} ±{robust_sharpe_results['std_sharpe']}, Best: {robust_sharpe_results['best_sharpe']}, Worst: {robust_sharpe_results['worst_sharpe']}")
    
    # Viability Check 2: Parametric Fragility
    if mean_sharpe_drops > 0.3:
        print(f"\n❌ REJECTED: Sharpe drops by {mean_sharpe_drops*100:.0f}% on average when params perturbed")
        exit()
    else:
        print(f"\n✅ Parametric Stability: Sharpe drops by {mean_sharpe_drops*100:.0f}% (±{std_sharpe_drops*100:.0f}%)")
    
    # --- Stage 3: Final Validation on Unseen Data ---
    test_data = get_data_split(data)  # Last 30% of data
    _, returns, _ = RobustBreakoutProblem(test_data).evaluate_single_run(robust_params)
    sharpe = calculate_sharpe(returns)
    
    # Viability Check 3: Live Simulation
    if sharpe < 1.5:
        print(f"\n❌ REJECTED: Final Test Sharpe = {sharpe:.2f} (Unreliable for live trading)")
    else:
        print(f"\n✅ FINAL APPROVAL: Test Sharpe = {sharpe:.2f}")
        print(f"\n🔥 Robust Params:", get_params_dict(robust_params))

    # --- Strategy Viability Check ---
    # if oos_sharpes_mean < 1.0 or mc_results['worst_sharpe'] < 0.5:
    #     print("\n⚠️ WARNING: Strategy fails robustness checks!")
    # else:
    #     print("\n✅ Strategy passes basic robustness tests.")
    
    round_params_string = lambda params: [f"{k}={np.round(v, 1) if k.endswith('_multi') else int(np.round(v))}" for k, v in params.items()]
    
    print("Test run: python main.py", SYMBOL, *round_params_string(get_params_dict(robust_params)))
    
    t2 = time.time()
    
    print(f"Time taken: {t2-t1:.2f}s")

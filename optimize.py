
from typing import Dict, List, Tuple, Any
import pygmo as pg
import numpy as np
import argparse
import time
from Utilities import read_from_csv, DataTuple, get_strategy
from indicators.risk_metrics import calculate_sharpe, calculate_sortino, calculate_max_drawdown

parser = argparse.ArgumentParser(description="Optimize the strategy")
parser.add_argument('symbol', type=str, help="Symbol to optimize")
parser.add_argument('--strategy', '-S', type=str, required=True, help="Strategy to optimize")
parser.add_argument('--pop', type=int, default=40, help="Population size")
parser.add_argument('--gen', type=int, default=50, help="Generations")
args = parser.parse_args()

def walk_forward_split(data: DataTuple, train_size=3375, test_size=375):
    """Yields train, test sets."""
    for start in range(0, len(data[1]) - train_size - test_size + 1, test_size):
        train = [data[0], *[np.array(d[start:start+train_size]) for d in data[1:]]]
        test = [data[0], *[np.array(d[start+train_size:start+train_size+test_size]) for d in data[1:]]]
        yield train, test

def get_data_split(data: DataTuple, split=0.3):
    start = int(len(data[1]) * split)  # percent split
    # Ensure divisible by something sensible if needed, or just take slice
    return [data[0], *[np.array(d[-start:]) for d in data[1:]]]

class StrategyOptimizationProblem:
    def __init__(self, data: DataTuple, strategy_class: Any, bounds: Tuple[List[float], List[float]], param_names: List[str]):
        self.data = data
        self.strategy = strategy_class()
        self.bounds = bounds
        self.param_names = param_names
        
    def get_params_kwargs(self, params: List[float]) -> Dict[str, Any]:
        return dict(zip(self.param_names, params))

    def fitness(self, params: List[float]) -> List[float]:
        kwargs = self.get_params_kwargs(params)
        try:
            _, returns, win_pct = self.strategy.run(self.data, **kwargs)
        except Exception:
            return [1e6, 1e6, 1e6] # Punishment

        sharpe = calculate_sharpe(returns)
        drawdown = calculate_max_drawdown(returns)
        
        # Objective: Maximize Sharpe, Maximize Win Rate, Minimize Drawdown
        # Pygmo minimizes, so we negate Sharpe and Win Rate
        
        # Penalties
        if len(returns) < 10: # Too few trades
            return [1e6, 1e6, 1e6]
            
        return [-sharpe, -win_pct, drawdown]

    def get_bounds(self) -> Tuple[List[float], List[float]]:
        return self.bounds

    def get_nobj(self) -> int:
        return 3

def optimize_single_period(problem) -> Tuple[List[float], List[float]]:
    prob = pg.problem(problem)
    algo = pg.algorithm(pg.nsga2(gen=args.gen))
    pop = pg.population(prob, size=args.pop)
    pop = algo.evolve(pop)
    return pop.get_x(), pop.get_f()

def walk_forward_optimize(data: DataTuple, strategy_class, bounds, param_names) -> List[Dict]:
    results = []
    # Adjust train/test size based on data length if needed
    total_len = len(data[1])
    train_size = int(total_len * 0.6)
    test_size = int(total_len * 0.15)
    
    if train_size < 100 or test_size < 20:
        # Fallback for small data
        train_size = int(total_len * 0.7)
        test_size = int(total_len * 0.2)
        
    
    print(f"WFA: Train={train_size}, Test={test_size}")

    for train_data, test_data in walk_forward_split(data, train_size, test_size):
        problem = StrategyOptimizationProblem(train_data, strategy_class, bounds, param_names)
        pareto_x, pareto_f = optimize_single_period(problem)
        
        # Validate on Test
        test_problem = StrategyOptimizationProblem(test_data, strategy_class, bounds, param_names)
        
        for params in pareto_x:
            # We just want metrics here
            fit = test_problem.fitness(params)
            # fit is [-sharpe, -win_pct, drawdown]
            
            results.append({
                "params": params,
                "oos_sharpe": -fit[0],
                "win_pct": -fit[1],
                "drawdown": fit[2]
            })
            
    return results

if __name__ == "__main__":
    if not args.strategy:
        print("Strategy is required.")
        exit()
        
    SYMBOL = args.symbol.upper()
    try:
        data = read_from_csv(SYMBOL, "./data/5/")
    except Exception as e:
        print(f"Error reading data for {SYMBOL}: {e}")
        # Try default path assumption from previous code if needed or just fail
        exit()

    strategy_module = get_strategy(args.strategy)
    StrategyClass = getattr(strategy_module, args.strategy)
    
    # Check if strategy has optimization definition
    if hasattr(StrategyClass, 'get_optimization_params'):
        # Expected format: {"param_name": (min, max), ...}
        opt_params = StrategyClass.get_optimization_params()
        param_names = list(opt_params.keys())
        lower_bounds = [v[0] for v in opt_params.values()]
        upper_bounds = [v[1] for v in opt_params.values()]
        bounds = (lower_bounds, upper_bounds)
    else:
        print(f"Strategy {args.strategy} does not define 'get_optimization_params'.")
        print("Please add a static method 'get_optimization_params' returning dict {'param': (min, max)}")
        exit()

    print("Running Walk-Forward Optimization...")
    wfa_results = walk_forward_optimize(data, StrategyClass, bounds, param_names)
    
    if not wfa_results:
        print("No results generated.")
        exit()

    # Simple selection: Best OOS Sharpe
    best_result = sorted(wfa_results, key=lambda x: x['oos_sharpe'], reverse=True)[0]
    
    print("\nBest Robust Parameters Found:")
    print("-" * 30)
    best_params_dict = dict(zip(param_names, best_result['params']))
    print(best_params_dict)
    print(f"OOS Sharpe: {best_result['oos_sharpe']:.2f}")
    print(f"Win Rate: {best_result['win_pct']*100:.2f}%")
    print(f"Max DD: {best_result['drawdown']*100:.2f}%")
    
    print("\nCmd to run:")
    param_str = " ".join([f"--{k} {v}" for k,v in best_params_dict.items()]) # This assumes main.py takes args exactly like this, which currently it doesn't support generic args well
    # Current main.py doesn't accept dynamic args easily via CLI yet without work. 
    # But we print the dict for user to use.


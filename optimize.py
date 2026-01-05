from typing import Dict, List, Tuple, Any, Type
import pygmo as pg
import numpy as np
import argparse
from multiprocessing import cpu_count
from Utilities import read_from_csv, DataTuple, get_strategy, get_interval
from indicators.risk_metrics import calculate_sharpe, calculate_sortino, calculate_max_drawdown
from strategies.Base import Base

parser = argparse.ArgumentParser(description="Optimize the strategy")
parser.add_argument('symbol', type=str, help="Symbol to optimize")
parser.add_argument('--strategy', '-S', type=str, required=True, help="Strategy to optimize")
parser.add_argument('--pop', type=int, default=80, help="Population size per island")
parser.add_argument('--gen', type=int, default=200, help="Generations")
parser.add_argument('--interval', '-I', type=str, default='5', help='Interval (1, 5, 15, 1H, 1D, etc.)')
args = parser.parse_args()

def walk_forward_split(data: DataTuple, train_size=1500, test_size=200):
    """Yields train, test sets."""
    n = len(data[1])
    end = n - (n % test_size)
    for start in range(0, end, test_size):
        train_end = start+train_size
        test_end = train_end+test_size
        train = [data[0], *[np.array(d[0:train_end]) for d in data[1:]]]
        test = [data[0], *[np.array(d[train_end:test_end]) for d in data[1:]]]
        yield train, test

def get_data_split(data: DataTuple, split=0.3):
    start = int(len(data[1]) * split)  # percent split
    # Ensure divisible by something sensible if needed, or just take slice
    return [data[0], *[np.array(d[-start:]) for d in data[1:]]]

class StrategyOptimizationProblem:
    def __init__(self, data: DataTuple, strategy_class: Type[Base], bounds: Tuple[List[float], List[float]], param_names: List[str]):
        self.data = data
        self.strategy = strategy_class()
        self.bounds = bounds
        self.param_names = param_names
        self.n_obj = 1 # Single objective
        
    def get_params_kwargs(self, params: List[float]) -> Dict[str, Any]:
        return dict(zip(self.param_names, params))

    def evaluate(self, params: List[float]) -> Tuple[np.ndarray, np.ndarray, float, int]:
        # returns, equity_curve, win_rate, no_of_trades
        kwargs = self.get_params_kwargs(params)
        
        # Check constraints
        if not self.strategy.validate_params(**kwargs):
            return (np.array([0.0]), np.array([1.0]), 0.0, 0)
            
        try:
            return self.strategy.process(self.data, **kwargs)
        except Exception:
            return (np.array([0.0]), np.array([1.0]), 0.0, 0)

    def fitness(self, params: List[float]) -> List[float]:
        # returns, equity_curve, win_rate, no_of_trades
        returns, _, _, _ = self.evaluate(params)
        
        # Use Trade-based metrics for optimization stability
        trades = returns[returns != 0]
        
        # Penalties
        if len(trades) < 2: # Too few trades
            return [1e6]
            
        sharpe = calculate_sharpe(trades, risk_free_rate=0.0, scaling_factor=1.0) # Trade Sharpe
        # Drawdown can be incorporated as penalty or constraint if needed, but for now just Sharpe
        
        return [-sharpe]

    def get_bounds(self) -> Tuple[List[float], List[float]]:
        return self.bounds

    def get_nobj(self) -> int:
        return self.n_obj

def optimize_single_period(problem) -> Tuple[List[float], List[float]]:
    # DE1220 Algorithm
    algo = pg.algorithm(pg.de1220(gen=args.gen))
    
    # Island Model (Parallelism)
    island_count = cpu_count()
    prob = pg.problem(problem)
    
    # Create Archipelago
    archi = pg.archipelago(n=island_count, algo=algo, prob=prob, pop_size=args.pop)
    archi.evolve()
    archi.wait_check()
    
    # Single objective: Champions are the best found from each island
    return archi.get_champions_x(), archi.get_champions_f()

def walk_forward_optimize(data: DataTuple, strategy_class: Type[Base], bounds, param_names) -> List[Dict]:
    results = []
    total_len = len(data[1])
    train_size = int(total_len * 0.4)
    test_size = int(total_len * 0.1)
    
    if train_size < 100 or test_size < 20:
        train_size = int(total_len * 0.6)
        test_size = int(total_len * 0.2)
        
    print(f"WFA: Train={train_size}, Test={test_size}, Algo=de1220")

    for train_data, test_data in walk_forward_split(data, train_size, test_size):
        problem = StrategyOptimizationProblem(train_data, strategy_class, bounds, param_names)
        pareto_x, _ = optimize_single_period(problem)
        
        # Validate on Test
        test_problem = StrategyOptimizationProblem(test_data, strategy_class, bounds, param_names)
        
        for params in pareto_x:
            # Re-run to get full metrics
            returns, _, win_pct, _ = test_problem.evaluate(params)
            trades = returns[returns != 0]
            
            if len(trades) < 2:
                # print(f"Skipping result: Too few trades ({len(trades)})")
                # print(f"Skipping result: Too few trades ({len(trades)}). Params: {params}")
                continue
                
            sharpe = calculate_sharpe(trades, risk_free_rate=0.0, scaling_factor=1.0)
            drawdown = calculate_max_drawdown(returns)
            
            res = {
                "params": params,
                "oos_sharpe": sharpe,
                "win_pct": win_pct,
                "drawdown": drawdown
            }
            results.append(res)
            
    return results

if __name__ == "__main__":
    if not args.strategy:
        print("Strategy is required.")
        exit()
        
    SYMBOL = args.symbol.upper()
    interval_enum = get_interval(args.interval)
    data_path = f"./data/{interval_enum.value}/"
    
    # Read data first
    try:
        data = read_from_csv(SYMBOL, data_path)
    except Exception as e:
        print(f"Error reading data for {SYMBOL} from {data_path}: {e}")
        # Try default path assumption from previous code if needed or just fail
        exit()

    # Get strategy class
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
    
    # print("\nCmd to run:")
    # param_str = " ".join([f"--{k} {v}" for k,v in best_params_dict.items()]) # This assumes main.py takes args exactly like this, which currently it doesn't support generic args well
    # Current main.py doesn't accept dynamic args easily via CLI yet without work. 
    # But we print the dict for user to use.


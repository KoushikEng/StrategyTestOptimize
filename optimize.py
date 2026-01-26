from typing import Dict, List, Tuple, Any, Type
import pygmo as pg
import numpy as np
import argparse
from multiprocessing import cpu_count
from Utilities import read_from_csv, DataTuple, get_strategy, get_interval
from indicators.risk_metrics import calculate_sharpe, calculate_sortino, calculate_max_drawdown
from strategies.Base import Base

def walk_forward_split(data: DataTuple, train_size=1500, test_size=200):
    """Yields train, test sets.
    progressively increses the training set size and moves forward the test set.
    """
    n = len(data[1])
    end = n - train_size - (n % test_size)
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

def calculate_robust_score(sortino: np.float32, drawdown: np.float32, total_return: np.float32) -> np.float32:
    """Calculate the robust score for a strategy."""
    
    return sortino * (1.0 + drawdown) * np.log1p(1.0 + abs(total_return))

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
            return self.strategy.run(self.data, **kwargs)
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
            
        sharpe = calculate_sharpe(trades) # Trade Sharpe
        sortino = calculate_sortino(trades)
        drawdown = calculate_max_drawdown(returns) # Max DD from equity curve perspective (using full returns)
        total_return = np.sum(returns)
        
        # Robust Score Calculation
        
        # Check for NaN/Inf
        if np.isnan(sharpe) or np.isnan(sortino):
            return [1e6]

        # Composite score
        score = calculate_robust_score(sortino, drawdown, total_return)
        
        # Invert for minimization
        return [-score]

    def get_bounds(self) -> Tuple[List[float], List[float]]:
        return self.bounds

    def get_nobj(self) -> int:
        return self.n_obj

def optimize_single_period(problem, pop=40, gen=50) -> Tuple[List[float], List[float]]:
    # DE1220 Algorithm
    algo = pg.algorithm(pg.de1220(gen=gen))
    
    # Island Model (Parallelism)
    island_count = cpu_count()
    prob = pg.problem(problem)
    
    # Create Archipelago
    archi = pg.archipelago(n=island_count, algo=algo, prob=prob, pop_size=pop)
    archi.evolve()
    archi.wait_check()
    
    # Single objective: Champions are the best found from each island
    return archi.get_champions_x(), archi.get_champions_f()

def walk_forward_optimize(data: DataTuple, strategy_class: Type[Base], bounds, param_names, pop=40, gen=50) -> List[Dict]:
    results = []
    total_len = len(data[1])
    train_size = int(total_len * 0.4)
    test_size = int(total_len * 0.2)
    
    if train_size < 100 or test_size < 20:
        train_size = int(total_len * 0.6)
        test_size = int(total_len * 0.2)
        
    print(f"WFA: Train={train_size}, Test={test_size}, Algo=de1220")

    for train_data, test_data in walk_forward_split(data, train_size, test_size):
        problem = StrategyOptimizationProblem(train_data, strategy_class, bounds, param_names)
        pareto_x, _ = optimize_single_period(problem, pop=pop, gen=gen)
        
        # Validate on Test
        test_problem = StrategyOptimizationProblem(test_data, strategy_class, bounds, param_names)
        
        for params in pareto_x:
            # Re-run to get full metrics
            returns, _, win_pct, _ = test_problem.evaluate(params)
            trades = returns[returns != 0]
            
            if len(trades) < 2:
                continue
                
            sharpe = calculate_sharpe(trades)
            sortino = calculate_sortino(trades)
            drawdown = calculate_max_drawdown(returns)
            total_return = np.sum(returns)
            
            # Recalculate robust score for sorting
            robust_score = calculate_robust_score(sortino, drawdown, total_return)

            res = {
                "params": params,
                "oos_sharpe": sharpe,
                "oos_sortino": sortino,
                "total_return": total_return,
                "win_pct": win_pct,
                "drawdown": drawdown,
                "robust_score": robust_score
            }
            results.append(res)
            
    return results

def run_optimization(symbol: str, strategy_name: str, interval: str = '5', pop: int = 80, gen: int = 200) -> List[Dict]:
    """
    Run optimization for a strategy on a specific symbol.
    
    Args:
        symbol (str): Symbol to optimize.
        strategy_name (str): Name of the strategy class.
        interval (str, optional): Data interval. Defaults to '5'.
        pop (int, optional): Population size. Defaults to 80.
        gen (int, optional): Generations. Defaults to 200.
        
    Returns:
        List[Dict]: List of optimization results from WFA.
    """
    
    SYMBOL = symbol.upper()
    from Utilities import get_interval # import here to avoid circular or early import issues if any
    interval_enum = get_interval(interval)
    data_path = f"./data/{interval_enum.value}/"
    
    # Read data
    try:
        data = read_from_csv(SYMBOL, data_path)
    except Exception as e:
        print(f"Error reading data for {SYMBOL} from {data_path}: {e}")
        return []

    # Get strategy class
    try:
        strategy_module = get_strategy(strategy_name)
        StrategyClass: Type[Base] = getattr(strategy_module, strategy_name)
    except (ValueError, AttributeError) as e:
        print(f"Error loading strategy '{strategy_name}': {e}")
        return []
    
    bounds = StrategyClass.get_optimization_params()
    param_names = list(bounds.keys())
    # Convert bounds dict to tuple of lists
    lower_bounds = [b[0] for b in bounds.values()]
    upper_bounds = [b[1] for b in bounds.values()]
    bounds_tuple = (lower_bounds, upper_bounds)
    
    print("Running Walk-Forward Optimization...")
    wfa_results = walk_forward_optimize(data, StrategyClass, bounds_tuple, param_names, pop=pop, gen=gen)
    
    return wfa_results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Optimize the strategy")
    parser.add_argument('symbol', type=str, help="Symbol to optimize")
    parser.add_argument('--strategy', '-S', type=str, required=True, help="Strategy to optimize")
    parser.add_argument('--pop', type=int, default=80, help="Population size per island")
    parser.add_argument('--gen', type=int, default=200, help="Generations")
    parser.add_argument('--interval', '-I', type=str, default='5', help='Interval (1, 5, 15, 1H, 1D, etc.)')
    args = parser.parse_args()

    wfa_results = run_optimization(
        args.symbol, 
        args.strategy, 
        args.interval, 
        args.pop, 
        args.gen
    )
    
    if not wfa_results:
        print("No results generated.")
        exit()
        
    # Process results to find best robust params
    # Sort by robust_score (descending)
    wfa_results.sort(key=lambda x: x['robust_score'], reverse=True)
    
    best_result = wfa_results[0]
    best_params = best_result['params']
    
    strategy_module = get_strategy(args.strategy)
    StrategyClass = getattr(strategy_module, args.strategy)
    param_names = list(StrategyClass.get_optimization_params().keys())
    best_params_dict = dict(zip(param_names, best_params))

    print("\nBest Robust Parameters Found:")
    print("-" * 30)
    print(best_params_dict)
    print(f"OOS Sharpe: {best_result['oos_sharpe']:.2f}")
    if 'oos_sortino' in best_result:
        print(f"OOS Sortino: {best_result['oos_sortino']:.2f}")
    if 'total_return' in best_result:
        print(f"Total Return: {best_result['total_return']*100:.2f}%")
        
    print(f"Win Rate: {best_result['win_pct']*100:.2f}%")
    print(f"Max DD: {best_result['drawdown']*100:.2f}%")

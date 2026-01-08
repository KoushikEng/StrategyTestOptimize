"""
Strategy Optimizer Agent

Wrapper around the core optimization engine.
Only runs if the Reviewer approves the strategy.
"""

from typing import Dict, List, Optional
from optimize import run_optimization


def optimize_strategy(
    symbol: str,
    strategy_name: str,
    interval: str = "5",
    pop: int = 40,
    gen: int = 50,
) -> Dict:
    """
    Optimize a strategy's parameters using Walk-Forward Analysis.
    
    Args:
        symbol: Symbol to optimize on
        strategy_name: Name of the strategy class
        interval: Data interval
        pop: Population size for DE
        gen: Number of generations
        
    Returns:
        Dict with best parameters and metrics
    """
    
    results = run_optimization(
        symbol=symbol,
        strategy_name=strategy_name,
        interval=interval,
        pop=pop,
        gen=gen
    )
    
    if not results:
        return {
            "success": False,
            "message": "Optimization failed to find valid parameters",
            "params": None,
            "metrics": None
        }
    
    # Sort by robust score
    results.sort(key=lambda x: x.get("robust_score", 0), reverse=True)
    
    best = results[0]
    
    return {
        "success": True,
        "message": "Optimization complete",
        "params": best.get("params"),
        "metrics": {
            "oos_sharpe": best.get("oos_sharpe"),
            "oos_sortino": best.get("oos_sortino"),
            "total_return": best.get("total_return"),
            "win_rate": best.get("win_pct"),
            "max_drawdown": best.get("drawdown"),
            "robust_score": best.get("robust_score")
        },
        "all_results": results[:5]  # Top 5 results
    }


def format_optimization_result(result: Dict, param_names: List[str]) -> str:
    """Format optimization result for display."""
    lines = []
    
    if not result["success"]:
        return f"❌ {result['message']}"
    
    lines.append("✅ Optimization Complete")
    lines.append("")
    
    # Best parameters
    lines.append("📈 Best Parameters:")
    if result["params"] and param_names:
        for name, value in zip(param_names, result["params"]):
            lines.append(f"  {name}: {value:.2f}")
    
    # Metrics
    metrics = result.get("metrics", {})
    lines.append("")
    lines.append("📊 Out-of-Sample Metrics:")
    if metrics.get("oos_sharpe") is not None:
        lines.append(f"  Sharpe: {metrics['oos_sharpe']:.2f}")
    if metrics.get("oos_sortino") is not None:
        lines.append(f"  Sortino: {metrics['oos_sortino']:.2f}")
    if metrics.get("total_return") is not None:
        lines.append(f"  Return: {metrics['total_return']*100:.2f}%")
    if metrics.get("win_rate") is not None:
        lines.append(f"  Win Rate: {metrics['win_rate']*100:.2f}%")
    if metrics.get("max_drawdown") is not None:
        lines.append(f"  Max DD: {metrics['max_drawdown']*100:.2f}%")
    
    return "\n".join(lines)


# Example / Testing
if __name__ == "__main__":
    print("Testing Optimizer Agent...")
    print("Note: This requires existing strategy and data.")
    
    # Quick test with minimal settings
    result = optimize_strategy(
        symbol="SBIN",
        strategy_name="SimpleMACross",
        interval="15",
        pop=10,
        gen=2
    )
    
    from Utilities import get_strategy
    strategy_module = get_strategy("SimpleMACross")
    StrategyClass = getattr(strategy_module, "SimpleMACross")
    param_names = list(StrategyClass.get_optimization_params().keys())
    
    print(format_optimization_result(result, param_names))

"""
Research Agent Master Orchestrator

The closed-loop system that connects:
1. Translator (Text -> Spec)
2. Compiler (Spec -> Python)
3. Backtest Engine (Test)
4. Reviewer (Validate)
5. Optimizer (Tune)
"""

import argparse
import os
import sys
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from research_agent.schema import StrategySpec
from research_agent.translator import translate
from research_agent.compiler import compile_strategy, save_strategy
from research_agent.reviewer import review_strategy, format_review
from research_agent.optimizer import optimize_strategy, format_optimization_result
from main import run_backtest
from Utilities import get_strategy


def research_loop(
    description: str,
    symbol: str = "SBIN",
    interval: str = "15",
    provider: str = "google",
    download: bool = False,
    optimize: bool = False,
    verbose: bool = True
) -> dict:
    """
    Execute the full research loop.
    
    Args:
        description: Natural language strategy description
        symbol: Symbol to test on
        interval: Data interval
        provider: LLM provider ("google" or "openai")
        download: Whether to download data
        optimize: Whether to run optimization if approved
        verbose: Print progress
        
    Returns:
        dict: Results of the research loop
    """
    
    result = {
        "success": False,
        "spec": None,
        "strategy_path": None,
        "backtest_results": None,
        "review": None,
        "optimization": None,
        "error": None
    }
    
    # === STEP 1: Translate ===
    if verbose:
        print("=" * 60)
        print("🧠 STEP 1: Translation (Text -> Spec)")
        print("=" * 60)
        print(f"Input: {description[:100]}...")
        print()
    
    try:
        spec = translate(description, provider=provider)
        result["spec"] = spec.model_dump()
        if verbose:
            print(f"✅ Generated Spec: {spec.name}")
            print(f"   Indicators: {[i.name for i in spec.indicators]}")
            print(f"   Entry: {len(spec.entry_conditions)} conditions")
            print(f"   Exit: {len(spec.exit_conditions)} conditions")
            print()
    except Exception as e:
        result["error"] = f"Translation failed: {e}"
        if verbose:
            print(f"❌ Translation failed: {e}")
        return result
    
    # === STEP 2: Compile ===
    if verbose:
        print("=" * 60)
        print("🔧 STEP 2: Compilation (Spec -> Python)")
        print("=" * 60)
    
    try:
        strategy_path = save_strategy(spec, output_dir="strategies")
        result["strategy_path"] = strategy_path
        if verbose:
            print(f"✅ Compiled to: {strategy_path}")
            print()
    except Exception as e:
        result["error"] = f"Compilation failed: {e}"
        if verbose:
            print(f"❌ Compilation failed: {e}")
        return result
    
    # === STEP 3: Backtest ===
    if verbose:
        print("=" * 60)
        print("📊 STEP 3: Backtest")
        print("=" * 60)
    
    try:
        backtest_results = run_backtest(
            symbols=[symbol],
            strategy_name=spec.name,
            interval=interval,
            download=download
        )
        result["backtest_results"] = backtest_results
        
        if verbose and backtest_results:
            row = backtest_results[0]
            print(f"Symbol: {row[0]}")
            print(f"Net Profit: {row[1]:.2f}%")
            print(f"Win Rate: {row[2]:.2f}%")
            print(f"Sharpe: {row[3]:.2f}")
            print(f"Max DD: {row[5]:.2f}%")
            print(f"Trades: {row[6]}")
            print()
    except Exception as e:
        result["error"] = f"Backtest failed: {e}"
        if verbose:
            print(f"❌ Backtest failed: {e}")
        return result
    
    # === STEP 4: Review ===
    if verbose:
        print("=" * 60)
        print("🔍 STEP 4: Review (Sanity Check)")
        print("=" * 60)
    
    review = review_strategy(backtest_results)
    result["review"] = {
        "passed": review.passed,
        "score": review.score,
        "issues": review.issues,
        "warnings": review.warnings
    }
    
    if verbose:
        print(format_review(review))
        print()
    
    if not review.passed:
        result["error"] = "Strategy rejected by reviewer"
        if verbose:
            print("🛑 Strategy DID NOT PASS review. Stopping here.")
        return result
    
    result["success"] = True
    
    # === STEP 5: Optimize (Optional) ===
    if optimize and review.passed:
        if verbose:
            print("=" * 60)
            print("⚡ STEP 5: Optimization")
            print("=" * 60)
        
        try:
            opt_result = optimize_strategy(
                symbol=symbol,
                strategy_name=spec.name,
                interval=interval,
                pop=20,
                gen=10
            )
            result["optimization"] = opt_result
            
            if verbose:
                param_names = list(spec.optimization_params.keys())
                print(format_optimization_result(opt_result, param_names))
        except Exception as e:
            if verbose:
                print(f"⚠️ Optimization failed: {e}")
    
    # === COMPLETE ===
    if verbose:
        print()
        print("=" * 60)
        print("✅ Research Loop Complete!")
        print("=" * 60)
        print(f"Strategy: {spec.name}")
        print(f"Location: {strategy_path}")
        if result.get("optimization", {}).get("success"):
            print("Optimization: Complete")
    
    return result


def main():
    parser = argparse.ArgumentParser(description="Research Agent - Generate and test trading strategies")
    parser.add_argument("description", type=str, nargs="?", help="Strategy description")
    parser.add_argument("--symbol", "-s", type=str, default="SBIN", help="Symbol to test")
    parser.add_argument("--interval", "-I", type=str, default="15", help="Data interval")
    parser.add_argument("--provider", type=str, default="google", choices=["google", "openai"], help="LLM provider")
    parser.add_argument("--download", action="store_true", help="Download data first")
    parser.add_argument("--optimize", "-O", action="store_true", help="Run optimization if approved")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet mode")
    
    args = parser.parse_args()
    
    if not args.description:
        # Interactive mode
        print("🤖 Research Agent - Strategy Generator")
        print("-" * 40)
        print("Enter your strategy description (Ctrl+D to finish):")
        print()
        
        try:
            lines = []
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
        
        description = "\n".join(lines)
    else:
        description = args.description
    
    if not description.strip():
        print("No description provided. Exiting.")
        return
    
    result = research_loop(
        description=description,
        symbol=args.symbol,
        interval=args.interval,
        provider=args.provider,
        download=args.download,
        optimize=args.optimize,
        verbose=not args.quiet
    )
    
    if not result["success"]:
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
Research Agent Master Orchestrator (LangGraph Edition)

The closed-loop system that connects:
1. Translator (Text -> Spec)
2. Compiler (Spec -> Python)
3. Backtest Engine (Test)
4. Reviewer (Validate)
5. Repair Agent (Fix)
6. Optimizer (Tune)

Powered by LangGraph for cyclic orchestration and state management.
"""

import argparse
import os
import sys
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from research_agent.graph import build_graph
from research_agent.state import AgentState
from research_agent.reviewer import format_review
from research_agent.optimizer import format_optimization_result

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
    Execute the full research loop using LangGraph.
    """
    
    if verbose:
        print("🚀 Starting Research Agent (LangGraph)...")
        print(f"Goal: {description[:100]}...")
        print("-" * 50)
    
    # Initialize State
    initial_state: AgentState = {
        "user_request": description,
        "symbol": symbol,
        "interval": interval,
        "download": download,
        "strategy_spec": None,
        "strategy_path": None,
        "backtest_results": None,
        "review_result": None,
        "error": None,
        "iterations": 0
    }
    
    # Build Graph
    app = build_graph()
    
    # Invoke Graph
    # This runs the entire loop including repairs
    try:
        final_state = app.invoke(initial_state)
    except Exception as e:
        if verbose:
            print(f"❌ Graph execution failed: {e}")
        return {"error": str(e), "success": False}
    
    # Process Final State
    result = {
        "success": False,
        "spec": final_state.get("strategy_spec"),
        "strategy_path": final_state.get("strategy_path"),
        "backtest_results": final_state.get("backtest_results"),
        "review": final_state.get("review_result"),
        "optimization": final_state.get("optimizer_result"),
        "error": final_state.get("error")
    }
    
    # Check if we succeeded
    # Success means: No error, passed review (if reviewed), and optimization done (if requested)
    # Actually simpler: if final node was optimizer (and it ran), or if we ended at reviewer/backtester but cleanly.
    # If error is present, we failed.
    
    if final_state.get("error"):
        if verbose:
           print(f"\n❌ FAILED: {final_state['error']}")
    else:
        result["success"] = True
        
        if verbose:
            print("\n✅ Research Loop Complete!")
            if result['strategy_path']:
                print(f"Strategy: {result['spec'].get('name')}")
                print(f"Path: {result['strategy_path']}")
            
            if result['review']:
                print("\nREVIEW RESULT:")
                # Construct temporary review obj for formatting
                from research_agent.reviewer import ReviewResult
                r_dict = result['review']
                rev_obj = ReviewResult(**r_dict)
                print(format_review(rev_obj))
                
            if result['optimization']:
                print("\nOPTIMIZATION RESULT:")
                param_names = list(result['spec'].get('optimization_params', {}).keys())
                print(format_optimization_result(result['optimization'], param_names))

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

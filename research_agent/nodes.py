"""
Research Agent Graph Nodes

Wrappers around core logic components to function as nodes in the LangGraph.
"""

from research_agent.state import AgentState
from research_agent.translator import translate, save_spec
from research_agent.compiler import save_strategy
from research_agent.reviewer import review_strategy
from research_agent.repair import repair_spec
from research_agent.optimizer import optimize_strategy
from research_agent.schema import StrategySpec
from main import run_backtest
from research_agent.config import MAX_ITERATIONS

def translator_node(state: AgentState):
    """Generate strategy spec from user request."""
    print("--- TRANSLATOR ---")
    try:
        # Default to google for now, or pick from args if we stored it
        spec = translate(state["user_request"], provider="google")
        save_spec(spec)
        return {"strategy_spec": spec.model_dump(), "error": None}
    except Exception as e:
        print(f"Translation failed: {e}")
        exit(1)
        return {"error": f"Translation error: {str(e)}"}

def compiler_node(state: AgentState):
    """Compile spec to Python strategy."""
    print("--- COMPILER ---")
    spec_data = state.get("strategy_spec")
    print("spec_data", spec_data)
    if not spec_data:
        return {"error": "No strategy spec found"}
    
    try:
        spec = StrategySpec(**spec_data)
        path = save_strategy(spec)
        return {"strategy_path": path, "error": None}
    except Exception as e:
        return {"error": f"Compilation error: {str(e)}"}

def backtester_node(state: AgentState):
    """Run backtest."""
    print("--- BACKTESTER ---")
    path = state.get("strategy_path")
    if not path:
        return {"error": "No strategy file path"}
    
    spec_dict = state.get("strategy_spec", {})
    strategy_name = spec_dict.get("name")
    
    try:
        results = run_backtest(
            symbols=[state["symbol"]],
            strategy_name=strategy_name,
            interval=state["interval"],
            download=state["download"]
        )
        return {"backtest_results": results, "error": None}
    except Exception as e:
        return {"error": f"Runtime error: {str(e)}"}

def reviewer_node(state: AgentState):
    """Review results."""
    print("--- REVIEWER ---")
    results = state.get("backtest_results")
    if not results:
        return {"error": "No backtest results to review"}
        
    review = review_strategy(results)
    return {"review_result": {
        "passed": review.passed,
        "score": review.score,
        "issues": review.issues,
        "warnings": review.warnings,
        "recommendations": review.recommendations
    }}

def optimizer_node(state: AgentState):
    """Run optimization (optional final step)."""
    print("--- OPTIMIZER ---")
    # This is terminal for now, just print or return result
    # We could store optimization results in state
    spec = state.get("strategy_spec")
    try:
        opt_res = optimize_strategy(
            symbol=state["symbol"],
            strategy_name=spec.get("name"),
            interval=state["interval"]
        )
        return {"optimizer_result": opt_res} # Add to schema if we want
    except Exception as e:
        print(f"Optimization failed: {e}")
        return {}

def repair_node(state: AgentState):
    """Fix the strategy spec."""
    print("--- REPAIR ---")
    iterations = state.get("iterations", 0)
    if iterations >= MAX_ITERATIONS:
        return {"error": "Max iterations reached. Stopping repair loops."}
    
    error = state.get("error")
    review = state.get("review_result")
    spec = state.get("strategy_spec")
    
    context = ""
    if error:
        context = f"Error occurred: {error}"
    elif review and not review.get("passed"):
        context = f"Review Failed. Issues: {review.get('issues')}"
    
    try:
        # Defaults to google
        fixed_spec = repair_spec(spec, context, provider="google")
        return {
            "strategy_spec": fixed_spec, 
            "error": None, 
            "review_result": None,
            "iterations": iterations + 1
        }
    except Exception as e:
        return {"error": f"Repair failed: {str(e)}"}

"""
Research Agent Graph Definition

Defines the LangGraph StateGraph, nodes, and edges.
"""

from langgraph.graph import StateGraph, END
from research_agent.state import AgentState
from research_agent.nodes import (
    translator_node, 
    compiler_node, 
    backtester_node, 
    reviewer_node, 
    repair_node,
    optimizer_node
)
from research_agent.config import MAX_ITERATIONS

def should_repair_after_compile(state: AgentState):
    if state.get("error"):
        return "repair"
    return "backtest"

def should_repair_after_backtest(state: AgentState):
    if state.get("error"):
        return "repair"
    # Also check if results are empty (runtime silent fail?)
    if not state.get("backtest_results"):
         # Treat empty results as error for repair
        state["error"] = "No trades generated or silent failure"
        return "repair"
    return "review"

def should_repair_after_review(state: AgentState):
    review = state.get("review_result")
    if not review or not review.get("passed"):
        return "repair"
    return "optimize"

def should_continue_repair(state: AgentState):
    if state.get("iterations", 0) >= MAX_ITERATIONS:
        return "end" # Give up
    if state.get("error") and "Max iterations" in state.get("error"):
        return "end"
    return "compile" # Try compiling the fixed spec

def build_graph():
    """Construct the Research Agent Graph."""
    
    workflow = StateGraph(AgentState)
    
    # Add Nodes
    workflow.add_node("translator", translator_node)
    workflow.add_node("compiler", compiler_node)
    workflow.add_node("backtester", backtester_node)
    workflow.add_node("reviewer", reviewer_node)
    workflow.add_node("repair", repair_node)
    workflow.add_node("optimizer", optimizer_node)
    
    # Set Entry Point
    workflow.set_entry_point("translator")
    
    # Add Edges
    workflow.add_edge("translator", "compiler")
    
    # Conditional Edges
    workflow.add_conditional_edges(
        "compiler",
        should_repair_after_compile,
        {
            "repair": "repair",
            "backtest": "backtester"
        }
    )
    
    workflow.add_conditional_edges(
        "backtester",
        should_repair_after_backtest,
        {
            "repair": "repair",
            "review": "reviewer"
        }
    )
    
    workflow.add_conditional_edges(
        "reviewer",
        should_repair_after_review,
        {
            "repair": "repair",
            "optimize": "optimizer"
        }
    )
    
    workflow.add_conditional_edges(
        "repair",
        should_continue_repair,
        {
            "compile": "compiler",
            "end": END
        }
    )
    
    workflow.add_edge("optimizer", END)
    
    return workflow.compile()

if __name__ == "__main__":
    # Visualization (if supported)
    try:
        app = build_graph()
        print(app.get_graph().draw_mermaid())
    except Exception as e:
        print(f"Could not draw graph: {e}")

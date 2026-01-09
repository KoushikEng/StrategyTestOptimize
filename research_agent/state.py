"""
Research Agent State

Defines the state object passed between nodes in the LangGraph.
"""

from typing import TypedDict, Optional, Dict, Any, List, Annotated
import operator

class AgentState(TypedDict):
    """
    The state of the Research Agent workflow.
    """
    # Inputs
    user_request: str
    symbol: str
    interval: str
    download: bool
    
    # Artifacts (Mutable)
    strategy_spec: Optional[Dict[str, Any]]  # The JSON Spec
    # We store Python code as string, but maybe just path is enough. 
    # Storing path is safer for now as we save to disk.
    strategy_path: Optional[str]
    
    # Execution Results
    backtest_results: Optional[List[Any]] # Raw rows
    
    # Feedback / validation
    review_result: Optional[Dict[str, Any]] # {passed, score, issues, ...}
    error: Optional[str] # Any error message (Compiler, Runtime, etc.)
    
    # Orchestration
    iterations: int # To prevent infinite loops

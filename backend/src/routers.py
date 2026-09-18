import logging
from typing import Literal
from .state import AgentState

logger = logging.getLogger("insight_copilot.routers")


def route_after_plan(state: AgentState) -> Literal["tool_executor", "direct_answer", "unsupported"]:
    """
    Evaluates planner decision and routes execution to tool_executor, direct_answer, or unsupported.
    """
    route = state.get("route", "direct_answer")
    if route == "tools":
        return "tool_executor"
    elif route == "unsupported":
        return "unsupported"
    return "direct_answer"


def should_continue(state: AgentState) -> Literal["tool_executor", "synthesizer", "error_handler"]:
    """
    Evaluates loop termination, remaining tools in plan, or error state.
    """
    # 1. Error condition
    if state.get("error"):
        return "error_handler"

    # 2. Max iterations safeguard
    if state.get("iterations", 0) >= 4:
        logger.info("Max iterations (4) reached. Forcing synthesis.")
        return "synthesizer"

    # 3. Remaining tools in queue
    tool_plan = state.get("tool_plan", [])
    if tool_plan and len(tool_plan) > 0:
        return "tool_executor"

    # 4. All tools executed -> finalize
    return "synthesizer"

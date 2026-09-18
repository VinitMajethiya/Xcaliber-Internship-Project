import logging
from langgraph.graph import StateGraph, START, END
from .state import AgentState
from .nodes import (
    planner_node,
    tool_executor_node,
    synthesizer_node,
    direct_answer_node,
    unsupported_node,
    error_handler_node,
)
from .routers import route_after_plan, should_continue
from .config import get_checkpointer

logger = logging.getLogger("insight_copilot.graph")


def build_graph(checkpointer=None):
    """
    Constructs and compiles the Insight Copilot LangGraph StateGraph.
    """
    builder = StateGraph(AgentState)

    # 1. Add all graph nodes
    builder.add_node("planner", planner_node)
    builder.add_node("tool_executor", tool_executor_node)
    builder.add_node("synthesizer", synthesizer_node)
    builder.add_node("direct_answer", direct_answer_node)
    builder.add_node("unsupported", unsupported_node)
    builder.add_node("error_handler", error_handler_node)

    # 2. Add edges
    builder.add_edge(START, "planner")

    builder.add_conditional_edges(
        "planner",
        route_after_plan,
        {
            "tool_executor": "tool_executor",
            "direct_answer": "direct_answer",
            "unsupported": "unsupported",
        },
    )

    builder.add_conditional_edges(
        "tool_executor",
        should_continue,
        {
            "tool_executor": "tool_executor",
            "synthesizer": "synthesizer",
            "error_handler": "error_handler",
        },
    )

    builder.add_edge("synthesizer", END)
    builder.add_edge("direct_answer", END)
    builder.add_edge("unsupported", END)
    builder.add_edge("error_handler", END)

    # 3. Compile with checkpointer
    cp = checkpointer if checkpointer is not None else get_checkpointer()
    graph = builder.compile(checkpointer=cp)
    logger.info("LangGraph agent graph successfully compiled.")
    return graph

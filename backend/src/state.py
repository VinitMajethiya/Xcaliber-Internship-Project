from typing import TypedDict, Annotated, Literal, Any
from langgraph.graph.message import add_messages


class ReasoningStep(TypedDict):
    stage: Literal["plan", "tool_call", "tool_result", "synthesis", "error"]
    title: str
    detail: str
    payload: dict[str, Any] | None


class AgentState(TypedDict):
    # conversation
    messages: Annotated[list, add_messages]

    # planning
    user_query: str
    plan: str                      # natural-language rationale shown to the user
    route: Literal["tools", "direct_answer", "unsupported"]
    tool_plan: list[dict[str, Any]] # [{"tool": "query_data", "why": "...", "args": {...}}]

    # execution
    tool_results: list[dict[str, Any]] # [{"tool": ..., "ok": bool, "data": ..., "summary": str}]
    iterations: int                # guard against loops, max 4

    # output
    reasoning_trace: list[ReasoningStep]
    chart_spec: dict[str, Any] | None
    final_answer: str
    error: str | None

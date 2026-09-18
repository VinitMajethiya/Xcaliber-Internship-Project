import logging
from typing import Literal, Any
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from .state import AgentState, ReasoningStep
from .schema import get_schema_prompt_text
from .prompts import (
    PLANNER_SYSTEM_PROMPT,
    SYNTHESIZER_SYSTEM_PROMPT,
    DIRECT_ANSWER_PROMPT,
    UNSUPPORTED_PROMPT,
)
from .config import get_llm, GEMINI_API_KEY
from .tools import query_data, compute_metrics, make_chart, web_search

logger = logging.getLogger("insight_copilot.nodes")


class ToolCallPlan(BaseModel):
    tool: Literal["query_data", "compute_metrics", "make_chart", "web_search"] = Field(
        description="The tool to invoke"
    )
    why: str = Field(description="Explanation of why this specific tool is needed")
    args: dict[str, Any] = Field(default_factory=dict, description="Structured arguments for the tool")


class PlanModel(BaseModel):
    rationale: str = Field(description="Step-by-step reasoning plan for answering the inquiry")
    route: Literal["tools", "direct_answer", "unsupported"] = Field(
        description="Target execution route"
    )
    tool_plan: list[ToolCallPlan] = Field(
        default_factory=list,
        description="Sequence of tool calls to execute if route is 'tools'"
    )


def _extract_text_content(content: Any) -> str:
    """Robustly normalizes LLM response content into a clean string across model versions."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, dict):
                text_parts.append(part.get("text", ""))
            elif hasattr(part, "text"):
                text_parts.append(getattr(part, "text"))
            else:
                text_parts.append(str(part))
        return "".join(text_parts).strip()
    return str(content)


def planner_node(state: AgentState) -> dict[str, Any]:
    """
    Planner node: analyzes query, consults schema profile, and generates structured plan.
    Emits structured JSON: rationale, route, tool_plan.
    """
    user_query = state.get("user_query") or (state["messages"][-1].content if state.get("messages") else "")
    trace = list(state.get("reasoning_trace") or [])

    schema_text = get_schema_prompt_text()
    prompt = PLANNER_SYSTEM_PROMPT.format(schema_context=schema_text)

    # Fallback / heuristic plan if API key is not present (for local testing/offline validation)
    if not GEMINI_API_KEY:
        lower_q = user_query.lower()
        words_q = set(lower_q.replace("?", "").replace(".", "").replace(",", "").split())
        
        if words_q & {"hi", "hello", "hey", "howdy"} or any(p in lower_q for p in ["who are you", "what can you", "help me", "capabilities", "what do you do"]):
            route = "direct_answer"
            rationale = "User inquiry is a greeting or capability question. Routing directly to introductory assistant response."
            tool_plan = []
        elif any(w in lower_q for w in ["weather", "flight", "hotel", "crypto", "bitcoin", "book", "stock price", "recipe", "password"]):
            route = "unsupported"
            rationale = "Inquiry requires external real-time actions or personal services outside the scope of e-commerce retail analytics."
            tool_plan = []
        elif any(w in lower_q for w in ["plot", "chart", "visualize", "graph"]):
            route = "tools"
            rationale = "User requested a visual chart. First querying aggregated metrics, then generating Plotly chart specification."
            tool_plan = [
                {
                    "tool": "query_data",
                    "why": "Aggregate monthly order payments to prepare time-series chart data",
                    "args": {"group_by": ["order_year_month"], "metrics": [{"column": "total_payment", "agg": "sum"}], "limit": 24, "ascending": True}
                },
                {
                    "tool": "make_chart",
                    "why": "Construct interactive line chart comparing monthly revenue",
                    "args": {"chart_type": "line", "x": "order_year_month", "y": "total_payment", "title": "Monthly Payment Volume Over Time", "data_ref": 0}
                }
            ]
        elif any(w in lower_q for w in ["season", "seasonality", "seasonal"]):
            route = "tools"
            rationale = "User inquired about seasonality. First extracting monthly metrics, then computing coefficient of variation to detect seasonal patterns."
            tool_plan = [
                {
                    "tool": "query_data",
                    "why": "Retrieve monthly revenue and order volume",
                    "args": {"group_by": ["order_month"], "metrics": [{"column": "total_payment", "agg": "mean"}], "sort_by": "order_month", "ascending": True}
                },
                {
                    "tool": "compute_metrics",
                    "why": "Evaluate coefficient of variation (CV) to determine whether meaningful seasonality exists (CV > 0.15)",
                    "args": {"operation": "seasonality", "column": "total_payment", "data_ref": 0}
                }
            ]
        elif any(w in lower_q for w in ["compare", "difference", "vs", "versus"]):
            route = "tools"
            rationale = "User asked for a regional or category comparison. Slicing comparative groups, then calculating share of total."
            tool_plan = [
                {
                    "tool": "query_data",
                    "why": "Retrieve top regions/states by sales volume",
                    "args": {"group_by": ["customer_state"], "metrics": [{"column": "total_payment", "agg": "sum"}], "limit": 5}
                },
                {
                    "tool": "compute_metrics",
                    "why": "Compute share of total percentage across the compared segments",
                    "args": {"operation": "share_of_total", "column": "total_payment", "data_ref": 0}
                }
            ]
        elif any(w in lower_q for w in ["unusual", "outlier", "anomaly", "anomalies", "summarize", "summary", "strange", "spike", "irregularity"]):
            route = "tools"
            rationale = "User requested anomaly detection or an open-ended summary. Running IQR outlier analysis and descriptive stats across key metrics."
            tool_plan = [
                {
                    "tool": "compute_metrics",
                    "why": "Detect freight value anomalies and extreme outliers using Interquartile Range (IQR) fence calculation",
                    "args": {"operation": "outliers", "column": "freight_value"}
                }
            ]
        elif any(w in lower_q for w in ["inflation", "brazil economy", "gdp", "market condition", "external"]):
            route = "tools"
            rationale = "Inquiry requires external macroeconomic knowledge outside the dataset. Routing to web search."
            tool_plan = [
                {
                    "tool": "web_search",
                    "why": "Retrieve external Brazilian macroeconomic and e-commerce growth context",
                    "args": {"query": user_query, "max_results": 3}
                }
            ]
        else:
            route = "tools"
            rationale = "Inquiry asks for dataset metrics or rankings. Executing structured query_data aggregation."
            tool_plan = [
                {
                    "tool": "query_data",
                    "why": "Retrieve top categories by total payment",
                    "args": {"group_by": ["category"], "metrics": [{"column": "total_payment", "agg": "sum"}], "limit": 5}
                }
            ]
    else:
        try:
            llm = get_llm()
            structured_llm = llm.with_structured_output(PlanModel)
            messages = [
                SystemMessage(content=prompt),
                HumanMessage(content=f"User Query: {user_query}")
            ]
            plan_result: PlanModel = structured_llm.invoke(messages)
            rationale = plan_result.rationale
            route = plan_result.route
            tool_plan = [tp.model_dump() for tp in plan_result.tool_plan]
        except Exception as e:
            logger.error(f"Planner LLM invocation failed: {e}. Using fallback routing.")
            route = "direct_answer"
            rationale = f"Encountered planner issue ({e}), answering directly."
            tool_plan = []

    plan_step: ReasoningStep = {
        "stage": "plan",
        "title": f"Plan: route → '{route}'",
        "detail": rationale,
        "payload": {
            "route": route,
            "tool_count": len(tool_plan),
            "tool_plan": tool_plan,
        }
    }
    trace.append(plan_step)

    return {
        "plan": rationale,
        "route": route,
        "tool_plan": tool_plan,
        "reasoning_trace": trace,
        "iterations": 0,
        "tool_results": state.get("tool_results") or [],
        "error": None,
    }


def tool_executor_node(state: AgentState) -> dict[str, Any]:
    """
    Tool executor node: executes tools from tool_plan sequentially.
    Handles data_ref chaining, chart_spec capture, and reasoning trace logging.
    """
    tool_plan = list(state.get("tool_plan") or [])
    tool_results = list(state.get("tool_results") or [])
    trace = list(state.get("reasoning_trace") or [])
    iterations = state.get("iterations", 0) + 1
    chart_spec = state.get("chart_spec")

    if not tool_plan:
        return {"iterations": iterations}

    # 1. Pop next tool in queue
    current_tool = tool_plan.pop(0)
    tool_name = current_tool.get("tool", "unknown")
    tool_args = current_tool.get("args", {})
    why = current_tool.get("why", "")

    trace.append({
        "stage": "tool_call",
        "title": f"Calling Tool: {tool_name}",
        "detail": f"Reason: {why}",
        "payload": {"tool": tool_name, "args": tool_args}
    })

    # 2. Execute the tool
    tool_result = None
    try:
        if tool_name == "query_data":
            tool_result = query_data(tool_args)
        elif tool_name == "compute_metrics":
            tool_result = compute_metrics(tool_args, prior_results=tool_results)
        elif tool_name == "make_chart":
            tool_result = make_chart(tool_args, prior_results=tool_results)
            if tool_result.get("ok") and tool_result.get("data"):
                chart_spec = tool_result["data"]
        elif tool_name == "web_search":
            tool_result = web_search(tool_args)
        else:
            tool_result = {
                "ok": False,
                "data": {},
                "summary": f"Unrecognized tool '{tool_name}' requested.",
                "meta": {},
                "error": f"Unknown tool: {tool_name}"
            }
    except Exception as e:
        logger.error(f"Error executing tool '{tool_name}': {e}", exc_info=True)
        tool_result = {
            "ok": False,
            "data": {},
            "summary": f"Execution of tool '{tool_name}' failed: {str(e)}",
            "meta": {"tool": tool_name},
            "error": str(e),
        }

    # Stamp the tool name into the result envelope so synthesizer and test assertions can reference it
    tool_result["tool"] = tool_name
    tool_results.append(tool_result)

    # 3. Log reasoning trace step
    summary_text = tool_result.get("summary", "")
    trace.append({
        "stage": "tool_result",
        "title": f"Result: {tool_name}",
        "detail": summary_text,
        "payload": {
            "ok": tool_result.get("ok", False),
            "meta": tool_result.get("meta", {}),
            "has_data": bool(tool_result.get("data")),
        }
    })

    result_updates: dict[str, Any] = {
        "tool_plan": tool_plan,
        "tool_results": tool_results,
        "reasoning_trace": trace,
        "iterations": iterations,
    }

    if chart_spec:
        result_updates["chart_spec"] = chart_spec

    # If critical unrecoverable tool failure
    if not tool_result.get("ok") and tool_result.get("error"):
        # We store error in state only if it completely blocks the inquiry
        if iterations >= 4 or not tool_plan:
            result_updates["error"] = tool_result.get("error")

    return result_updates


def synthesizer_node(state: AgentState) -> dict[str, Any]:
    """
    Synthesizer node: packages tool findings into the mandatory 3-part answer shape
    (1. Direct Answer, 2. Supporting Numbers, 3. Why it Matters).
    """
    user_query = state.get("user_query", "")
    tool_results = state.get("tool_results", [])
    trace = list(state.get("reasoning_trace") or [])

    # Format summaries from all executed tools
    summaries = "\n".join([f"- **Tool `{tr.get('tool')}`**: {tr.get('summary', '')}" for tr in tool_results])

    if not GEMINI_API_KEY:
        # High quality rule-based 3-part executive synthesis for offline/local validation
        first_tool = tool_results[0] if tool_results else {}
        first_summary = first_tool.get("summary", "Analysis completed.")
        
        answer = (
            f"### Executive Insight: {user_query}\n\n"
            f"**1. Direct Answer:**\n"
            f"{first_summary}\n\n"
            f"**2. Supporting Numbers & Breakdown:**\n"
            f"{summaries if summaries else 'Processed analytics across 112,650 verified retail orders.'}\n\n"
            f"**3. Strategic Takeaway / Why it Matters:**\n"
            f"Understanding these volume and operational patterns enables management to allocate inventory more efficiently, "
            f"mitigate shipping bottlenecks, and focus marketing spend on high-margin segments."
        )
    else:
        try:
            llm = get_llm()
            context_text = f"User Query: {user_query}\n\nTool Execution Results:\n{summaries}\n\nRaw Tool Outputs:\n{tool_results}"
            messages = [
                SystemMessage(content=SYNTHESIZER_SYSTEM_PROMPT),
                HumanMessage(content=context_text)
            ]
            response = llm.invoke(messages)
            answer = _extract_text_content(response.content)
        except Exception as e:
            logger.error(f"Synthesizer LLM failed: {e}")
            answer = f"### Analysis for: {user_query}\n\n{summaries}"

    trace.append({
        "stage": "synthesis",
        "title": "Synthesis & Executive Insight",
        "detail": "Formulated structured three-part executive insight from tool findings.",
        "payload": {"tool_results_count": len(tool_results)}
    })

    return {
        "final_answer": answer,
        "reasoning_trace": trace,
        "messages": [AIMessage(content=answer)],
    }


def direct_answer_node(state: AgentState) -> dict[str, Any]:
    """
    Direct answer node for greetings and capability explanations.
    """
    user_query = state.get("user_query", "")
    trace = list(state.get("reasoning_trace") or [])

    if not GEMINI_API_KEY:
        answer = (
            "👋 **Hello! I am Insight Copilot**, your AI Business Intelligence Analyst specialized in **Brazilian E-Commerce (Olist)**.\n\n"
            "I can assist you with deep analytics across **112,650 orders** spanning 2016–2018:\n"
            "- 📈 **Revenue & Payment Analysis**: Credit cards, boleto, vouchers across 73 product categories.\n"
            "- 🚚 **Logistics & Delivery Efficiency**: Freight costs, shipping transit times, and delivery delays.\n"
            "- ⭐ **Customer Satisfaction**: Review score drivers, review distributions, and regional sentiment.\n"
            "- 📊 **Interactive Visualizations & Outlier Detection**: Dynamic Plotly charts, IQR anomaly alerts, and seasonality testing.\n\n"
            "**Try asking me:**\n"
            "1. *What are the top 5 product categories by total payment?*\n"
            "2. *Is there any seasonal trend or quarterly spike in order volume?*\n"
            "3. *Compare revenue and freight costs between São Paulo (SP) and Rio de Janeiro (RJ).*\n"
            "4. *Plot monthly payment volume over time.*"
        )
    else:
        try:
            llm = get_llm()
            messages = [
                SystemMessage(content=DIRECT_ANSWER_PROMPT),
                HumanMessage(content=user_query)
            ]
            response = llm.invoke(messages)
            answer = _extract_text_content(response.content)
        except Exception as e:
            logger.error(f"Direct answer generation failed: {e}")
            answer = "Hello! I am Insight Copilot. How can I assist you with analyzing your retail e-commerce data today?"

    trace.append({
        "stage": "synthesis",
        "title": "Direct Response Generated",
        "detail": "Formulated direct introductory response without executing data tools.",
        "payload": None
    })

    return {
        "final_answer": answer,
        "reasoning_trace": trace,
        "messages": [AIMessage(content=answer)],
    }


def unsupported_node(state: AgentState) -> dict[str, Any]:
    """
    Unsupported node for out-of-scope inquiries.
    Provides an honest refusal without hallucination and redirects to supported analytics.
    """
    user_query = state.get("user_query", "")
    trace = list(state.get("reasoning_trace") or [])

    if not GEMINI_API_KEY:
        answer = (
            "I cannot assist with that specific request because it falls outside the analytical scope of the **Brazilian E-Commerce (Olist)** dataset.\n\n"
            "My capabilities are focused strictly on e-commerce operations, financial aggregations, logistics performance, and customer review insights. "
            "I do not have access to live personal booking services, weather telemetry, or external system mutations.\n\n"
            "**What I can do instead:**\n"
            "- Analyze order payments, freight rates, and customer review ratings.\n"
            "- Compare regional performances across Brazilian states (e.g., SP, RJ, MG).\n"
            "- Generate interactive time-series plots and identify anomalous transactions."
        )
    else:
        try:
            llm = get_llm()
            messages = [
                SystemMessage(content=UNSUPPORTED_PROMPT),
                HumanMessage(content=user_query)
            ]
            response = llm.invoke(messages)
            answer = _extract_text_content(response.content)
        except Exception as e:
            logger.error(f"Unsupported handler failed: {e}")
            answer = "This request is outside the scope of the Brazilian E-Commerce dataset. Please ask an analytical retail data question."

    trace.append({
        "stage": "synthesis",
        "title": "Honest Scope Refusal",
        "detail": "Gracefully refused out-of-scope inquiry and provided valid analytical alternatives.",
        "payload": None
    })

    return {
        "final_answer": answer,
        "reasoning_trace": trace,
        "messages": [AIMessage(content=answer)],
    }


def error_handler_node(state: AgentState) -> dict[str, Any]:
    """
    Error handler node: transforms internal tool failures into constructive guidance.
    """
    error_msg = state.get("error") or "An unexpected issue occurred during tool execution."
    trace = list(state.get("reasoning_trace") or [])

    answer = (
        f"⚠️ I encountered an issue while processing your analytical request: **{error_msg}**.\n\n"
        "Please check that the requested dimensions (e.g., category, customer_state, order_year) or metrics "
        "(total_payment, price, freight_value, review_score) exist in the dataset, or try rephrasing your inquiry."
    )

    trace.append({
        "stage": "error",
        "title": "Error Handled Gracefully",
        "detail": f"Handled tool failure gracefully: {error_msg}",
        "payload": {"error": error_msg}
    })

    return {
        "final_answer": answer,
        "reasoning_trace": trace,
        "messages": [AIMessage(content=answer)],
    }

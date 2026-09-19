# 06 — The Planner

The single highest-leverage component in the build. If routing is wrong, every downstream node is wrong and the reasoning trace is fiction. Build this first, verify it in isolation, then let tools land on top of it.

---

## 1. Model config (`src/config.py`)

```python
import os
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI


def _get_secret(key: str) -> str:
    """Streamlit secrets in deployment, env var locally."""
    try:
        return st.secrets[key]
    except Exception:
        value = os.environ.get(key)
        if not value:
            raise RuntimeError(f"Missing required secret: {key}")
        return value


PLANNER_MODEL = "gemini-2.5-flash"
SYNTH_MODEL = "gemini-2.5-flash"


def get_llm(model: str = PLANNER_MODEL, temperature: float = 0.0):
    return ChatGoogleGenerativeAI(
        model=model,
        temperature=temperature,
        google_api_key=_get_secret("GOOGLE_API_KEY"),
        max_retries=3,
    )
```

Gemini free-tier notes that will bite you:

- **Rate limits are per-minute.** A multi-step query fires planner + re-plan + synthesizer in seconds. Add `max_retries=3` (above) and catch `ResourceExhausted` in the node, routing to `error_handler` with "I'm being rate-limited, try again in a moment." A reviewer hitting a raw 429 traceback costs you the hosting/UX marks.
- **Temperature 0 for the planner**, higher (0.3–0.4) for the synthesizer. Routing should be deterministic; prose shouldn't be robotic.
- **Verify the model string** before you build on it — Gemini names shift. Run a one-line `get_llm().invoke("hi")` as your very first check.

---

## 2. The schema (`src/state.py` or `src/models.py`)

```python
from typing import Literal, Any
from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    """One step in the agent's plan."""

    tool: Literal["query_data", "compute_metrics", "make_chart", "web_search"] = Field(
        description="Which tool to invoke for this step."
    )
    why: str = Field(
        description=(
            "One sentence explaining why THIS tool is the right choice for this step, "
            "referring to what the user asked for. Shown to the user in the reasoning panel."
        )
    )
    args: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Arguments for the tool, matching its parameter schema. May be left empty "
            "for a later step whose inputs depend on an earlier step's result."
        ),
    )


class PlanModel(BaseModel):
    """The planner's structured output. Produced BEFORE any tool runs."""

    rationale: str = Field(
        description=(
            "2-3 sentences of plain-language reasoning: what is the user actually asking, "
            "what would be needed to answer it, and what the approach will be. "
            "Write it for a human reading a 'show reasoning' panel. "
            "Do not mention that you are an AI or describe your own schema."
        )
    )
    route: Literal["tools", "direct_answer", "unsupported"] = Field(
        description="Which path this query takes through the graph."
    )
    tool_plan: list[ToolCall] = Field(
        default_factory=list,
        description=(
            "Ordered list of tool calls. MUST be empty unless route == 'tools'. "
            "Include only the tools genuinely needed — one is common, two is normal "
            "for comparison or chart questions, three is rare."
        ),
    )
    assumptions: list[str] = Field(
        default_factory=list,
        description=(
            "Any interpretation you had to make, e.g. resolving 'last quarter' to a "
            "specific date range, or assuming 'revenue' means the Sales column. "
            "These get surfaced to the user so they can correct you."
        ),
    )
```

Three things here are doing real work:

- **`why` on every `ToolCall`** is what turns "the agent called query_data" into "the agent explained why it called query_data." That distinction is literally the wording of the 20% reasoning criterion.
- **`assumptions`** handles the "last quarter" problem — there is no *today* inside a static dataset. Surfacing the resolution instead of silently picking one reads as analyst judgment.
- **Field descriptions are prompt.** Gemini reads them when filling the schema. Vague descriptions produce vague plans.

---

## 3. The prompt (`src/prompts.py`)

```python
PLANNER_SYSTEM = """You are the planning component of an analyst agent that answers \
questions about a sales dataset. Your job is to decide HOW to answer — not to answer.

## The dataset you have access to
{dataset_profile}

## Your tools
- query_data: filter, group and aggregate the dataset. Returns records.
  Use for: totals, rankings, top-N, breakdowns by region/category/segment, filtered slices.
- compute_metrics: growth rates, share of total, descriptive stats, correlation,
  outlier detection, trend direction, seasonality.
  Use for: derived analysis. Usually runs AFTER query_data on its output.
- make_chart: returns a chart spec rendered in the UI.
  Use for: explicit visual requests ("plot", "chart", "show me a graph"), or when a
  trend over many time periods is genuinely clearer as a picture.
- web_search: looks up information on the public web.
  Use ONLY for context that cannot come from the dataset — definitions, market events,
  external benchmarks. NEVER use it for anything the dataset can answer.

## Choosing a route
- "direct_answer": greetings, small talk, questions about what you can do. No tools.
- "tools": anything answerable from the dataset, or needing genuine external context.
- "unsupported": the request is outside what your tools can reach — taking actions,
  accessing live or personal systems, data not in this dataset, advice unrelated to it.
  Choose this rather than guessing. Refusing correctly is better than inventing a number.

## Rules
1. Pick the FEWEST tools that answer the question. Do not call all of them.
2. If a step's arguments depend on an earlier step's output, leave its `args` empty —
   it will be filled in once the earlier result exists.
3. Never invent a column name. Use only columns listed in the dataset profile above.
4. Relative time phrases ("last quarter", "recently") resolve against the dataset's own
   date range, not today's calendar. Record that in `assumptions`.
5. If the question is ambiguous but reasonably answerable, pick the most likely reading,
   state it in `assumptions`, and proceed. Do not stall on clarification.
6. tool_plan MUST be empty when route is not "tools".

## Conversation so far
{history}

Plan for this question."""
```

Point 5 matters more than it looks. An agent that asks a clarifying question on every vague input demos badly. Assume, state the assumption, answer.

---

## 4. The node (`src/nodes.py`)

```python
from langchain_core.messages import SystemMessage, HumanMessage
from src.config import get_llm, PLANNER_MODEL
from src.prompts import PLANNER_SYSTEM
from src.schema import get_dataset_profile
from src.models import PlanModel
from src.state import AgentState


def _format_history(messages: list, limit: int = 6) -> str:
    """Recent turns only — the planner needs context, not the full transcript."""
    if not messages:
        return "(no prior turns)"
    recent = messages[-limit:]
    return "\n".join(
        f"{'User' if m.type == 'human' else 'Assistant'}: {m.content}" for m in recent
    )


def planner_node(state: AgentState) -> dict:
    """Decide the route and the tool plan. Runs before any tool executes."""
    query = state["user_query"]

    llm = get_llm(PLANNER_MODEL, temperature=0.0).with_structured_output(PlanModel)

    system = PLANNER_SYSTEM.format(
        dataset_profile=get_dataset_profile(as_text=True),
        history=_format_history(state.get("messages", [])),
    )

    try:
        plan: PlanModel = llm.invoke(
            [SystemMessage(content=system), HumanMessage(content=query)]
        )
    except Exception as exc:
        return {
            "error": f"planner_failed: {exc}",
            "route": "unsupported",
            "reasoning_trace": [
                {
                    "stage": "error",
                    "title": "Planning failed",
                    "detail": str(exc)[:300],
                    "payload": None,
                }
            ],
        }

    # Enforce the invariant the model might violate.
    tool_plan = [tc.model_dump() for tc in plan.tool_plan] if plan.route == "tools" else []

    detail = plan.rationale
    if plan.assumptions:
        detail += "\n\nAssumptions: " + "; ".join(plan.assumptions)

    return {
        "plan": plan.rationale,
        "route": plan.route,
        "tool_plan": tool_plan,
        "iterations": 0,
        "reasoning_trace": [
            {
                "stage": "plan",
                "title": f"Plan — routing to '{plan.route}'",
                "detail": detail,
                "payload": {
                    "tools_selected": [tc.tool for tc in plan.tool_plan],
                    "assumptions": plan.assumptions,
                },
            }
        ],
    }
```

The post-validation on line `tool_plan = [...] if plan.route == "tools"` is not paranoia — models routinely fill a tool plan while routing to `direct_answer`. Enforce invariants in code, never in the prompt alone.

---

## 5. The router (`src/routers.py`)

```python
from typing import Literal
from src.state import AgentState


def route_after_plan(state: AgentState) -> Literal["tools", "direct_answer", "unsupported"]:
    if state.get("error"):
        return "unsupported"
    route = state.get("route", "unsupported")
    # A 'tools' route with nothing to run is a planning failure, not a tool path.
    if route == "tools" and not state.get("tool_plan"):
        return "direct_answer"
    return route
```

---

## 6. Dataset profile (`src/schema.py`) — the other half of routing quality

The planner is only as good as what it knows about the data. Don't hand it a bare column list.

```python
def get_dataset_profile(as_text: bool = False):
    df = load_data()
    profile = {
        "rows": len(df),
        "date_range": [str(df["Order Date"].min().date()),
                       str(df["Order Date"].max().date())],
        "columns": {c: str(df[c].dtype) for c in df.columns},
        "categorical_values": {
            c: sorted(df[c].dropna().unique().tolist())
            for c in ["Region", "Category", "Sub-Category", "Segment", "Ship Mode"]
            if c in df.columns and df[c].nunique() <= 30
        },
        "numeric_columns": ["Sales", "Profit", "Quantity", "Discount"],
    }
    if not as_text:
        return profile
    ...  # render as compact markdown
```

Listing the **actual distinct values** of `Region` and `Category` is what stops the agent planning a filter for `Region == "Europe"` when the data says `"EMEA"`. Cache it — it's computed once per session.

---

## 7. Verify before building anything else

`scripts/smoke_test.py`:

```python
CASES = [
    ("hi there",                                          "direct_answer", 0),
    ("what can you do?",                                  "direct_answer", 0),
    ("What were the top 3 products by revenue last quarter?", "tools",     1),
    ("Compare APAC and EMEA and tell me what's driving it",   "tools",     2),
    ("Plot monthly sales for 2014",                       "tools",         2),
    ("Is there a seasonal trend in furniture sales?",      "tools",        2),
    ("Book me a flight to Delhi",                          "unsupported",  0),
    ("asdkjfh",                                            "unsupported",  0),
]
```

Run each through `planner_node` alone — no graph, no tools — and print route, tool names, and rationale.

**Gate: do not write a single line of tool code until at least 7 of 8 land correctly.** If "hi there" plans a `query_data` call, or the flight booking routes to `tools`, the fix is in the prompt or the field descriptions, and it is far cheaper to fix now than after four tools and a UI are sitting on top of it.

Expected failure modes and where to fix them:
| Symptom | Fix |
|---|---|
| Everything routes to `tools` | Sharpen the `direct_answer` / `unsupported` descriptions in the route field; add 2–3 few-shot examples to the prompt |
| Plans 3–4 tools for simple questions | Strengthen Rule 1; add "one tool is the common case" to the `tool_plan` field description |
| `why` fields are generic ("to get the data") | Tighten the `ToolCall.why` description to demand it reference the user's actual words |
| Invents column names | Dataset profile isn't reaching the prompt, or `categorical_values` is empty — print the rendered system prompt and look |

# Insight Copilot — Tool Specifications

Four tools. The brief requires three; four gives you headroom to drop one and still pass.

**Core design rule:** tools take **structured parameters**, not free-form code or SQL strings. An LLM writing `df.query()` strings fails on quoting, dates, and column-name drift. An LLM filling a Pydantic schema fails loudly and recoverably.

Every tool returns the same envelope:

```python
class ToolResult(TypedDict):
    ok: bool
    data: Any            # records, dict of metrics, or chart spec
    summary: str         # one-line natural-language summary for the LLM
    meta: dict           # rows_returned, columns_used, filters_applied
    error: str | None
```

The `summary` field matters more than it looks: the synthesizer reads it first, so a good summary produces a good final answer.

---

## Tool 1 — `query_data`

Slice, filter, group, and aggregate the dataset. This is the workhorse.

```python
class QueryDataArgs(BaseModel):
    filters: list[Filter] = []          # [{column, op, value}]
    group_by: list[str] = []            # e.g. ["Region"] or ["order_year", "Category"]
    metrics: list[Metric] = []          # [{column: "Sales", agg: "sum"}]
    sort_by: str | None = None
    ascending: bool = False
    limit: int = 20

class Filter(BaseModel):
    column: str
    op: Literal["==", "!=", ">", ">=", "<", "<=", "in", "between", "contains"]
    value: Any

class Metric(BaseModel):
    column: str
    agg: Literal["sum", "mean", "median", "count", "nunique", "min", "max"]
```

Implementation requirements:
- **Validate column names against the real dataframe** before executing. Unknown column → `ok=False` with a message listing the closest valid names. The agent can then re-plan instead of hallucinating.
- Cap `limit` at 100 server-side regardless of what the LLM asks for.
- Return records as `list[dict]`, not a DataFrame — must be JSON-serializable for state.
- `summary` example: `"Sales summed by Region for 2014, 4 groups, top value APAC at $1.2M."`

---

## Tool 2 — `compute_metrics`

Derived analytics on top of a previous `query_data` result, or on a fresh slice.

```python
class ComputeMetricsArgs(BaseModel):
    operation: Literal[
        "growth_rate",       # period-over-period % change
        "share_of_total",    # each group's % of total
        "descriptive_stats", # mean, median, std, min, max, quartiles
        "correlation",       # between two numeric columns
        "outliers",          # IQR or z-score flagging
        "trend",             # slope + direction over a date column
        "seasonality",       # mean by month/quarter + coefficient of variation
    ]
    data_ref: int | None = None   # index into tool_results to reuse a prior query
    column: str | None = None
    group_by: list[str] = []
    date_column: str | None = None
    period: Literal["month", "quarter", "year"] | None = None
```

Implementation requirements:
- `data_ref` is what enables genuine tool chaining. When set, operate on `state["tool_results"][data_ref]["data"]` instead of hitting the raw dataframe again.
- `seasonality`: compute mean per month across years, then report the coefficient of variation. A CV above ~0.15 is worth calling a seasonal pattern; below that, say there isn't one. **Being able to say "no meaningful seasonality" is a scoring opportunity.**
- `outliers`: IQR method, return the flagged rows with the metric value and how far outside the fence they sit.
- `summary` must state the finding, not just that a calculation happened: `"Q4 revenue grew 34% over Q3; largest jump in the series."`

---

## Tool 3 — `make_chart`

Returns a **spec**, never an image. The UI renders it.

```python
class MakeChartArgs(BaseModel):
    chart_type: Literal["line", "bar", "scatter", "area"]
    data_ref: int | None = None
    x: str
    y: str
    color: str | None = None     # series/grouping column
    title: str
```

Implementation requirements:
- Return a Plotly figure dict or a Vega-Lite spec. Plotly is simpler with Streamlit (`st.plotly_chart`).
- Store it in `state["chart_spec"]`, not in the message text.
- The tool must still return a `summary` describing what the chart shows, so the synthesizer can write about it in prose. A chart with no accompanying insight is a data dump.
- If `x` is a date column with more than ~200 points, resample to monthly before plotting.

---

## Tool 4 — `web_search`

For context the dataset can't supply — market conditions, what a term means, external events.

```python
class WebSearchArgs(BaseModel):
    query: str
    max_results: int = 3
```

Implementation:
- Tavily free tier or DuckDuckGo (`ddgs` package, no key needed — the safer choice for a 5-day build with no billing).
- Return title, snippet, URL for each result.
- The planner should route here **only** when the question needs outside context. "What were top products?" must never trigger a search. Make this explicit in the planner prompt.

---

## The fifth "tool": no tool

Not a tool — a routing outcome. The `unsupported` node.

The brief awards "bonus points for gracefully saying 'I don't have a tool for that' rather than hallucinating." So make it a first-class path and demo it. The response should name the limitation and redirect:

> I can't answer that — my tools only reach the Global Superstore sales data (orders, products, regions, 2011–2014) plus general web lookup. I can't book anything or access live systems. I could tell you which product categories grew fastest in that period, if that's useful.

---

## Tool docstrings are prompts

Whatever provider you bind tools with, the docstring is what the LLM reads when deciding. Write them for the model, not for a human maintainer:

```python
@tool(args_schema=QueryDataArgs)
def query_data(...) -> ToolResult:
    """Filter, group and aggregate the Global Superstore sales dataset.

    USE WHEN: the question asks for numbers from the dataset — totals,
    top-N rankings, breakdowns by region/category/segment, or a filtered slice.

    DO NOT USE WHEN: the question asks for a derived analysis like growth rate,
    correlation or outliers (use compute_metrics), or for a visual (use make_chart).

    Returns records plus a one-line summary.
    """
```

The `USE WHEN` / `DO NOT USE WHEN` pattern measurably improves selection accuracy and is cheap to add. Apply it to all four.

from typing import TypedDict, Any, Literal
from pydantic import BaseModel, Field

class ToolResult(TypedDict):
    ok: bool
    data: Any            # records (list[dict]), dict of metrics, or chart spec (dict)
    summary: str         # one-line natural-language summary for the LLM synthesizer
    meta: dict[str, Any] # rows_returned, columns_used, filters_applied, etc.
    error: str | None

from .query_data import query_data, QueryDataArgs, Filter, Metric
from .compute_metrics import compute_metrics, ComputeMetricsArgs
from .make_chart import make_chart, MakeChartArgs
from .web_search import web_search, WebSearchArgs

__all__ = [
    "ToolResult",
    "query_data",
    "QueryDataArgs",
    "Filter",
    "Metric",
    "compute_metrics",
    "ComputeMetricsArgs",
    "make_chart",
    "MakeChartArgs",
    "web_search",
    "WebSearchArgs",
]

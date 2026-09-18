import difflib
import logging
from typing import Literal, Any
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from ..data import get_dataset
from . import ToolResult

logger = logging.getLogger("insight_copilot.tools.query_data")


class Filter(BaseModel):
    column: str = Field(description="Column name to filter on")
    op: Literal["==", "!=", ">", ">=", "<", "<=", "in", "between", "contains"] = Field(
        description="Comparison operator"
    )
    value: Any = Field(description="Value to compare against")


class Metric(BaseModel):
    column: str = Field(description="Column name to aggregate")
    agg: Literal["sum", "mean", "median", "count", "nunique", "min", "max"] = Field(
        default="sum", description="Aggregation function"
    )


class QueryDataArgs(BaseModel):
    filters: list[Filter] = Field(default_factory=list, description="Filter conditions to apply")
    group_by: list[str] = Field(default_factory=list, description="Columns to group by")
    metrics: list[Metric] = Field(default_factory=list, description="Metrics to calculate")
    sort_by: str | None = Field(default=None, description="Column to sort results by")
    ascending: bool = Field(default=False, description="Sort direction: False for descending, True for ascending")
    limit: int = Field(default=20, description="Max rows to return (capped at 100)")


def _validate_column(col: str, valid_cols: list[str]) -> str | None:
    """
    Returns None if valid, or error message with suggestions if invalid.
    """
    if col in valid_cols:
        return None
    matches = difflib.get_close_matches(col, valid_cols, n=3, cutoff=0.4)
    suggestion = f" Did you mean: {', '.join(matches)}?" if matches else ""
    return f"Column '{col}' does not exist in dataset.{suggestion} Valid columns: {', '.join(valid_cols[:10])}..."


def _clean_json_record(record: dict[str, Any]) -> dict[str, Any]:
    """
    Sanitizes values for JSON serialization (handles NaN, pd.Timestamp, numpy types).
    """
    clean = {}
    for k, v in record.items():
        if pd.isna(v) or v is None:
            clean[k] = None
        elif isinstance(v, (pd.Timestamp, np.datetime64)):
            clean[k] = str(v)[:10] if pd.notna(v) else None
        elif isinstance(v, (np.floating, float)):
            clean[k] = round(float(v), 2)
        elif isinstance(v, (np.integer, int)):
            clean[k] = int(v)
        elif isinstance(v, (np.ndarray, list)):
            clean[k] = list(v)
        else:
            clean[k] = str(v)
    return clean


def query_data(args: QueryDataArgs | dict[str, Any], df: pd.DataFrame | None = None) -> ToolResult:
    """
    Filter, group and aggregate the dataset.

    USE WHEN: the question asks for numbers from the dataset — totals,
    top-N rankings, breakdowns by region/category/state, or a filtered slice.

    DO NOT USE WHEN: the question asks for a derived analysis like growth rate,
    correlation or outliers (use compute_metrics), or for a visual (use make_chart).

    Returns records plus an informative summary for the synthesizer.
    """
    if isinstance(args, dict):
        args = QueryDataArgs(**args)

    if df is None:
        df = get_dataset()

    valid_cols = list(df.columns)

    # 1. Validate requested columns
    for f in args.filters:
        err = _validate_column(f.column, valid_cols)
        if err:
            return {
                "ok": False,
                "data": [],
                "summary": f"Query failed: {err}",
                "meta": {"valid_columns": valid_cols},
                "error": err,
            }

    for col in args.group_by:
        err = _validate_column(col, valid_cols)
        if err:
            return {
                "ok": False,
                "data": [],
                "summary": f"Query failed: {err}",
                "meta": {"valid_columns": valid_cols},
                "error": err,
            }

    for m in args.metrics:
        err = _validate_column(m.column, valid_cols)
        if err:
            return {
                "ok": False,
                "data": [],
                "summary": f"Query failed: {err}",
                "meta": {"valid_columns": valid_cols},
                "error": err,
            }

    # 2. Apply Filters
    sub_df = df
    applied_filters = []
    for f in args.filters:
        col = f.column
        op = f.op
        val = f.value

        try:
            # Handle type compatibility
            if pd.api.types.is_numeric_dtype(sub_df[col]):
                if isinstance(val, (list, tuple)):
                    val = [float(x) for x in val]
                elif val is not None and not isinstance(val, (int, float)):
                    try:
                        val = float(val)
                    except ValueError:
                        pass

            if op == "==":
                sub_df = sub_df[sub_df[col] == val]
            elif op == "!=":
                sub_df = sub_df[sub_df[col] != val]
            elif op == ">":
                sub_df = sub_df[sub_df[col] > val]
            elif op == ">=":
                sub_df = sub_df[sub_df[col] >= val]
            elif op == "<":
                sub_df = sub_df[sub_df[col] < val]
            elif op == "<=":
                sub_df = sub_df[sub_df[col] <= val]
            elif op == "in":
                if isinstance(val, (list, tuple, set)):
                    sub_df = sub_df[sub_df[col].isin(val)]
                else:
                    sub_df = sub_df[sub_df[col].isin([val])]
            elif op == "between":
                if isinstance(val, (list, tuple)) and len(val) >= 2:
                    sub_df = sub_df[(sub_df[col] >= val[0]) & (sub_df[col] <= val[1])]
            elif op == "contains":
                sub_df = sub_df[sub_df[col].astype(str).str.contains(str(val), case=False, na=False)]
            applied_filters.append(f"{col} {op} {val}")
        except Exception as filter_err:
            logger.warning(f"Filter error on {col} {op} {val}: {filter_err}")

    # 3. Aggregation or Slice
    limit = min(max(1, args.limit), 100)

    if args.group_by and args.metrics:
        agg_dict = {}
        col_rename = {}
        for m in args.metrics:
            agg_dict[m.column] = m.agg
            col_rename[m.column] = f"{m.column}_{m.agg}" if len(args.metrics) > 1 or m.column in args.group_by else m.column

        grouped = sub_df.groupby(args.group_by, observed=True).agg({m.column: m.agg for m in args.metrics}).reset_index()
        
        # Sort
        sort_col = args.sort_by
        if not sort_col:
            sort_col = args.metrics[0].column
        if sort_col in grouped.columns:
            grouped = grouped.sort_values(by=sort_col, ascending=args.ascending)

        result_df = grouped.head(limit)
        records = [_clean_json_record(r) for r in result_df.to_dict(orient="records")]

        # Generate insightful summary
        top_row = records[0] if records else {}
        top_group_val = " / ".join([str(top_row.get(g, "")) for g in args.group_by]) if top_row else "None"
        first_metric = args.metrics[0].column
        top_metric_val = top_row.get(first_metric, 0) if top_row else 0
        summary = (
            f"Aggregated {len(args.metrics)} metric(s) grouped by {', '.join(args.group_by)}. "
            f"Total groups: {len(grouped):,}. Top group: '{top_group_val}' with {first_metric}={top_metric_val:,.2f} "
            f"({applied_filters if applied_filters else 'no filters'})."
        )

    elif args.metrics and not args.group_by:
        agg_dict = {m.column: m.agg for m in args.metrics}
        computed = {}
        for m in args.metrics:
            val = sub_df[m.column].agg(m.agg)
            key = f"{m.column}_{m.agg}" if len(args.metrics) > 1 else m.column
            computed[key] = round(float(val), 2) if isinstance(val, (int, float, np.number)) else val
        records = [_clean_json_record(computed)]
        summary = (
            f"Calculated {len(args.metrics)} metric(s) over {len(sub_df):,} matching rows: "
            + ", ".join([f"{k}={v}" for k, v in computed.items()])
        )

    elif args.group_by and not args.metrics:
        counts = sub_df.groupby(args.group_by, observed=True).size().reset_index(name="count")
        counts = counts.sort_values(by="count", ascending=args.ascending).head(limit)
        records = [_clean_json_record(r) for r in counts.to_dict(orient="records")]
        summary = f"Grouped by {', '.join(args.group_by)}. Found {len(counts)} groups (showing top {len(records)})."

    else:
        # Sliced records
        if args.sort_by and args.sort_by in sub_df.columns:
            sub_df = sub_df.sort_values(by=args.sort_by, ascending=args.ascending)
        result_df = sub_df.head(limit)
        records = [_clean_json_record(r) for r in result_df.to_dict(orient="records")]
        summary = f"Retrieved {len(records):,} records matching filters ({', '.join(applied_filters) if applied_filters else 'unfiltered'})."

    return {
        "ok": True,
        "data": records,
        "summary": summary,
        "meta": {
            "rows_returned": len(records),
            "columns_used": args.group_by + [m.column for m in args.metrics],
            "filters_applied": applied_filters,
            "limit": limit,
        },
        "error": None,
    }

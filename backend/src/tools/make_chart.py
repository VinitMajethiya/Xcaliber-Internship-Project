import logging
from typing import Literal, Any
import numpy as np
import pandas as pd
import plotly.express as px
from pydantic import BaseModel, Field

from ..data import get_dataset
from . import ToolResult

logger = logging.getLogger("insight_copilot.tools.make_chart")


class MakeChartArgs(BaseModel):
    chart_type: Literal["line", "bar", "scatter", "area"] = Field(
        description="Type of chart to generate"
    )
    data_ref: int | None = Field(
        default=None, description="Index into prior tool_results to use as chart data source"
    )
    x: str = Field(description="Column name for the X-axis")
    y: str = Field(description="Column name for the Y-axis")
    color: str | None = Field(
        default=None, description="Optional column name for color segmentation/grouping"
    )
    title: str = Field(description="Clear, executive-ready title for the chart")


def make_chart(
    args: MakeChartArgs | dict[str, Any],
    prior_results: list[dict[str, Any]] | None = None,
    df: pd.DataFrame | None = None,
) -> ToolResult:
    """
    Generates an interactive Plotly chart specification (spec dictionary, not an image).

    USE WHEN: the question requests a plot, chart, visualization, visual distribution,
    or visual comparison over time or categories.

    DO NOT USE WHEN: the user only asked for numeric tables or text summaries.
    """
    if isinstance(args, dict):
        args = MakeChartArgs(**args)

    # 1. Resolve source data
    if args.data_ref is not None and prior_results and 0 <= args.data_ref < len(prior_results):
        ref_data = prior_results[args.data_ref].get("data")
        if isinstance(ref_data, list) and len(ref_data) > 0 and isinstance(ref_data[0], dict):
            chart_df = pd.DataFrame(ref_data)
        else:
            chart_df = df if df is not None else get_dataset()
    else:
        chart_df = df if df is not None else get_dataset()

    if chart_df.empty:
        return {
            "ok": False,
            "data": {},
            "summary": "Cannot create chart: dataset is empty.",
            "meta": {"chart_type": args.chart_type},
            "error": "Dataset is empty",
        }

    # 2. Validate columns
    valid_cols = list(chart_df.columns)
    for col_name, label in [(args.x, "X-axis"), (args.y, "Y-axis")]:
        if col_name not in valid_cols:
            return {
                "ok": False,
                "data": {},
                "summary": f"Chart error: {label} column '{col_name}' was not found.",
                "meta": {"valid_columns": valid_cols},
                "error": f"Column '{col_name}' not in dataset",
            }

    if args.color and args.color not in valid_cols:
        args.color = None

    plot_df = chart_df.copy()

    # 3. Downsample / aggregate if X is a dense date column (> 200 points)
    if pd.api.types.is_datetime64_any_dtype(plot_df[args.x]) or "date" in args.x.lower() or "timestamp" in args.x.lower():
        try:
            plot_df[args.x] = pd.to_datetime(plot_df[args.x], errors="coerce")
            plot_df = plot_df.dropna(subset=[args.x])
            if len(plot_df) > 200:
                # Resample monthly
                plot_df["month_period"] = plot_df[args.x].dt.to_period("M").dt.to_timestamp()
                grp_cols = ["month_period"]
                if args.color and args.color in plot_df.columns:
                    grp_cols.append(args.color)
                plot_df = plot_df.groupby(grp_cols, observed=True)[args.y].sum().reset_index()
                args.x = "month_period"
        except Exception as date_e:
            logger.warning(f"Could not resample date column for chart: {date_e}")

    # Cap rows for snappy chart rendering
    if len(plot_df) > 500:
        plot_df = plot_df.head(500)

    # 4. Generate Plotly figure
    try:
        if args.chart_type == "line":
            fig = px.line(plot_df, x=args.x, y=args.y, color=args.color, title=args.title)
        elif args.chart_type == "bar":
            fig = px.bar(plot_df, x=args.x, y=args.y, color=args.color, title=args.title)
        elif args.chart_type == "scatter":
            fig = px.scatter(plot_df, x=args.x, y=args.y, color=args.color, title=args.title)
        elif args.chart_type == "area":
            fig = px.area(plot_df, x=args.x, y=args.y, color=args.color, title=args.title)
        else:
            fig = px.bar(plot_df, x=args.x, y=args.y, color=args.color, title=args.title)

        # Apply clean, premium dark-mode theme
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(15, 23, 42, 0)",
            plot_bgcolor="rgba(15, 23, 42, 0.4)",
            margin=dict(l=40, r=40, t=50, b=40),
            font=dict(family="Inter, system-ui, sans-serif", size=12, color="#94A3B8"),
            title=dict(font=dict(size=15, color="#F8FAFC")),
            hovermode="closest",
        )
        fig.update_xaxes(showgrid=True, gridcolor="rgba(148, 163, 184, 0.1)")
        fig.update_yaxes(showgrid=True, gridcolor="rgba(148, 163, 184, 0.1)")

        import json as _json
        chart_dict = _json.loads(fig.to_json())

        # Build informative summary
        max_y = plot_df[args.y].max() if pd.api.types.is_numeric_dtype(plot_df[args.y]) else "N/A"
        summary = (
            f"Generated {args.chart_type} chart '{args.title}' with {len(plot_df):,} points "
            f"mapping '{args.y}' across '{args.x}'"
            f"{f' segmented by {args.color}' if args.color else ''}."
        )

        return {
            "ok": True,
            "data": chart_dict,
            "summary": summary,
            "meta": {
                "chart_type": args.chart_type,
                "x": args.x,
                "y": args.y,
                "points_rendered": len(plot_df),
                "title": args.title,
            },
            "error": None,
        }

    except Exception as e:
        logger.error(f"Failed to generate {args.chart_type} chart: {e}", exc_info=True)
        return {
            "ok": False,
            "data": {},
            "summary": f"Failed to build chart: {str(e)}",
            "meta": {"chart_type": args.chart_type},
            "error": str(e),
        }

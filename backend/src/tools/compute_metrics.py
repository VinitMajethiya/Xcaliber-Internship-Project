import logging
from typing import Literal, Any
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from ..data import get_dataset
from . import ToolResult

logger = logging.getLogger("insight_copilot.tools.compute_metrics")


class ComputeMetricsArgs(BaseModel):
    operation: Literal[
        "growth_rate",
        "share_of_total",
        "descriptive_stats",
        "correlation",
        "outliers",
        "trend",
        "seasonality",
    ] = Field(description="Analytical computation to perform")
    data_ref: int | None = Field(
        default=None, description="Index into prior tool_results to analyze previous output"
    )
    column: str | None = Field(default=None, description="Primary column to analyze")
    second_column: str | None = Field(
        default=None, description="Second numeric column for correlation analysis"
    )
    group_by: list[str] = Field(
        default_factory=list, description="Categorical or date column to group by"
    )
    date_column: str | None = Field(default=None, description="Date column for time series")
    period: Literal["month", "quarter", "year"] | None = Field(
        default=None, description="Time aggregation period"
    )


def compute_metrics(
    args: ComputeMetricsArgs | dict[str, Any],
    prior_results: list[dict[str, Any]] | None = None,
    df: pd.DataFrame | None = None,
) -> ToolResult:
    """
    Derived analytics on top of a previous query_data result, or on the raw dataset.

    USE WHEN: the question asks for growth rates, share of total (percentages),
    descriptive statistics (mean, median, IQR), correlation between metrics,
    anomaly/outlier detection, time series trends, or seasonal patterns.

    DO NOT USE WHEN: the question only needs raw data filtering, grouping or totals
    (use query_data first).
    """
    if isinstance(args, dict):
        args = ComputeMetricsArgs(**args)

    # 1. Resolve source dataframe
    source_label = "raw dataset"
    if args.data_ref is not None and prior_results and 0 <= args.data_ref < len(prior_results):
        ref_data = prior_results[args.data_ref].get("data")
        if isinstance(ref_data, list) and len(ref_data) > 0 and isinstance(ref_data[0], dict):
            work_df = pd.DataFrame(ref_data)
            source_label = f"prior result (data_ref={args.data_ref})"
        else:
            work_df = df if df is not None else get_dataset()
    else:
        work_df = df if df is not None else get_dataset()

    if work_df.empty:
        return {
            "ok": False,
            "data": {},
            "summary": "Cannot compute metrics: dataset / prior result is empty.",
            "meta": {"operation": args.operation},
            "error": "Dataset is empty",
        }

    # Identify numeric columns
    numeric_cols = [c for c in work_df.columns if pd.api.types.is_numeric_dtype(work_df[c])]
    target_col = args.column
    if not target_col or target_col not in work_df.columns:
        if numeric_cols:
            target_col = numeric_cols[0]
        else:
            return {
                "ok": False,
                "data": {},
                "summary": f"No numeric column available for operation '{args.operation}'.",
                "meta": {"columns": list(work_df.columns)},
                "error": "No numeric column found",
            }

    op = args.operation

    try:
        # ==========================================
        # 1. SHARE OF TOTAL
        # ==========================================
        if op == "share_of_total":
            total_sum = work_df[target_col].sum()
            if total_sum == 0:
                share_pct = np.zeros(len(work_df))
            else:
                share_pct = (work_df[target_col] / total_sum * 100).round(2)

            res_df = work_df.copy()
            res_df["share_pct"] = share_pct
            res_df = res_df.sort_values(by="share_pct", ascending=False)
            records = res_df.head(20).to_dict(orient="records")

            top_row = records[0] if records else {}
            group_col = args.group_by[0] if args.group_by and args.group_by[0] in work_df.columns else (
                [c for c in work_df.columns if c != target_col and c != "share_pct"][0]
                if len(work_df.columns) > 1 else target_col
            )
            top_name = top_row.get(group_col, "Top group")
            top_share = top_row.get("share_pct", 0)

            summary = (
                f"Computed share of total for '{target_col}'. "
                f"Leading segment is '{top_name}' contributing {top_share:.1f}% of overall {target_col} "
                f"across {len(res_df):,} groups."
            )
            return {
                "ok": True,
                "data": records,
                "summary": summary,
                "meta": {"operation": op, "target_column": target_col, "total_sum": round(float(total_sum), 2)},
                "error": None,
            }

        # ==========================================
        # 2. GROWTH RATE
        # ==========================================
        elif op == "growth_rate":
            # Determine ordering column
            order_col = args.date_column
            if not order_col or order_col not in work_df.columns:
                date_candidates = [c for c in work_df.columns if "date" in c.lower() or "year" in c.lower() or "month" in c.lower()]
                order_col = date_candidates[0] if date_candidates else work_df.columns[0]

            sorted_df = work_df.sort_values(by=order_col).copy()
            sorted_df["growth_rate_pct"] = (sorted_df[target_col].pct_change() * 100).round(2)
            records = sorted_df.to_dict(orient="records")

            valid_growth = sorted_df["growth_rate_pct"].dropna()
            if not valid_growth.empty:
                latest_growth = valid_growth.iloc[-1]
                max_jump = valid_growth.max()
                min_drop = valid_growth.min()
                avg_growth = valid_growth.mean()
                summary = (
                    f"Growth rate for '{target_col}' along '{order_col}': Latest period changed by {latest_growth:+.1f}%. "
                    f"Average period growth is {avg_growth:+.1f}% (Peak jump: {max_jump:+.1f}%, Lowest: {min_drop:+.1f}%)."
                )
            else:
                summary = f"Insufficient periods to calculate growth rate for '{target_col}'."

            return {
                "ok": True,
                "data": records,
                "summary": summary,
                "meta": {"operation": op, "target_column": target_col, "order_col": order_col},
                "error": None,
            }

        # ==========================================
        # 3. DESCRIPTIVE STATS
        # ==========================================
        elif op == "descriptive_stats":
            series = work_df[target_col].dropna().astype(float)
            q25 = float(series.quantile(0.25))
            q75 = float(series.quantile(0.75))
            iqr = round(q75 - q25, 2)
            stats = {
                "column": target_col,
                "count": int(series.count()),
                "mean": round(float(series.mean()), 2),
                "std": round(float(series.std()), 2) if series.count() > 1 else 0.0,
                "median": round(float(series.median()), 2),
                "min": round(float(series.min()), 2),
                "max": round(float(series.max()), 2),
                "q25": round(q25, 2),
                "q75": round(q75, 2),
                "iqr": iqr,
            }
            summary = (
                f"Descriptive statistics for '{target_col}': Mean={stats['mean']:,.2f}, Median={stats['median']:,.2f}, "
                f"StdDev={stats['std']:,.2f}, IQR={stats['iqr']:,.2f} (Range: {stats['min']:,.2f} to {stats['max']:,.2f})."
            )
            return {
                "ok": True,
                "data": stats,
                "summary": summary,
                "meta": {"operation": op, "target_column": target_col},
                "error": None,
            }

        # ==========================================
        # 4. CORRELATION
        # ==========================================
        elif op == "correlation":
            col2 = args.second_column
            if not col2 or col2 not in work_df.columns:
                other_numerics = [c for c in numeric_cols if c != target_col]
                col2 = other_numerics[0] if other_numerics else None

            if not col2:
                return {
                    "ok": False,
                    "data": {},
                    "summary": f"Correlation requires a second numeric column.",
                    "meta": {"numeric_columns": numeric_cols},
                    "error": "Missing second column",
                }

            clean_pair = work_df[[target_col, col2]].dropna()
            r_val = float(clean_pair[target_col].corr(clean_pair[col2]))
            r_val_rounded = round(r_val, 3)

            # Verbal interpretation
            abs_r = abs(r_val)
            if abs_r >= 0.7:
                strength = "strong"
            elif abs_r >= 0.35:
                strength = "moderate"
            elif abs_r >= 0.15:
                strength = "weak"
            else:
                strength = "negligible / no"

            direction = "positive" if r_val >= 0 else "negative"
            summary = (
                f"Correlation between '{target_col}' and '{col2}' is r = {r_val_rounded} ({strength} {direction} correlation) "
                f"based on {len(clean_pair):,} observations."
            )
            return {
                "ok": True,
                "data": {"col1": target_col, "col2": col2, "pearson_r": r_val_rounded, "strength": strength, "direction": direction},
                "summary": summary,
                "meta": {"operation": op, "sample_size": len(clean_pair)},
                "error": None,
            }

        # ==========================================
        # 5. OUTLIERS (IQR METHOD)
        # ==========================================
        elif op == "outliers":
            series = work_df[target_col].dropna().astype(float)
            q1 = float(series.quantile(0.25))
            q3 = float(series.quantile(0.75))
            iqr = q3 - q1
            lower_fence = q1 - 1.5 * iqr
            upper_fence = q3 + 1.5 * iqr

            outlier_mask = (work_df[target_col] < lower_fence) | (work_df[target_col] > upper_fence)
            outlier_df = work_df[outlier_mask].copy()
            outlier_df["distance_outside_fence"] = np.where(
                outlier_df[target_col] > upper_fence,
                outlier_df[target_col] - upper_fence,
                lower_fence - outlier_df[target_col],
            ).round(2)

            outlier_df = outlier_df.sort_values(by="distance_outside_fence", ascending=False)
            records = outlier_df.head(20).to_dict(orient="records")

            total_outliers = int(outlier_mask.sum())
            max_val = float(series.max()) if not series.empty else 0.0
            summary = (
                f"Identified {total_outliers:,} outliers in '{target_col}' using IQR method "
                f"(Fence: [{lower_fence:,.2f}, {upper_fence:,.2f}]). "
                f"Maximum outlier is {max_val:,.2f} ({total_outliers/len(work_df)*100:.1f}% of rows flagged)."
            )
            return {
                "ok": True,
                "data": records,
                "summary": summary,
                "meta": {
                    "operation": op,
                    "target_column": target_col,
                    "lower_fence": round(lower_fence, 2),
                    "upper_fence": round(upper_fence, 2),
                    "outliers_count": total_outliers,
                },
                "error": None,
            }

        # ==========================================
        # 6. TREND (SLOPE & DIRECTION)
        # ==========================================
        elif op == "trend":
            order_col = args.date_column
            if not order_col or order_col not in work_df.columns:
                date_candidates = [c for c in work_df.columns if "date" in c.lower() or "year" in c.lower() or "month" in c.lower()]
                order_col = date_candidates[0] if date_candidates else work_df.columns[0]

            sorted_df = work_df.sort_values(by=order_col).dropna(subset=[target_col]).copy()
            n = len(sorted_df)
            if n < 2:
                return {
                    "ok": False,
                    "data": {},
                    "summary": f"Not enough time periods ({n}) to compute a trend line.",
                    "meta": {"operation": op},
                    "error": "Insufficient data points for trend",
                }

            x = np.arange(n)
            y = sorted_df[target_col].values.astype(float)
            slope, intercept = np.polyfit(x, y, 1)
            first_val = y[0]
            last_val = y[-1]
            pct_change = ((last_val - first_val) / first_val * 100) if first_val != 0 else 0.0

            if abs(slope) < 0.01 or abs(pct_change) < 2.0:
                direction = "flat / stable"
            elif slope > 0:
                direction = "upward growth"
            else:
                direction = "downward contraction"

            summary = (
                f"Trend analysis for '{target_col}' over {n} points: {direction.capitalize()} "
                f"(slope={slope:+.2f}/period, total shift of {pct_change:+.1f}% from start to end)."
            )
            return {
                "ok": True,
                "data": {
                    "direction": direction,
                    "slope": round(float(slope), 3),
                    "pct_change": round(float(pct_change), 2),
                    "first_value": round(float(first_val), 2),
                    "last_value": round(float(last_val), 2),
                },
                "summary": summary,
                "meta": {"operation": op, "target_column": target_col, "periods_analyzed": n},
                "error": None,
            }

        # ==========================================
        # 7. SEASONALITY (COEFFICIENT OF VARIATION)
        # ==========================================
        elif op == "seasonality":
            # Check for month or quarter column or timestamp
            season_col = None
            for c in ["order_month", "Month", "month", "order_quarter", "Quarter", "quarter"]:
                if c in work_df.columns:
                    season_col = c
                    break

            if not season_col and "order_purchase_timestamp" in work_df.columns:
                dt_series = pd.to_datetime(work_df["order_purchase_timestamp"], errors="coerce")
                work_df = work_df.copy()
                work_df["calendar_month"] = dt_series.dt.month
                season_col = "calendar_month"

            if not season_col:
                season_col = work_df.columns[0]

            grouped = work_df.groupby(season_col, observed=True)[target_col].mean().dropna()
            mean_val = float(grouped.mean())
            std_val = float(grouped.std()) if len(grouped) > 1 else 0.0
            cv = (std_val / mean_val) if mean_val > 0 else 0.0
            cv_rounded = round(cv, 3)

            # Rubric check: CV > 0.15 indicates seasonality, CV <= 0.15 indicates NO meaningful seasonality!
            has_seasonality = cv > 0.15
            peak_period = grouped.idxmax()
            trough_period = grouped.idxmin()

            if has_seasonality:
                summary = (
                    f"Noticeable seasonal pattern detected for '{target_col}' (Coefficient of Variation = {cv_rounded} > 0.15). "
                    f"Peak activity occurs in period '{peak_period}' (avg {grouped.max():,.2f}) vs trough in '{trough_period}' (avg {grouped.min():,.2f})."
                )
            else:
                summary = (
                    f"No meaningful seasonality detected for '{target_col}' (Coefficient of Variation = {cv_rounded} <= 0.15). "
                    f"Demand and volume remain relatively steady across periods."
                )

            return {
                "ok": True,
                "data": {
                    "has_seasonality": bool(has_seasonality),
                    "coefficient_of_variation": cv_rounded,
                    "threshold": 0.15,
                    "period_means": {str(k): round(float(v), 2) for k, v in grouped.items()},
                    "peak_period": str(peak_period),
                    "trough_period": str(trough_period),
                },
                "summary": summary,
                "meta": {"operation": op, "season_column": season_col, "target_column": target_col},
                "error": None,
            }

        else:
            return {
                "ok": False,
                "data": {},
                "summary": f"Unsupported compute operation: '{op}'.",
                "meta": {"supported_operations": ["growth_rate", "share_of_total", "descriptive_stats", "correlation", "outliers", "trend", "seasonality"]},
                "error": f"Unknown operation {op}",
            }

    except Exception as e:
        logger.error(f"Error in compute_metrics ({op}): {e}", exc_info=True)
        return {
            "ok": False,
            "data": {},
            "summary": f"Failed to compute {op}: {str(e)}",
            "meta": {"operation": op},
            "error": str(e),
        }

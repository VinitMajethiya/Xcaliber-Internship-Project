from functools import lru_cache
from typing import Any
import pandas as pd
from .data import get_dataset


@lru_cache(maxsize=1)
def get_dataset_profile() -> dict[str, Any]:
    """
    Computes and caches a lightweight dataset profile dictionary.
    Used for UI sidebar summary and system prompt injection.
    """
    df = get_dataset()

    # Determine date column
    date_col = "order_purchase_timestamp" if "order_purchase_timestamp" in df.columns else "Order Date" if "Order Date" in df.columns else None

    if date_col and date_col in df.columns:
        min_date = df[date_col].min().strftime("%Y-%m-%d") if pd.notna(df[date_col].min()) else "N/A"
        max_date = df[date_col].max().strftime("%Y-%m-%d") if pd.notna(df[date_col].max()) else "N/A"
    else:
        min_date = "N/A"
        max_date = "N/A"

    cat_cols = [
        "category", "customer_state", "seller_state", "primary_payment_type",
        "order_status", "Region", "Market", "Category", "Sub-Category", "Segment", "Ship Mode"
    ]
    categorical_values: dict[str, list[str]] = {}
    for col in cat_cols:
        if col in df.columns:
            categorical_values[col] = sorted(df[col].dropna().unique().astype(str).tolist())

    dtypes_dict = {col: str(dtype) for col, dtype in df.dtypes.items()}

    num_cols = ["price", "freight_value", "total_payment", "review_score", "delivery_days", "Sales", "Profit", "Quantity"]
    metrics_summary = {}
    for num_col in num_cols:
        if num_col in df.columns:
            metrics_summary[num_col] = {
                "min": float(round(df[num_col].min(), 2)),
                "max": float(round(df[num_col].max(), 2)),
                "mean": float(round(df[num_col].mean(), 2)),
                "total": float(round(df[num_col].sum(), 2)),
            }

    dataset_name = "Olist Brazilian E-Commerce" if "customer_state" in df.columns else "Global Superstore Sales"

    return {
        "dataset_name": dataset_name,
        "total_rows": int(len(df)),
        "total_columns": int(len(df.columns)),
        "columns": list(df.columns),
        "dtypes": dtypes_dict,
        "date_range": {
            "min_date": min_date,
            "max_date": max_date,
            "years": sorted(df["order_year"].unique().tolist()) if "order_year" in df.columns else []
        },
        "categories": categorical_values,
        "metrics_summary": metrics_summary,
    }


def get_schema_prompt_text() -> str:
    """
    Returns a compact markdown string describing the schema for injection into LLM prompts.
    """
    profile = get_dataset_profile()
    date_info = profile["date_range"]
    cats = profile["categories"]

    lines = [
        f"### Dataset Schema Profile: {profile['dataset_name']}",
        f"- **Rows**: {profile['total_rows']:,} | **Time Span**: {date_info['min_date']} to {date_info['max_date']} (Years: {', '.join(map(str, date_info['years']))})",
        "- **Columns & Types**:",
    ]
    for col, dt in profile["dtypes"].items():
        lines.append(f"  - `{col}` ({dt})")

    lines.append("- **Categorical Distinct Values**:")
    for cat_name, vals in cats.items():
        vals_str = ", ".join(vals) if len(vals) <= 12 else f"{', '.join(vals[:12])} (+ {len(vals)-12} more)"
        lines.append(f"  - **{cat_name}**: [{vals_str}]")

    return "\n".join(lines)

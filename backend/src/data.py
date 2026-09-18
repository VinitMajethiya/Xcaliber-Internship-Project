import logging
from functools import lru_cache
from pathlib import Path
import pandas as pd
import numpy as np
from .config import DATASET_PATH

logger = logging.getLogger("insight_copilot.data")


def load_and_clean_dataset(csv_path: str | Path = DATASET_PATH) -> pd.DataFrame:
    """
    Loads the dataset CSV (Olist E-Commerce or Superstore) and applies aggressive memory downcasting and derived columns.
    Target memory footprint: < 30 MB in RAM.
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset CSV not found at: {path.resolve()}")

    logger.info(f"Loading dataset from {path.resolve()}...")
    df = pd.read_csv(path)

    # 1. Date conversion
    date_cols = ["order_purchase_timestamp", "order_delivered_customer_date", "Order Date", "Ship Date"]
    for c in date_cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")

    # 2. Derived time series column
    if "order_purchase_timestamp" in df.columns:
        df["order_year_month"] = df["order_purchase_timestamp"].dt.to_period("M").astype(str).astype("category")

    # 3. Categorical downcasting for low/medium cardinality strings
    cat_cols = [
        "customer_state", "seller_state", "category", "primary_payment_type",
        "order_status", "order_quarter", "order_year_month", "Ship Mode", "Segment", "Country",
        "Market", "Region", "Category", "Sub-Category", "Order Priority"
    ]
    for col in cat_cols:
        if col in df.columns:
            df[col] = df[col].astype("category")

    # 3. Numeric downcasting
    int32_cols = ["Row ID", "order_item_id"]
    for c in int32_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(np.int32)

    int16_cols = ["Quantity", "payment_installments", "order_year"]
    for c in int16_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(np.int16)

    int8_cols = ["order_month"]
    for c in int8_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(np.int8)

    float_cols = [
        "price", "freight_value", "total_payment", "review_score", "delivery_days",
        "Sales", "Discount", "Profit", "Shipping Cost"
    ]
    for col in float_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype(np.float32)

    # 4. Derived columns if not already computed
    if "order_purchase_timestamp" in df.columns and "order_year" not in df.columns:
        df["order_year"] = df["order_purchase_timestamp"].dt.year.fillna(2017).astype(np.int16)
        df["order_quarter"] = df["order_purchase_timestamp"].dt.to_period("Q").astype(str).astype("category")
        df["order_month"] = df["order_purchase_timestamp"].dt.month.fillna(1).astype(np.int8)

    if "Order Date" in df.columns and "order_year" not in df.columns:
        df["order_year"] = df["Order Date"].dt.year.fillna(2014).astype(np.int16)
        df["order_quarter"] = df["Order Date"].dt.to_period("Q").astype(str).astype("category")
        df["order_month"] = df["Order Date"].dt.month.fillna(1).astype(np.int8)

    # Measure memory usage
    mem_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
    logger.info(f"Dataset loaded: {len(df):,} rows, {len(df.columns)} columns, RAM usage: {mem_mb:.2f} MB")
    
    return df


@lru_cache(maxsize=1)
def get_dataset() -> pd.DataFrame:
    """
    Singleton accessor for the cleaned DataFrame.
    """
    return load_and_clean_dataset()

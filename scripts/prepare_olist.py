import os
import sys
import pandas as pd
import numpy as np

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
output_file = os.path.join(data_dir, 'olist_master.csv')

print(f"Loading raw Olist CSVs from {data_dir}...")

orders_path = os.path.join(data_dir, 'olist_orders_dataset.csv')
items_path = os.path.join(data_dir, 'olist_order_items_dataset.csv')
cust_path = os.path.join(data_dir, 'olist_customers_dataset.csv')
prod_path = os.path.join(data_dir, 'olist_products_dataset.csv')
trans_path = os.path.join(data_dir, 'product_category_name_translation.csv')
sellers_path = os.path.join(data_dir, 'olist_sellers_dataset.csv')
payments_path = os.path.join(data_dir, 'olist_order_payments_dataset.csv')
reviews_path = os.path.join(data_dir, 'olist_order_reviews_dataset.csv')

orders = pd.read_csv(orders_path)
items = pd.read_csv(items_path)
cust = pd.read_csv(cust_path)
prod = pd.read_csv(prod_path)
trans = pd.read_csv(trans_path) if os.path.exists(trans_path) else pd.DataFrame(columns=['product_category_name', 'product_category_name_english'])
sellers = pd.read_csv(sellers_path)
payments = pd.read_csv(payments_path)
reviews = pd.read_csv(reviews_path)

# 1. Translate product categories to English
if 'product_category_name_english' in trans.columns:
    prod = prod.merge(trans, on='product_category_name', how='left')
    prod['category'] = prod['product_category_name_english'].fillna(prod['product_category_name']).fillna('other')
else:
    prod['category'] = prod['product_category_name'].fillna('other')

# 2. Payments aggregate per order
pay_agg = payments.groupby('order_id').agg(
    total_payment=('payment_value', 'sum'),
    payment_installments=('payment_installments', 'max'),
    primary_payment_type=('payment_type', lambda x: x.iloc[0] if len(x) > 0 else 'unknown')
).reset_index()

# 3. Reviews aggregate per order
rev_agg = reviews.groupby('order_id').agg(
    review_score=('review_score', 'mean')
).reset_index()

# 4. Merge core fact table: items + orders
df = items.merge(orders, on='order_id', how='inner')
df = df.merge(cust[['customer_id', 'customer_city', 'customer_state']], on='customer_id', how='left')
df = df.merge(prod[['product_id', 'category', 'product_weight_g']], on='product_id', how='left')
df = df.merge(sellers[['seller_id', 'seller_city', 'seller_state']], on='seller_id', how='left')
df = df.merge(pay_agg, on='order_id', how='left')
df = df.merge(rev_agg, on='order_id', how='left')

# 5. Dates & Derived features
df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'], errors='coerce')
df['order_delivered_customer_date'] = pd.to_datetime(df['order_delivered_customer_date'], errors='coerce')

df['order_year'] = df['order_purchase_timestamp'].dt.year.fillna(2017).astype(np.int16)
df['order_quarter'] = df['order_purchase_timestamp'].dt.to_period('Q').astype(str)
df['order_month'] = df['order_purchase_timestamp'].dt.month.fillna(1).astype(np.int8)

# Delivery lead time in days
delivery_diff = (df['order_delivered_customer_date'] - df['order_purchase_timestamp']).dt.total_seconds() / 86400.0
df['delivery_days'] = np.where(delivery_diff.isna() | (delivery_diff < 0), np.nan, delivery_diff).round(2)

# Keep standard analytical columns
keep_cols = [
    'order_id', 'order_item_id', 'order_status', 'order_purchase_timestamp',
    'order_year', 'order_quarter', 'order_month', 'customer_state', 'customer_city',
    'seller_state', 'category', 'price', 'freight_value', 'total_payment',
    'primary_payment_type', 'payment_installments', 'review_score', 'delivery_days'
]
df = df[[c for c in keep_cols if c in df.columns]]

# Save master CSV
df.to_csv(output_file, index=False)
file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
print(f"Successfully generated {output_file} with {len(df):,} records ({file_size_mb:.2f} MB).")

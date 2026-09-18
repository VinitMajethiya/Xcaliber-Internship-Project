import sys, pandas as pd, numpy as np
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

df = pd.read_csv('data/olist_master.csv')
mem_mb = df.memory_usage(deep=True).sum() / (1024*1024)

print('=== DATASET QUALITY REPORT (olist_master.csv) ===')
print(f'Rows: {len(df):,}  |  Columns: {len(df.columns)}')
print(f'Columns: {list(df.columns)}')
print()

print('--- Dtypes ---')
print(df.dtypes.to_string())
print()

print('--- Null Count per Column ---')
print(df.isnull().sum().to_string())
print()

print('--- Date Range ---')
df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'], errors='coerce')
print('Min date:', df['order_purchase_timestamp'].min())
print('Max date:', df['order_purchase_timestamp'].max())
print('Years:', sorted(df['order_purchase_timestamp'].dt.year.dropna().unique().astype(int).tolist()))
print()

print('--- Category breakdown (top 15) ---')
print(df['category'].value_counts().head(15).to_string())
print()

print('--- Customer State breakdown (top 10) ---')
print(df['customer_state'].value_counts().head(10).to_string())
print()

print('--- Numeric Column Stats ---')
for col in ['price', 'freight_value', 'total_payment', 'review_score', 'delivery_days']:
    s = pd.to_numeric(df[col], errors='coerce')
    print(f'{col}: min={s.min():.2f}  mean={s.mean():.2f}  max={s.max():.2f}  nulls={s.isna().sum()}')
print()

print('--- order_status distribution ---')
print(df['order_status'].value_counts().to_string())
print()

print('--- payment_type distribution ---')
print(df['primary_payment_type'].value_counts().to_string())
print()

print(f'RAM Footprint (raw CSV load, no downcasting): {mem_mb:.2f} MB')

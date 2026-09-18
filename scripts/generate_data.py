import csv
import random
from datetime import datetime, timedelta
import os

random.seed(42)

regions_data = {
    'Central': {'countries': ['United States', 'Germany', 'France', 'Poland', 'Mexico'], 'markets': ['US', 'EU', 'LATAM']},
    'South': {'countries': ['United States', 'Italy', 'Spain', 'Brazil', 'South Africa'], 'markets': ['US', 'EU', 'LATAM', 'Africa']},
    'East': {'countries': ['United States', 'United Kingdom', 'Netherlands', 'Turkey', 'Egypt'], 'markets': ['US', 'EU', 'EMEA']},
    'West': {'countries': ['United States', 'Canada', 'Australia', 'New Zealand', 'China', 'Japan', 'India'], 'markets': ['US', 'APAC']},
    'North': {'countries': ['Sweden', 'Norway', 'Finland', 'Canada', 'Russia'], 'markets': ['EU', 'EMEA']},
    'EMEA': {'countries': ['Saudi Arabia', 'United Arab Emirates', 'Israel', 'South Africa', 'Nigeria'], 'markets': ['EMEA', 'Africa']},
    'APAC': {'countries': ['Australia', 'China', 'India', 'Japan', 'Indonesia', 'Singapore', 'South Korea'], 'markets': ['APAC']},
    'Africa': {'countries': ['Egypt', 'Nigeria', 'South Africa', 'Kenya', 'Morocco', 'Ghana'], 'markets': ['Africa']},
    'LATAM': {'countries': ['Brazil', 'Mexico', 'Argentina', 'Colombia', 'Chile', 'Peru'], 'markets': ['LATAM']}
}

categories = {
    'Furniture': ['Bookcases', 'Chairs', 'Furnishings', 'Tables'],
    'Office Supplies': ['Appliances', 'Art', 'Binders', 'Envelopes', 'Fasteners', 'Labels', 'Paper', 'Storage', 'Supplies'],
    'Technology': ['Accessories', 'Copiers', 'Machines', 'Phones']
}

segments = ['Consumer', 'Corporate', 'Home Office']
ship_modes = ['Standard Class', 'Second Class', 'First Class', 'Same Day']
priorities = ['Low', 'Medium', 'High', 'Critical']

start_date = datetime(2011, 1, 1)
end_date = datetime(2014, 12, 31)
date_range_days = (end_date - start_date).days

num_rows = 51290
headers = [
    'Row ID', 'Order ID', 'Order Date', 'Ship Date', 'Ship Mode',
    'Customer ID', 'Customer Name', 'Segment', 'City', 'State',
    'Country', 'Postal Code', 'Market', 'Region', 'Product ID',
    'Category', 'Sub-Category', 'Product Name', 'Sales', 'Quantity',
    'Discount', 'Profit', 'Shipping Cost', 'Order Priority'
]

customers = [(f'CUST-{i:04d}', f'Customer {i}') for i in range(1, 1500)]

rows = []
for i in range(1, num_rows + 1):
    order_dt = start_date + timedelta(days=random.randint(0, date_range_days))
    ship_dt = order_dt + timedelta(days=random.randint(1, 7))
    
    region = random.choice(list(regions_data.keys()))
    reg_info = regions_data[region]
    country = random.choice(reg_info['countries'])
    market = random.choice(reg_info['markets'])
    
    cat = random.choice(list(categories.keys()))
    subcat = random.choice(categories[cat])
    
    cust_id, cust_name = random.choice(customers)
    segment = random.choice(segments)
    ship_mode = random.choice(ship_modes)
    priority = random.choice(priorities)
    
    qty = random.randint(1, 14)
    base_unit_price = {
        'Technology': random.uniform(50, 800),
        'Furniture': random.uniform(30, 450),
        'Office Supplies': random.uniform(5, 120)
    }[cat]
    
    seasonal_mult = 1.35 if order_dt.month in [10, 11, 12] else (1.15 if order_dt.month in [6, 7, 8] else 1.0)
    discount = random.choice([0.0, 0.0, 0.1, 0.2, 0.3, 0.4, 0.6, 0.7])
    
    sales = round(qty * base_unit_price * seasonal_mult * (1.0 - discount * 0.5), 2)
    base_margin = 0.25 if cat == 'Technology' else (0.15 if cat == 'Office Supplies' else 0.05)
    margin = base_margin - (discount * 0.7) + random.uniform(-0.08, 0.08)
    profit = round(sales * margin, 2)
    
    shipping_cost = round(random.uniform(1.5, 45.0) + (sales * 0.04), 2)
    order_id = f'{market}-{order_dt.year}-{random.randint(100000, 999999)}'
    prod_id = f'{cat[:3].upper()}-{subcat[:3].upper()}-{random.randint(1000, 9999)}'
    prod_name = f'{subcat} Model {random.randint(100, 999)}'
    postal = f'{random.randint(10000, 99999)}' if country == 'United States' else ''
    
    rows.append([
        i, order_id, order_dt.strftime('%Y-%m-%d'), ship_dt.strftime('%Y-%m-%d'),
        ship_mode, cust_id, cust_name, segment, f'{country} City', f'{country} State',
        country, postal, market, region, prod_id, cat, subcat, prod_name,
        sales, qty, discount, profit, shipping_cost, priority
    ])

os.makedirs('data', exist_ok=True)
dest = 'data/global_superstore.csv'
with open(dest, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    writer.writerows(rows)

size_mb = os.path.getsize(dest) / (1024 * 1024)
print(f'Successfully generated {dest} with {len(rows)} rows, size: {size_mb:.2f} MB')

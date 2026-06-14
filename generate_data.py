# generate_data.py
# Generates mock e-commerce data for the Star Schema Data Warehouse
# Run: python generate_data.py
# Dependencies: pip install pandas faker numpy

import pandas as pd
import numpy as np
from faker import Faker
import os
import time

fake = Faker()
Faker.seed(42)
np.random.seed(42)

OUTPUT_DIR = "data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

DIM_SIZE  = 10_000
FACT_SIZE = 50_000

CATEGORIES = ["Electronics", "Clothing", "Home & Garden", "Sports", "Books",
              "Toys", "Beauty", "Automotive", "Food & Grocery", "Office Supplies"]

BRANDS = ["NovaTech", "UrbanEdge", "PureLife", "SwiftGear", "BrightHome",
          "EcoWave", "PeakPro", "LuxeLine", "TrueValue", "ZenCraft"]

PAYMENT_METHODS = ["Credit Card", "Debit Card", "PayPal", "Apple Pay",
                   "Google Pay", "Bank Transfer", "Gift Card"]

STORE_TYPES = ["Flagship", "Express", "Online", "Outlet", "Pop-Up"]

CHANNELS    = ["Web", "Mobile App", "In-Store", "Phone", "Social Media"]

print("=" * 55)
print("  E-Commerce Data Warehouse — Data Generator")
print("=" * 55)

# ── 1. dim_customers ──────────────────────────────────────────
print("\n[1/5] Generating dim_customers ...", end=" ", flush=True)
t = time.time()

customer_sks = np.arange(1, DIM_SIZE + 1)

dim_customers = pd.DataFrame({
    "customer_sk":       customer_sks,
    "customer_id":       [fake.uuid4() for _ in range(DIM_SIZE)],
    "first_name":        [fake.first_name() for _ in range(DIM_SIZE)],
    "last_name":         [fake.last_name() for _ in range(DIM_SIZE)],
    "email":             [fake.unique.email() for _ in range(DIM_SIZE)],
    "phone":             [fake.phone_number() for _ in range(DIM_SIZE)],
    "city":              [fake.city() for _ in range(DIM_SIZE)],
    "state":             [fake.state_abbr() for _ in range(DIM_SIZE)],
    "country":           np.random.choice(
                             ["US", "CA", "GB", "AU", "DE", "FR", "IN", "BR"],
                             DIM_SIZE, p=[0.45, 0.12, 0.10, 0.08, 0.08, 0.07, 0.06, 0.04]),
    "gender":            np.random.choice(["M", "F", "Other"],
                             DIM_SIZE, p=[0.48, 0.48, 0.04]),
    "age":               np.random.randint(18, 80, DIM_SIZE),
    "loyalty_tier":      np.random.choice(
                             ["Bronze", "Silver", "Gold", "Platinum"],
                             DIM_SIZE, p=[0.50, 0.30, 0.15, 0.05]),
    "registration_date": pd.to_datetime(
                             np.random.randint(
                                 pd.Timestamp("2015-01-01").value // 10**9,
                                 pd.Timestamp("2023-12-31").value // 10**9,
                                 DIM_SIZE
                             ), unit="s"
                         ).strftime("%Y-%m-%d"),
    "is_active":         np.random.choice([True, False], DIM_SIZE, p=[0.88, 0.12]),
})

dim_customers.to_csv(f"{OUTPUT_DIR}/dim_customers.csv", index=False)
print(f"done  ({time.time()-t:.1f}s)  →  {len(dim_customers):,} rows")

# ── 2. dim_products ───────────────────────────────────────────
print("[2/5] Generating dim_products  ...", end=" ", flush=True)
t = time.time()

product_sks = np.arange(1, DIM_SIZE + 1)
categories  = np.random.choice(CATEGORIES, DIM_SIZE)
brands      = np.random.choice(BRANDS, DIM_SIZE)

dim_products = pd.DataFrame({
    "product_sk":   product_sks,
    "product_id":   [fake.uuid4() for _ in range(DIM_SIZE)],
    "product_name": [f"{brands[i]} {fake.word().capitalize()} {fake.word().capitalize()}"
                     for i in range(DIM_SIZE)],
    "category":     categories,
    "sub_category": [fake.word().capitalize() for _ in range(DIM_SIZE)],
    "brand":        brands,
    "unit_cost":    np.round(np.random.uniform(1.5, 450.0, DIM_SIZE), 2),
    "unit_price":   np.round(
                        np.random.uniform(1.5, 450.0, DIM_SIZE) *
                        np.random.uniform(1.15, 2.50, DIM_SIZE), 2),
    "weight_kg":    np.round(np.random.uniform(0.1, 30.0, DIM_SIZE), 2),
    "is_active":    np.random.choice([True, False], DIM_SIZE, p=[0.92, 0.08]),
    "launch_date":  pd.to_datetime(
                        np.random.randint(
                            pd.Timestamp("2010-01-01").value // 10**9,
                            pd.Timestamp("2023-12-31").value // 10**9,
                            DIM_SIZE
                        ), unit="s"
                    ).strftime("%Y-%m-%d"),
    "supplier_country": np.random.choice(
                            ["CN", "US", "DE", "IN", "VN", "MX", "KR"],
                            DIM_SIZE),
})

dim_products.to_csv(f"{OUTPUT_DIR}/dim_products.csv", index=False)
print(f"done  ({time.time()-t:.1f}s)  →  {len(dim_products):,} rows")

# ── 3. dim_stores ─────────────────────────────────────────────
print("[3/5] Generating dim_stores    ...", end=" ", flush=True)
t = time.time()

store_sks = np.arange(1, DIM_SIZE + 1)

dim_stores = pd.DataFrame({
    "store_sk":      store_sks,
    "store_id":      [fake.uuid4() for _ in range(DIM_SIZE)],
    "store_name":    [f"{fake.city()} {np.random.choice(STORE_TYPES)} Store"
                      for _ in range(DIM_SIZE)],
    "store_type":    np.random.choice(STORE_TYPES, DIM_SIZE,
                         p=[0.10, 0.25, 0.40, 0.15, 0.10]),
    "city":          [fake.city() for _ in range(DIM_SIZE)],
    "state":         [fake.state_abbr() for _ in range(DIM_SIZE)],
    "country":       np.random.choice(
                         ["US", "CA", "GB", "AU", "DE", "FR"],
                         DIM_SIZE, p=[0.45, 0.15, 0.15, 0.10, 0.10, 0.05]),
    "region":        np.random.choice(
                         ["North", "South", "East", "West", "Central"],
                         DIM_SIZE),
    "sq_footage":    np.random.randint(500, 25000, DIM_SIZE),
    "open_date":     pd.to_datetime(
                         np.random.randint(
                             pd.Timestamp("2000-01-01").value // 10**9,
                             pd.Timestamp("2022-12-31").value // 10**9,
                             DIM_SIZE
                         ), unit="s"
                     ).strftime("%Y-%m-%d"),
    "is_active":     np.random.choice([True, False], DIM_SIZE, p=[0.90, 0.10]),
    "manager_name":  [fake.name() for _ in range(DIM_SIZE)],
})

dim_stores.to_csv(f"{OUTPUT_DIR}/dim_stores.csv", index=False)
print(f"done  ({time.time()-t:.1f}s)  →  {len(dim_stores):,} rows")

# ── 4. dim_time ───────────────────────────────────────────────
print("[4/5] Generating dim_time      ...", end=" ", flush=True)
t = time.time()

# Generate DIM_SIZE unique dates spanning ~27 years
date_range   = pd.date_range(start="2018-01-01", periods=DIM_SIZE, freq="h")
time_sks     = np.arange(1, DIM_SIZE + 1)

dim_time = pd.DataFrame({
    "time_sk":        time_sks,
    "full_date":      date_range.strftime("%Y-%m-%d"),
    "year":           date_range.year,
    "quarter":        date_range.quarter,
    "month":          date_range.month,
    "month_name":     date_range.strftime("%B"),
    "week":           date_range.isocalendar().week.astype(int),
    "day_of_month":   date_range.day,
    "day_of_week":    date_range.dayofweek + 1,        # 1=Mon … 7=Sun
    "day_name":       date_range.strftime("%A"),
    "hour":           date_range.hour,
    "is_weekend":     date_range.dayofweek >= 5,
    "is_holiday":     np.random.choice([True, False], DIM_SIZE, p=[0.05, 0.95]),
    "fiscal_year":    np.where(date_range.month >= 10,
                               date_range.year + 1, date_range.year),
    "fiscal_quarter": ((date_range.month - 1) // 3 + 1),
})

dim_time.to_csv(f"{OUTPUT_DIR}/dim_time.csv", index=False)
print(f"done  ({time.time()-t:.1f}s)  →  {len(dim_time):,} rows")

# ── 5. fact_sales ─────────────────────────────────────────────
print("[5/5] Generating fact_sales    ...", end=" ", flush=True)
t = time.time()

# --- REFERENTIAL INTEGRITY: sample strictly from existing SKs ---
fk_customer = np.random.choice(customer_sks, FACT_SIZE, replace=True)
fk_product  = np.random.choice(product_sks,  FACT_SIZE, replace=True)
fk_store    = np.random.choice(store_sks,    FACT_SIZE, replace=True)
fk_time     = np.random.choice(time_sks,     FACT_SIZE, replace=True)

# Pull unit prices for the sampled products (vectorised lookup)
price_lookup = dim_products.set_index("product_sk")["unit_price"]
cost_lookup  = dim_products.set_index("product_sk")["unit_cost"]

unit_prices = price_lookup.loc[fk_product].values
unit_costs  = cost_lookup.loc[fk_product].values

quantity     = np.random.randint(1, 11, FACT_SIZE)
discount_pct = np.round(
    np.random.choice([0, 5, 10, 15, 20, 25, 30], FACT_SIZE,
                     p=[0.40, 0.15, 0.15, 0.12, 0.10, 0.05, 0.03]), 2)

gross_revenue  = np.round(unit_prices * quantity, 2)
discount_amt   = np.round(gross_revenue * discount_pct / 100, 2)
net_revenue    = np.round(gross_revenue - discount_amt, 2)
total_cost     = np.round(unit_costs * quantity, 2)
profit         = np.round(net_revenue - total_cost, 2)
tax_rate       = np.random.choice([0.05, 0.08, 0.10, 0.12], FACT_SIZE,
                                  p=[0.20, 0.35, 0.30, 0.15])
tax_amount     = np.round(net_revenue * tax_rate, 2)
shipping_cost  = np.round(np.random.uniform(0, 25, FACT_SIZE), 2)

fact_sales = pd.DataFrame({
    "sale_sk":          np.arange(1, FACT_SIZE + 1),
    "customer_sk":      fk_customer,
    "product_sk":       fk_product,
    "store_sk":         fk_store,
    "time_sk":          fk_time,
    "order_id":         [fake.uuid4() for _ in range(FACT_SIZE)],
    "quantity":         quantity,
    "unit_price":       unit_prices,
    "unit_cost":        unit_costs,
    "discount_pct":     discount_pct,
    "discount_amount":  discount_amt,
    "gross_revenue":    gross_revenue,
    "net_revenue":      net_revenue,
    "total_cost":       total_cost,
    "profit":           profit,
    "tax_amount":       tax_amount,
    "shipping_cost":    shipping_cost,
    "payment_method":   np.random.choice(PAYMENT_METHODS, FACT_SIZE,
                            p=[0.35, 0.20, 0.18, 0.10, 0.08, 0.05, 0.04]),
    "sales_channel":    np.random.choice(CHANNELS, FACT_SIZE,
                            p=[0.35, 0.28, 0.22, 0.08, 0.07]),
    "return_flag":      np.random.choice([True, False], FACT_SIZE,
                            p=[0.07, 0.93]),
    "return_amount":    np.where(
                            np.random.choice([True, False], FACT_SIZE,
                                             p=[0.07, 0.93]),
                            np.round(net_revenue * np.random.uniform(0.5, 1.0, FACT_SIZE), 2),
                            0.0),
})

fact_sales.to_csv(f"{OUTPUT_DIR}/fact_sales.csv", index=False)
print(f"done  ({time.time()-t:.1f}s)  →  {len(fact_sales):,} rows")

# ── Summary ───────────────────────────────────────────────────
print("\n" + "=" * 55)
print("  All CSV files written to ./data/")
print("=" * 55)
total_rows = DIM_SIZE * 4 + FACT_SIZE
for fname in sorted(os.listdir(OUTPUT_DIR)):
    path = f"{OUTPUT_DIR}/{fname}"
    rows = sum(1 for _ in open(path)) - 1
    size = os.path.getsize(path) / 1024
    print(f"  {fname:<25}  {rows:>6,} rows  {size:>8.1f} KB")
print(f"\n  Total rows generated: {total_rows:,}")
print("=" * 55)

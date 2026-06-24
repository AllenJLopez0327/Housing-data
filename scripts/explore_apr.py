"""
explore_apr.py

Exploratory analysis of the APR dataset before geocoding.
Run from the repo root:
    python3 scripts/explore_apr.py
"""

import pandas as pd
from pathlib import Path

# ── Load ──────────────────────────────────────────────────────────────────────

df = pd.read_csv('data/apr.csv', low_memory=False)

# ── 1. All columns with sample values ─────────────────────────────────────────

print("=" * 70)
print("ALL COLUMNS — name, dtype, and a sample non-null value")
print("=" * 70)
for col in df.columns:
    sample = df[col].dropna()
    sample = sample[sample.astype(str).str.strip() != '']
    sample_val = sample.iloc[0] if len(sample) > 0 else 'ALL NULL/EMPTY'
    print(f"  {col:<45} {str(df[col].dtype):<10} e.g. {sample_val}")

# ── 2. Basic shape ─────────────────────────────────────────────────────────────

print("\n" + "=" * 70)
print("BASIC SHAPE")
print("=" * 70)
print(f"  Total rows:    {len(df):,}")
print(f"  Total columns: {len(df.columns)}")

# ── 3. Lat/Long coverage ──────────────────────────────────────────────────────

print("\n" + "=" * 70)
print("LAT / LONG COVERAGE")
print("=" * 70)

lat_null  = df['LATITUDE'].isna() | (df['LATITUDE'].astype(str).str.strip() == '')
lng_null  = df['LONGITUDE'].isna() | (df['LONGITUDE'].astype(str).str.strip() == '')
both_null = lat_null & lng_null
has_both  = ~lat_null & ~lng_null

print(f"  Rows with both LAT and LONG:     {has_both.sum():,}")
print(f"  Rows missing LAT only:           {(lat_null & ~lng_null).sum():,}")
print(f"  Rows missing LONG only:          {(lng_null & ~lat_null).sum():,}")
both_missing = both_null.sum()
print(f"  Rows missing both:               {both_missing:,}")
print(f"  % geocodeable:                   {has_both.sum() / len(df) * 100:.1f}%")

unique_coords = df[has_both][['LATITUDE', 'LONGITUDE']].drop_duplicates()
print(f"  Unique lat/long pairs:           {len(unique_coords):,}")

# ── 4. Null counts for all columns ────────────────────────────────────────────

print("\n" + "=" * 70)
print("NULL / BLANK COUNTS PER COLUMN")
print("=" * 70)
for col in df.columns:
    null_count  = df[col].isna().sum()
    blank_count = (df[col].astype(str).str.strip() == '').sum()
    total_missing = null_count + blank_count
    pct = total_missing / len(df) * 100
    bar = '█' * int(pct / 5)  # rough visual bar (each block = 5%)
    print(f"  {col:<45} {total_missing:>7,} missing ({pct:5.1f}%) {bar}")

# ── 5. CO columns preview ─────────────────────────────────────────────────────

co_cols = [c for c in df.columns if c.startswith('CO_')]

print("\n" + "=" * 70)
print("CO (CERTIFICATE OF OCCUPANCY) COLUMNS — sum of completed units")
print("=" * 70)
for col in co_cols:
    if col == 'CO_ISSUE_DT1':
        non_null = df[col].notna().sum()
        print(f"  {col:<45} {non_null:>10,} non-null dates")
    else:
        total = pd.to_numeric(df[col], errors='coerce').sum()
        print(f"  {col:<45} {total:>10,.0f} total units")

print("\n" + "=" * 70)
print("CO COLUMNS — sample of 5 rows")
print("=" * 70)
print(df[['JURIS_NAME', 'CNTY_NAME', 'YEAR'] + co_cols].head(5).to_string())
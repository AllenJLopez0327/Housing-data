"""
crosswalk.py

Aligns 2010 Census block housing units to 2020 block boundaries
using the NHGIS crosswalk file. Each 2010 block's housing units
are distributed to 2020 blocks proportionally using the weight column.

Run from the repo root:
    python3 scripts/crosswalk.py

Input:  data/census_2010.csv
        data/crosswalk.csv
Output: data/census_2010_adjusted.csv
"""

import pandas as pd
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

INPUT_2010 = Path('data/census_2010.csv')
INPUT_CW   = Path('data/crosswalk.csv')
OUTPUT     = Path('data/census_2010_adjusted.csv')

# ── Main ──────────────────────────────────────────────────────────────────────

def main():

    # ── 1. Load 2010 census data ──────────────────────────────────────────────
    print("Loading 2010 census data...")
    census = pd.read_csv(INPUT_2010, low_memory=False)
    census['GEOID'] = census['GEOID'].astype(str).str.zfill(15)
    print(f"  {len(census):,} blocks loaded")

    # ── 2. Load crosswalk ─────────────────────────────────────────────────────
    print("\nLoading crosswalk...")
    cw = pd.read_csv(INPUT_CW, low_memory=False)
    cw['blk2010ge'] = cw['blk2010ge'].astype(str).str.zfill(15)
    cw['blk2020ge'] = cw['blk2020ge'].astype(str).str.zfill(15)
    print(f"  {len(cw):,} crosswalk rows loaded")

    # ── 3. Diagnose weight vs parea before applying ───────────────────────────
    print("\nDiagnosing weight and parea columns:")
    print(f"  weight — min: {cw['weight'].min():.4f}  "
          f"max: {cw['weight'].max():.4f}  "
          f"mean: {cw['weight'].mean():.4f}  "
          f"unique values: {cw['weight'].nunique()}")
    print(f"  parea  — min: {cw['parea'].min():.4f}  "
          f"max: {cw['parea'].max():.4f}  "
          f"mean: {cw['parea'].mean():.4f}  "
          f"unique values: {cw['parea'].nunique()}")

    # Decide which column to use
    # If weight has only 0s and 1s it's a flag, not a proportion — use parea
    weight_is_binary = cw['weight'].isin([0, 1]).all()
    if weight_is_binary:
        print("\n  ⚠ weight column is binary (0s and 1s only) — using parea instead")
        cw['allocation'] = cw['parea']
    else:
        print("\n  ✓ weight column looks correct — using weight")
        cw['allocation'] = cw['weight']

    # ── 4. Join census 2010 to crosswalk ──────────────────────────────────────
    print("\nJoining 2010 census to crosswalk...")
    merged = census.merge(
        cw[['blk2010ge', 'blk2020ge', 'allocation']],
        left_on='GEOID',
        right_on='blk2010ge',
        how='left'
    )

    matched   = merged['blk2020ge'].notna().sum()
    unmatched = merged['blk2020ge'].isna().sum()
    print(f"  ✓ Matched:   {matched:,} rows")
    print(f"  ✗ Unmatched: {unmatched:,} rows")

    # ── 5. Apply allocation weight to housing units ───────────────────────────
    merged['HOUSING_UNITS_2010'] = merged['HOUSING_UNITS'] * merged['allocation']

    # ── 6. Aggregate by 2020 GEOID ────────────────────────────────────────────
    print("\nAggregating by 2020 block GEOID...")
    adjusted = (
        merged
        .groupby('blk2020ge', as_index=False)
        .agg(HOUSING_UNITS_2010=('HOUSING_UNITS_2010', 'sum'))
        .rename(columns={'blk2020ge': 'GEOID20'})
    )
    print(f"  {len(adjusted):,} unique 2020 blocks")

    # ── 7. Quick sanity check ─────────────────────────────────────────────────
    total_2010_original = census['HOUSING_UNITS'].sum()
    total_2010_adjusted = adjusted['HOUSING_UNITS_2010'].sum()
    print(f"\nSanity check:")
    print(f"  Total units in original 2010 data:  {total_2010_original:,.0f}")
    print(f"  Total units after crosswalk:        {total_2010_adjusted:,.0f}")
    print(f"  Difference:                         {abs(total_2010_original - total_2010_adjusted):,.0f}")

    # ── 8. Save ───────────────────────────────────────────────────────────────
    adjusted.to_csv(OUTPUT, index=False)
    print(f"\nDone! {len(adjusted):,} rows → {OUTPUT}")


if __name__ == '__main__':
    main()
"""
clean_apr.py

Reads data/apr.csv and writes data/apr_clean.csv keeping only
columns relevant to the housing pipeline. Drops columns that are
>50% missing, internal CKAN fields, or outside project scope
(entitlement and building permit stage columns).

Run from the repo root:
    python3 scripts/clean_apr.py

Input:  data/apr.csv
Output: data/apr_clean.csv
"""

import pandas as pd
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

INPUT  = Path('data/apr.csv')
OUTPUT = Path('data/apr_clean.csv')

# Columns to keep and why
KEEP_COLUMNS = [
    # ── Identifiers ───────────────────────────────────────────────────────────
    'JURIS_NAME',       # Jurisdiction name (e.g. CITY OF OAKLAND)
    'CNTY_NAME',        # County name (e.g. Alameda)
    'YEAR',             # Year of report

    # ── Location ──────────────────────────────────────────────────────────────
    'APN',              # Assessor parcel number
    'STREET_ADDRESS',   # Raw address from jurisdiction
    'STD_ADDRESS',      # Standardized/geocoded address (more reliable)
    'LATITUDE',         # Lat coordinate — needed for geocoding to census block
    'LONGITUDE',        # Long coordinate — needed for geocoding to census block

    # ── Unit characteristics ───────────────────────────────────────────────────
    'UNIT_CAT',         # Unit category (e.g. ADU, SFD, MF)
    'TENURE',           # Owner or Renter

    # ── Completed units by income level (CO = Certificate of Occupancy) ───────
    # These are Karen's core ask — units actually built and occupied
    'CO_ACUTELY_LOW_INCOME_DR',     # Deed restricted acutely low income
    'CO_ACUTELY_LOW_INCOME_NDR',    # Non deed restricted acutely low income
    'CO_EXTREMELY_LOW_INCOME_DR',   # Deed restricted extremely low income
    'CO_EXTREMELY_LOW_INCOME_NDR',  # Non deed restricted extremely low income
    'CO_VLOW_INCOME_DR',            # Deed restricted very low income
    'CO_VLOW_INCOME_NDR',           # Non deed restricted very low income
    'CO_LOW_INCOME_DR',             # Deed restricted low income
    'CO_LOW_INCOME_NDR',            # Non deed restricted low income
    'CO_MOD_INCOME_DR',             # Deed restricted moderate income
    'CO_MOD_INCOME_NDR',            # Non deed restricted moderate income
    'CO_ABOVE_MOD_INCOME',          # Market rate units (above moderate income)
    'CO_ISSUE_DT1',                 # Date certificate of occupancy issued

    # ── Additional context Karen asked for ────────────────────────────────────
    'INFILL_UNITS',     # Units built on previously developed land
    'DEM_DES_UNITS',    # Units demolished or destroyed

    # ── Policy flags ──────────────────────────────────────────────────────────
    'APPROVE_SB35',         # Was project approved via SB35 streamlining? (Y/N)
    'DENSITY_BONUS_TOTAL',  # Total density bonus units received
]

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"Reading {INPUT}...")
    df = pd.read_csv(INPUT, low_memory=False)
    print(f"  Loaded {len(df):,} rows × {len(df.columns)} columns")

    # Verify all expected columns exist before dropping anything
    missing = [c for c in KEEP_COLUMNS if c not in df.columns]
    if missing:
        print(f"\n  ⚠ WARNING — these columns not found in data: {missing}")

    df_clean = df[[c for c in KEEP_COLUMNS if c in df.columns]]

    dropped = len(df.columns) - len(df_clean.columns)
    print(f"  Kept {len(df_clean.columns)} columns, dropped {dropped}")

    df_clean.to_csv(OUTPUT, index=False)
    print(f"\nDone! {len(df_clean):,} rows → {OUTPUT}")


if __name__ == '__main__':
    main()
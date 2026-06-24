"""
geocode.py

Converts APR lat/long coordinates into 2020 Census block GEOIDs
using a spatial join against the California census block shapefile.

Run from the repo root:
    python3 scripts/geocode.py

Input:  data/apr_clean.csv
        data/shapefiles/tl_2020_06_tabblock20.shp
Output: data/apr_geocoded.csv  (same as apr_clean.csv + GEOID20 column)
"""

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

INPUT_APR   = Path('data/apr_clean.csv')
INPUT_SHP   = Path('data/shapefiles/tl_2020_06_tabblock20.shp')
OUTPUT      = Path('data/apr_geocoded.csv')

# ── Main ──────────────────────────────────────────────────────────────────────

def main():

    # ── 1. Load APR data ──────────────────────────────────────────────────────
    print("Loading APR data...")
    apr = pd.read_csv(INPUT_APR, low_memory=False)
    print(f"  {len(apr):,} rows loaded")

    # ── 2. Load shapefile (keep only GEOID20 + geometry) ─────────────────────
    print("\nLoading census block shapefile...")
    blocks = gpd.read_file(INPUT_SHP, columns=['GEOID20'])
    print(f"  {len(blocks):,} census blocks loaded")
    print(f"  Shapefile CRS: {blocks.crs}")

    # ── 3. Deduplicate coordinates before joining ─────────────────────────────
    # 340k rows but only 254k unique lat/long pairs
    # Joining on unique pairs first is much faster
    print("\nDeduplicating coordinates...")
    coords = apr[['LATITUDE', 'LONGITUDE']].drop_duplicates().copy()
    print(f"  {len(coords):,} unique coordinate pairs")

    # ── 4. Convert to GeoDataFrame ────────────────────────────────────────────
    print("\nConverting coordinates to point geometries...")
    coords['geometry'] = coords.apply(
        lambda row: Point(row['LONGITUDE'], row['LATITUDE']), axis=1
    )
    coords_gdf = gpd.GeoDataFrame(coords, geometry='geometry', crs='EPSG:4326')

    # Reproject points to match shapefile CRS (NAD83 / EPSG:4269)
    coords_gdf = coords_gdf.to_crs(blocks.crs)
    print(f"  Reprojected to {blocks.crs}")

    # ── 5. Spatial join ───────────────────────────────────────────────────────
    print("\nRunning spatial join (this may take a minute)...")
    joined = gpd.sjoin(
        coords_gdf,
        blocks[['GEOID20', 'geometry']],
        how='left',
        predicate='within'
    )

    # Keep only the columns we need for the merge
    coord_to_geoid = joined[['LATITUDE', 'LONGITUDE', 'GEOID20']].copy()

    matched   = coord_to_geoid['GEOID20'].notna().sum()
    unmatched = coord_to_geoid['GEOID20'].isna().sum()
    print(f"  ✓ Matched:   {matched:,} coordinates")
    print(f"  ✗ Unmatched: {unmatched:,} coordinates")
    if unmatched > 0:
        pct = unmatched / len(coord_to_geoid) * 100
        print(f"    ({pct:.1f}% — likely points on water or county borders)")

    # ── 6. Merge GEOID back onto full APR dataset ─────────────────────────────
    print("\nMerging GEOIDs back onto full APR dataset...")
    apr_geocoded = apr.merge(coord_to_geoid, on=['LATITUDE', 'LONGITUDE'], how='left')

    # Move GEOID20 to front for readability
    cols = ['GEOID20'] + [c for c in apr_geocoded.columns if c != 'GEOID20']
    apr_geocoded = apr_geocoded[cols]

    # ── 7. Save ───────────────────────────────────────────────────────────────
    apr_geocoded.to_csv(OUTPUT, index=False)
    print(f"\nDone! {len(apr_geocoded):,} rows → {OUTPUT}")
    print(f"  Columns: {list(apr_geocoded.columns[:5])} ...")


if __name__ == '__main__':
    main()
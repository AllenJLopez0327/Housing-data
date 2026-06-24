"""
fetch_census_2010.py

Pulls 2010 Census housing unit counts for every census block
in all 58 California counties and saves the result to data/census_2010.csv.

Run from the repo root:
    python scripts/fetch_census_2010.py

Output columns:
    GEOID           - 15-digit Census block ID (state + county + tract + block)
    COUNTY_NAME     - Human-readable county name
    HOUSING_UNITS   - Number of housing units in this block
    STATE           - State FIPS code (always 06 for California)
    COUNTY          - County FIPS code (3 digits)
    TRACT           - Census tract code
    BLOCK           - Census block code
"""

import csv
import time
import requests
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

API_KEY   = 'f361e9ea9bbf4473f440cbe3580f8523ad28c4be'
OUTPUT    = Path('data/census_2010.csv')
BASE_URL  = 'https://api.census.gov/data/2010/dec/sf1'

# All 58 California counties: FIPS code → county name
COUNTIES = {
    '001': 'Alameda',
    '003': 'Alpine',
    '005': 'Amador',
    '007': 'Butte',
    '009': 'Calaveras',
    '011': 'Colusa',
    '013': 'Contra Costa',
    '015': 'Del Norte',
    '017': 'El Dorado',
    '019': 'Fresno',
    '021': 'Glenn',
    '023': 'Humboldt',
    '025': 'Imperial',
    '027': 'Inyo',
    '029': 'Kern',
    '031': 'Kings',
    '033': 'Lake',
    '035': 'Lassen',
    '037': 'Los Angeles',
    '039': 'Madera',
    '041': 'Marin',
    '043': 'Mariposa',
    '045': 'Mendocino',
    '047': 'Merced',
    '049': 'Modoc',
    '051': 'Mono',
    '053': 'Monterey',
    '055': 'Napa',
    '057': 'Nevada',
    '059': 'Orange',
    '061': 'Placer',
    '063': 'Plumas',
    '065': 'Riverside',
    '067': 'Sacramento',
    '069': 'San Benito',
    '071': 'San Bernardino',
    '073': 'San Diego',
    '075': 'San Francisco',
    '077': 'San Joaquin',
    '079': 'San Luis Obispo',
    '081': 'San Mateo',
    '083': 'Santa Barbara',
    '085': 'Santa Clara',
    '087': 'Santa Cruz',
    '089': 'Shasta',
    '091': 'Sierra',
    '093': 'Siskiyou',
    '095': 'Solano',
    '097': 'Sonoma',
    '099': 'Stanislaus',
    '101': 'Sutter',
    '103': 'Tehama',
    '105': 'Trinity',
    '107': 'Tulare',
    '109': 'Tuolumne',
    '111': 'Ventura',
    '113': 'Yolo',
    '115': 'Yuba',
}

# ── Main ──────────────────────────────────────────────────────────────────────

def fetch_county(code, name):
    """Fetch all census blocks for one county. Returns a list of row dicts."""
    url = (
        f"{BASE_URL}"
        f"?get=NAME,H001001"       # H001001 = total housing units (2010 SF1 variable)
        f"&for=block:*"
        f"&in=state:06"
        f"&in=county:{code}"
        f"&in=tract:*"
        f"&key={API_KEY}"
    )

    response = requests.get(url, timeout=60)
    response.raise_for_status()
    data = response.json()

    rows = []
    for row in data[1:]:  # Skip header row
        _, units, state, county, tract, block = row
        geoid = f"{state}{county}{tract}{block}"
        rows.append({
            'GEOID':         geoid,
            'COUNTY_NAME':   name,
            'HOUSING_UNITS': int(units) if units else 0,
            'STATE':         state,
            'COUNTY':        county,
            'TRACT':         tract,
            'BLOCK':         block,
        })
    return rows


def main():
    # Make sure data/ folder exists
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    total_rows = 0
    fieldnames = ['GEOID', 'COUNTY_NAME', 'HOUSING_UNITS', 'STATE', 'COUNTY', 'TRACT', 'BLOCK']

    with open(OUTPUT, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for i, (code, name) in enumerate(COUNTIES.items(), 1):
            print(f"[{i:02d}/58] Fetching {name} County...", end=' ', flush=True)
            try:
                rows = fetch_county(code, name)
                writer.writerows(rows)
                total_rows += len(rows)
                print(f"✓ {len(rows):,} blocks")
            except Exception as e:
                print(f"✗ ERROR: {e}")

            # Polite pause between requests to avoid rate limiting
            time.sleep(0.5)

    print(f"\nDone! {total_rows:,} total blocks → {OUTPUT}")


if __name__ == '__main__':
    main()
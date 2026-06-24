"""
fetch_apr.py

Pulls APR Table A2 from California HCD's CKAN SQL API.
Fetches ALL columns for all 58 California counties, completed units only
(Certificate of Occupancy issued), years 2020-2025.

Run from the repo root:
    python3 scripts/fetch_apr.py

Output:
    data/apr.csv  —  all columns returned by the API, paginated in full
"""

import csv
import time
import requests
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

OUTPUT      = Path('data/apr.csv')
RESOURCE_ID = 'fe505d9b-8c36-42ba-ba30-08bc4f34e022'
BASE_URL    = 'https://data.ca.gov/api/3/action/datastore_search_sql'
LIMIT       = 5000   # rows per page (CKAN max)

# ── Main ──────────────────────────────────────────────────────────────────────

def fetch_page(offset):
    """Fetch one page of APR records. Returns list of record dicts."""
    sql = (
        f'SELECT * FROM "{RESOURCE_ID}" '
        f'WHERE CAST("YEAR" AS INTEGER) >= 2020 '
        f'AND "CO_ISSUE_DT1" IS NOT NULL '
        f'LIMIT {LIMIT} OFFSET {offset}'
    )

    response = requests.get(
        BASE_URL,
        params={'sql': sql},
        timeout=60
    )
    response.raise_for_status()
    json = response.json()

    if not json.get('success'):
        raise RuntimeError(f"API error: {json.get('error')}")

    return json['result']['records']


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    offset     = 0
    total_rows = 0
    writer     = None
    file_obj   = None

    try:
        file_obj = open(OUTPUT, 'w', newline='', encoding='utf-8')

        while True:
            page_num = (offset // LIMIT) + 1
            print(f"Fetching page {page_num} (offset {offset:,})...", end=' ', flush=True)

            try:
                records = fetch_page(offset)
            except Exception as e:
                print(f"✗ ERROR: {e}")
                break

            if not records:
                print("No more records.")
                break

            # On the first page, use the record keys as CSV headers
            if writer is None:
                fieldnames = list(records[0].keys())
                writer = csv.DictWriter(file_obj, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()

            writer.writerows(records)
            total_rows += len(records)
            print(f"✓ {len(records):,} rows (total: {total_rows:,})")

            # If we got fewer rows than the limit, we've hit the last page
            if len(records) < LIMIT:
                break

            offset += LIMIT
            time.sleep(0.5)  # polite pause between pages

    finally:
        if file_obj:
            file_obj.close()

    print(f"\nDone! {total_rows:,} total APR rows → {OUTPUT}")


if __name__ == '__main__':
    main()
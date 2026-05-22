"""Build deterministic Wave 0 fixture parquet files from hand-coded test data.

Run this script to regenerate every parquet under tests/fixtures/. Lanes MUST NOT
modify the data here without orchestrator approval — these are the contract test
artifacts every lane validates against.

Usage:
    cd backend && uv run python ../tests/fixtures/build_fixtures.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from shapely import wkb
from shapely.geometry import Polygon

FIXTURES_DIR = Path(__file__).resolve().parent
REPO_ROOT = FIXTURES_DIR.parent.parent
NOW = datetime(2026, 5, 21, 3, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Deterministic per-location data. Order matches sample_addresses.csv.
# `lat`/`lon` are plausible hand-picked values, not necessarily real-world accurate.
# `building_id` and footprint geometries are synthetic and internally consistent.
# ---------------------------------------------------------------------------

LOCATIONS: list[dict] = [
    # Walmarts
    {"id": "WMART_001", "addr": "2110 W Walnut St", "city": "Rogers",      "state": "AR", "zip": "72756", "type": "retail",    "chain": "walmart", "lat": 36.3450, "lon": -94.1500, "precision": "ROOFTOP",            "building_id": "FP_WMART_001", "subtype": "supermarket",    "area_sqft": 165_000.0, "floors": 1, "height": 8.5},
    {"id": "WMART_002", "addr": "8801 Ocean Gateway",      "city": "Easton",      "state": "MD", "zip": "21601", "type": "retail",    "chain": "walmart", "lat": 38.7700, "lon": -76.0500, "precision": "ROOFTOP",            "building_id": "FP_WMART_002", "subtype": "supermarket",    "area_sqft": 175_000.0, "floors": 1, "height": 9.0},
    {"id": "WMART_003", "addr": "1331 SW Wanamaker Rd",    "city": "Topeka",      "state": "KS", "zip": "66604", "type": "retail",    "chain": "walmart", "lat": 39.0400, "lon": -95.7800, "precision": "ROOFTOP",            "building_id": "FP_WMART_003", "subtype": "supermarket",    "area_sqft": 158_000.0, "floors": 1, "height": 8.0},
    {"id": "WMART_004", "addr": "3500 College Ave",        "city": "San Diego",   "state": "CA", "zip": "92115", "type": "retail",    "chain": "walmart", "lat": 32.7600, "lon": -117.0700,"precision": "RANGE_INTERPOLATED", "building_id": "FP_WMART_004", "subtype": "supermarket",    "area_sqft": 142_000.0, "floors": 1, "height": 7.5},
    {"id": "WMART_005", "addr": "4505 Pacific Hwy SE",     "city": "Salem",       "state": "OR", "zip": "97302", "type": "retail",    "chain": "walmart", "lat": 44.9100, "lon": -123.0100,"precision": "ROOFTOP",            "building_id": "FP_WMART_005", "subtype": "supermarket",    "area_sqft": 152_000.0, "floors": 1, "height": 8.2},
    # Amazon FCs
    {"id": "AMZN_FC_001","addr": "1655 W 43rd Ave",         "city": "Kent",        "state": "WA", "zip": "98032", "type": "warehouse", "chain": "amazon",  "lat": 47.3800, "lon": -122.2400,"precision": "ROOFTOP",            "building_id": "FP_AMZN_001",  "subtype": "warehouse",      "area_sqft": 850_000.0, "floors": 1, "height": 12.0},
    {"id": "AMZN_FC_002","addr": "255 Park Center Dr",     "city": "Patterson",   "state": "CA", "zip": "95363", "type": "warehouse", "chain": "amazon",  "lat": 37.4700, "lon": -121.1300,"precision": "ROOFTOP",            "building_id": "FP_AMZN_002",  "subtype": "warehouse",      "area_sqft": 1_100_000.0,"floors": 1,"height": 13.5},
    # Chain retail
    {"id": "TGT_001",    "addr": "1015 W Sunset Blvd",      "city": "Los Angeles", "state": "CA", "zip": "90012", "type": "retail",    "chain": "target",  "lat": 34.0700, "lon": -118.2500,"precision": "ROOFTOP",            "building_id": "FP_TGT_001",   "subtype": "retail",         "area_sqft": 124_000.0, "floors": 2, "height": 9.0},
    {"id": "BBY_001",    "addr": "8225 W Bowles Ave",       "city": "Littleton",   "state": "CO", "zip": "80123", "type": "retail",    "chain": "best buy","lat": 39.6000, "lon": -105.0700,"precision": "ROOFTOP",            "building_id": "FP_BBY_001",   "subtype": "retail",         "area_sqft":  45_000.0, "floors": 1, "height": 7.0},
    {"id": "HD_001",     "addr": "3837 Veterans Memorial Hwy","city":"Ronkonkoma", "state": "NY", "zip": "11779", "type": "retail",    "chain": "home depot","lat":40.8000,"lon": -73.1100, "precision": "ROOFTOP",            "building_id": "FP_HD_001",    "subtype": "retail",         "area_sqft": 112_000.0, "floors": 1, "height": 8.5},
    {"id": "LOWE_001",   "addr": "5610 Almeda Genoa Rd",    "city": "Houston",     "state": "TX", "zip": "77048", "type": "retail",    "chain": "lowe's",  "lat": 29.6400, "lon": -95.3600, "precision": "ROOFTOP",            "building_id": "FP_LOWE_001",  "subtype": "retail",         "area_sqft": 117_000.0, "floors": 1, "height": 8.0},
    {"id": "COSTCO_001", "addr": "4849 Northern Lights Blvd","city":"Anchorage",   "state": "AK", "zip": "99508", "type": "retail",    "chain": None,      "lat": 61.1800, "lon": -149.8400,"precision": "ROOFTOP",            "building_id": "FP_COSTCO_001","subtype": "supermarket",    "area_sqft": 148_000.0, "floors": 1, "height": 9.5},
    # Small businesses
    {"id": "BAKER_001",  "addr": "200 W Mariposa Rd",       "city": "Stockton",    "state": "CA", "zip": "95207", "type": "other",     "chain": None,      "lat": 37.9700, "lon": -121.3000,"precision": "ROOFTOP",            "building_id": "FP_BAKER_001", "subtype": "commercial",     "area_sqft":   8_500.0, "floors": 2, "height": 7.5},
    {"id": "DRY_001",    "addr": "500 Elm St Suite 200",    "city": "Houston",     "state": "TX", "zip": "77002", "type": "other",     "chain": None,      "lat": 29.7600, "lon": -95.3700, "precision": "GEOMETRIC_CENTER",   "building_id": "FP_DRY_001",   "subtype": "office",         "area_sqft":  62_000.0, "floors": 12,"height": 48.0},
    {"id": "SHOP_001",   "addr": "1 Mall Drive",            "city": "Schaumburg",  "state": "IL", "zip": "60173", "type": "retail",    "chain": None,      "lat": 42.0500, "lon": -88.0300, "precision": "GEOMETRIC_CENTER",   "building_id": "FP_SHOP_001",  "subtype": "shopping_centre","area_sqft": 2_400_000.0,"floors":2,"height": 18.0},
    # TEST_* — intentional non-production rows (fictional/invalid addresses)
    {"id": "TEST_001",   "addr": "###",                     "city": "",            "state": "",   "zip": "",      "type": "other",     "chain": None,      "lat": None,    "lon": None,    "precision": "UNKNOWN",            "building_id": None,           "subtype": None,             "area_sqft": None,      "floors": None,"height": None},
    {"id": "TEST_002",   "addr": "PO Box 1234",             "city": "Anywhere",    "state": "XX", "zip": "00000", "type": "other",     "chain": None,      "lat": None,    "lon": None,    "precision": "UNKNOWN",            "building_id": None,           "subtype": None,             "area_sqft": None,      "floors": None,"height": None},
    {"id": "TEST_003",   "addr": "123 Main St",             "city": "Anytown",     "state": "IL", "zip": "60601", "type": "other",     "chain": None,      "lat": 41.8800, "lon": -87.6300, "precision": "RANGE_INTERPOLATED", "building_id": "FP_TEST_003", "subtype": "commercial",     "area_sqft":   3_200.0, "floors": 1, "height": 4.0},
    {"id": "TEST_004",   "addr": "742 Evergreen Terrace",   "city": "Springfield", "state": "IL", "zip": "62701", "type": "other",     "chain": None,      "lat": 39.7800, "lon": -89.6500, "precision": "RANGE_INTERPOLATED", "building_id": "FP_TEST_004",  "subtype": "commercial",     "area_sqft":   1_800.0, "floors": 1, "height": 4.0},
    {"id": "TEST_005",   "addr": "10810 100th Ave",         "city": "Edmonton",    "state": "AB", "zip": "99999", "type": "warehouse", "chain": "amazon",  "lat": 0.0,     "lon": 0.0,     "precision": "UNKNOWN",            "building_id": None,           "subtype": None,             "area_sqft": None,      "floors": None,"height": None},
]


def address_key(d: dict) -> str:
    return f"{d['addr'].lower().strip()}|{d['city'].lower().strip()}|{d['state'].lower().strip()}|{(d['zip'] or '').strip()}"


def apply_live_geocodes(locations: list[dict]) -> int:
    """When data/output/estimates.parquet exists, align fixture coords with the last live sample run."""
    live_path = REPO_ROOT / "data" / "output" / "estimates.parquet"
    if not live_path.exists():
        return 0
    df = pd.read_parquet(live_path)
    by_id = {str(row["location_id"]): row for _, row in df.iterrows()}
    updated = 0
    for d in locations:
        if d["id"].startswith("TEST_"):
            continue
        row = by_id.get(d["id"])
        if row is None:
            continue
        lat, lon = row.get("geocoded_lat"), row.get("geocoded_lon")
        if lat is not None and lon is not None and pd.notna(lat) and pd.notna(lon):
            d["lat"] = float(lat)
            d["lon"] = float(lon)
            updated += 1
    return updated


def square_around(lat: float, lon: float, half_deg: float = 0.0005) -> Polygon:
    """Tiny square polygon centered at (lat, lon). half_deg ~55m at mid-latitudes."""
    return Polygon([
        (lon - half_deg, lat - half_deg),
        (lon + half_deg, lat - half_deg),
        (lon + half_deg, lat + half_deg),
        (lon - half_deg, lat + half_deg),
        (lon - half_deg, lat - half_deg),
    ])


def build_normalized() -> list[dict]:
    rows = []
    for d in LOCATIONS:
        rows.append({
            "location_id": d["id"],
            "address_input": f"{d['addr']}, {d['city']}, {d['state']} {d['zip']}".strip(", "),
            "normalized_line_1": d["addr"].lower().strip(),
            "normalized_city": d["city"].lower().strip(),
            "normalized_state": d["state"].lower().strip(),
            "normalized_zip5": (d["zip"] or "")[:5],
            "address_key": address_key(d),
            "chain_token": d["chain"],
            "normalize_warnings": [],
        })
    return rows


def build_geocoded() -> list[dict]:
    """One row per unique address_key (every address here is already unique)."""
    rows = []
    seen: set[str] = set()
    for d in LOCATIONS:
        k = address_key(d)
        if k in seen:
            continue
        seen.add(k)
        ok = d["lat"] is not None and d["lon"] is not None
        rows.append({
            "address_key": k,
            "lat": d["lat"],
            "lon": d["lon"],
            "precision": d["precision"],
            "provider": "google_places" if d["chain"] else "google_geocoding",
            "place_id": f"placeid_{d['id']}" if ok else None,
            "formatted_address": d["addr"] if ok else None,
            "raw_response_hash": f"hash_{d['id']}" if ok else None,
            "status": "ok" if ok else "failed",
            "error": None if ok else "could not geocode",
        })
    return rows


def build_footprints() -> list[dict]:
    """One footprint per matched location (skip the unmatched/broken ones)."""
    rows = []
    for d in LOCATIONS:
        if d["building_id"] is None or d["lat"] is None:
            continue
        poly = square_around(d["lat"], d["lon"])
        minx, miny, maxx, maxy = poly.bounds
        rows.append({
            "id": d["building_id"],
            "geometry_wkb": wkb.dumps(poly),
            "bbox_xmin": minx,
            "bbox_ymin": miny,
            "bbox_xmax": maxx,
            "bbox_ymax": maxy,
            "height": d["height"],
            "num_floors": d["floors"],
            "overture_class": "commercial",
            "overture_subtype": d["subtype"],
            "overture_source": "fixture",
            "overture_version": 1,
            "overture_update_time": NOW,
        })
    return rows


def build_estimates(run_id: str) -> list[dict]:
    rows = []
    for d in LOCATIONS:
        ok = d["building_id"] is not None
        flags: list[str] = []
        flag_cols = {f"flag_{k}": False for k in (
            "no_building_match", "low_geocode_precision", "multi_building_parcel",
            "old_footprint", "nearest_fallback", "area_out_of_range", "height_outlier",
            "missing_floors_tall_building", "geocode_failed", "suite_or_tenant_address",
        )}
        if not ok:
            flags += ["NO_BUILDING_MATCH", "GEOCODE_FAILED"]
            flag_cols["flag_no_building_match"] = True
            flag_cols["flag_geocode_failed"] = True
            confidence = "unmatched"
            match_method = "unmatched"
        else:
            if d["precision"] not in ("ROOFTOP", "RANGE_INTERPOLATED"):
                flags.append("LOW_GEOCODE_PRECISION")
                flag_cols["flag_low_geocode_precision"] = True
            if d["addr"] and " suite " in d["addr"].lower():
                flags.append("SUITE_OR_TENANT_ADDRESS")
                flag_cols["flag_suite_or_tenant_address"] = True
            # Confidence rules:
            if flags:
                confidence = "medium"
            else:
                confidence = "high"
            match_method = "within"
        estimated = (d["area_sqft"] * (d["floors"] or 1)) if (d["area_sqft"] and ok) else None
        rows.append({
            "location_id": d["id"],
            "address_input": f"{d['addr']}, {d['city']}, {d['state']} {d['zip']}".strip(", "),
            "address_key": address_key(d),
            "location_type": d["type"],
            "geocoded_lat": d["lat"],
            "geocoded_lon": d["lon"],
            "geocoder_precision": d["precision"],
            "geocoder_provider": ("google_places" if d["chain"] else "google_geocoding") if d["lat"] is not None else None,
            "formatted_address": d["addr"] if d["lat"] is not None else None,
            "building_id": d["building_id"],
            "match_method": match_method,
            "multi_building_count": 1 if ok else 0,
            "candidates_json": json.dumps([{
                "building_id": d["building_id"],
                "area_sqft": d["area_sqft"],
                "distance_m": 0.0,
                "overture_class": "commercial",
                "overture_subtype": d["subtype"],
                "is_chosen": True,
            }]) if ok else "[]",
            "footprint_area_sqft": d["area_sqft"],
            "num_floors_used": d["floors"],
            "floors_source": "overture_num_floors" if ok else None,
            "raw_overture_height": d["height"],
            "raw_overture_num_floors": d["floors"],
            "estimated_sqft": estimated,
            "overture_class": "commercial" if ok else None,
            "overture_subtype": d["subtype"],
            "overture_source": "fixture" if ok else None,
            "overture_update_time": NOW if ok else None,
            "overture_release": "fixture-1.0",
            "confidence": confidence,
            "flags_json": json.dumps(flags),
            **flag_cols,
            "pipeline_run_id": run_id,
        })
    return rows


def build_qa_reviews_empty() -> list[dict]:
    return []  # empty, but with correct schema (handled by io.write_parquet)


def main() -> None:
    print(f"Writing fixtures to {FIXTURES_DIR}")
    run_id = "fixture-run-001"
    n = apply_live_geocodes(LOCATIONS)
    if n:
        print(f"  aligned {n} location coords from data/output/estimates.parquet")

    fixtures = {
        "normalized.parquet": build_normalized(),
        "geocoded.parquet": build_geocoded(),
        "footprints.parquet": build_footprints(),
        "estimates.parquet": build_estimates(run_id),
        "qa_reviews.parquet": build_qa_reviews_empty(),
    }

    for name, rows in fixtures.items():
        path = FIXTURES_DIR / name
        if rows:
            table = pa.Table.from_pylist(rows)
        else:
            # Empty fallback: write a 0-row table with at least one column.
            table = pa.table({"_empty": pa.array([], type=pa.string())})
        pq.write_table(table, path)
        print(f"  wrote {name:24s} rows={len(rows):4d}")

    print("Done.")


if __name__ == "__main__":
    main()

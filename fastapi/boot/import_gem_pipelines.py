#!/usr/bin/env python3
"""
Import Global Energy Monitor (GEM) pipeline data into PostGIS.

Data source:
  Global Gas Infrastructure Tracker (GGIT)
  https://globalenergymonitor.org/projects/global-gas-infrastructure-tracker/
  License: CC BY 4.0

Download steps:
  1. Go to the URL above → "Download Data"
  2. Download "Global Gas Infrastructure Tracker – Pipelines" as Excel/CSV
  3. For GeoJSON: use the Europe Gas Tracker interactive map → export,
     OR use the Tools4MSP mirror:
     https://geoplatform.tools4msp.eu/layers/geonode:Gas_pipelines
  4. Place files in ./data/

Usage:
  pip install psycopg2-binary geopandas shapely pandas openpyxl
  python import_gem_pipelines.py --dsn "postgresql://user:pass@localhost/gasdb"
"""

import argparse
import json
import os
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from shapely.geometry import LineString, MultiLineString, mapping

# =============================================================
# GEM field name → our schema column mapping
# Column names vary slightly between GEM releases; adjust here.
# =============================================================
GEM_PIPELINE_FIELD_MAP = {
    # GEM field               → our column
    "GEM Unit ID":              "gem_id",
    "Pipeline Name":            "pipeline_name",
    "Segment Name":             "source_name",
    "Operator":                 "operator",
    "Status":                   "gem_status",
    "Diameter (mm)":            "diameter_mm",
    "Max. Capacity (Mm3/d)":    "capacity_mcm_d",
    "Length (km)":              "length_km",
    "Start Year":               "year_built",
    "Countries":                "countries_raw",
}

GEM_STATUS_MAP = {
    "Operating":        "operating",
    "Construction":     "construction",
    "Pre-construction": "planned",
    "Proposed":         "planned",
    "Announced":        "planned",
    "Cancelled":        "decommissioned",
    "Shelved":          "decommissioned",
    "Retired":          "decommissioned",
    "Idle":             "decommissioned",
}

# Countries we care about for the Europe scope
EUROPE_COUNTRIES = {
    "AT","BE","BG","CH","CY","CZ","DE","DK","EE","ES","FI","FR",
    "GB","GR","HR","HU","IE","IS","IT","LT","LU","LV","MK","MT",
    "NL","NO","PL","PT","RO","RS","SE","SI","SK","TR","UA","AL",
    "BA","ME","MD","BY","DZ","LY","EG","MA","AZ","GE","AM",
}


def parse_countries(raw: str) -> list[str]:
    """Extract ISO-2 country codes from GEM's free-text country field."""
    if not raw or pd.isna(raw):
        return []
    # GEM uses full names: "Germany, France, Belgium"
    # We keep as-is and let the caller map to ISO2 if needed.
    # For now return the raw split list.
    return [c.strip() for c in str(raw).split(",") if c.strip()]


def gem_geojson_to_linestrings(geojson_path: str) -> gpd.GeoDataFrame:
    """Load GEM pipeline GeoJSON and normalise to LineStrings in EPSG:4326."""
    gdf = gpd.read_file(geojson_path)
    gdf = gdf.to_crs(epsg=4326)

    # Explode MultiLineStrings to individual LineStrings
    gdf = gdf.explode(index_parts=False).reset_index(drop=True)

    # Ensure all geometries are LineString
    gdf = gdf[gdf.geometry.geom_type == "LineString"].copy()

    print(f"  Loaded {len(gdf)} pipeline segments from GeoJSON")
    return gdf


def ensure_nodes_for_endpoints(cur, segments: list[dict]) -> dict:
    """
    For each unique endpoint coordinate in the segment list,
    ensure a pipeline_nodes row exists (type='intersection').
    Returns mapping: (lon, lat) → node_id
    """
    # Collect all unique endpoints
    endpoints: set[tuple[float, float]] = set()
    for seg in segments:
        coords = seg["coords"]
        if coords:
            endpoints.add((round(coords[0][0], 6), round(coords[0][1], 6)))
            endpoints.add((round(coords[-1][0], 6), round(coords[-1][1], 6)))

    coord_to_id: dict[tuple[float, float], int] = {}

    for lon, lat in endpoints:
        # Check if a node already exists within 500m
        cur.execute("""
            SELECT id FROM pipeline_nodes
            WHERE ST_DWithin(
                geom::geography,
                ST_SetSRID(ST_Point(%s, %s), 4326)::geography,
                500
            )
            ORDER BY geom <-> ST_SetSRID(ST_Point(%s, %s), 4326)
            LIMIT 1
        """, (lon, lat, lon, lat))
        row = cur.fetchone()
        if row:
            coord_to_id[(lon, lat)] = row[0]
        else:
            cur.execute("""
                INSERT INTO pipeline_nodes
                    (name, node_type, geom, status)
                VALUES
                    (%s, 'intersection',
                     ST_SetSRID(ST_Point(%s, %s), 4326),
                     'operating')
                RETURNING id
            """, (f"junction_{lon}_{lat}", lon, lat))
            coord_to_id[(lon, lat)] = cur.fetchone()[0]

    print(f"  Ensured {len(coord_to_id)} endpoint nodes")
    return coord_to_id


def import_geojson(conn, geojson_path: str, europe_only: bool = True):
    """Main import: GeoJSON pipeline segments → pipeline_edges + auto nodes."""
    print(f"\nImporting pipeline GeoJSON: {geojson_path}")
    gdf = gem_geojson_to_linestrings(geojson_path)

    if europe_only:
        # Rough Europe bounding box filter
        europe_bbox = (-30, 20, 60, 75)
        gdf = gdf.cx[europe_bbox[0]:europe_bbox[2], europe_bbox[1]:europe_bbox[3]]
        print(f"  Filtered to Europe bbox: {len(gdf)} segments")

    # Build list of segment dicts
    segments = []
    for _, row in gdf.iterrows():
        coords = list(row.geometry.coords)
        # Map GEM status
        raw_status = str(row.get("Status", "Operating"))
        status = GEM_STATUS_MAP.get(raw_status, "operating")

        segments.append({
            "coords":        coords,
            "gem_id":        row.get("GEM Unit ID"),
            "pipeline_name": row.get("Pipeline Name"),
            "source_name":   row.get("Segment Name") or row.get("Pipeline Name"),
            "operator":      row.get("Operator"),
            "status":        status,
            "diameter_mm":   _safe_int(row.get("Diameter (mm)")),
            "capacity_mcm_d":_safe_float(row.get("Max. Capacity (Mm3/d)")),
            "length_km":     _safe_float(row.get("Length (km)")),
            "year_built":    _safe_int(row.get("Start Year")),
            "countries_raw": str(row.get("Countries", "")) or "",
        })

    with conn.cursor() as cur:
        # Ensure nodes exist for all endpoints
        coord_to_id = ensure_nodes_for_endpoints(cur, segments)

        # Insert edges
        inserted = 0
        skipped = 0
        for seg in segments:
            coords = seg["coords"]
            if not coords or len(coords) < 2:
                skipped += 1
                continue

            start_coord = (round(coords[0][0], 6), round(coords[0][1], 6))
            end_coord   = (round(coords[-1][0], 6), round(coords[-1][1], 6))

            source_id = coord_to_id.get(start_coord)
            target_id = coord_to_id.get(end_coord)
            if not source_id or not target_id:
                skipped += 1
                continue

            geom_wkt = LineString(coords).wkt
            countries = parse_countries(seg["countries_raw"])

            cur.execute("""
                INSERT INTO pipeline_edges (
                    source, target, geom,
                    pipeline_name, source_name, operator, status,
                    diameter_mm, capacity_mcm_d, length_km, year_built,
                    country_codes, gem_id,
                    tariff_type
                ) VALUES (
                    %s, %s, ST_GeomFromText(%s, 4326),
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s,
                    'estimated'
                )
                ON CONFLICT DO NOTHING
            """, (
                source_id, target_id, geom_wkt,
                seg["pipeline_name"], seg["source_name"], seg["operator"], seg["status"],
                seg["diameter_mm"], seg["capacity_mcm_d"], seg["length_km"], seg["year_built"],
                countries, seg["gem_id"],
            ))
            inserted += 1

        conn.commit()
        print(f"  Inserted {inserted} edges, skipped {skipped}")

        # Recompute all costs
        print("  Recomputing edge costs...")
        cur.execute("SELECT recompute_edge_costs()")
        conn.commit()
        print("  Done.")


def import_known_nodes(conn):
    """
    Seed the database with well-known hubs and LNG terminals.
    These are manually curated — don't rely on GEM geometry endpoints for these.
    """
    known_nodes = [
        # (name, node_type, country, lon, lat, is_hub, hub_code, lng_cap, lng_type)
        ("TTF Hub (Gasunie)",      "hub",          "NL",  5.291, 52.132, True,  "TTF",    None, None),
        ("NCG Hub",                "hub",          "DE",  9.993, 53.565, True,  "NCG",    None, None),
        ("Gaspool Hub",            "hub",          "DE", 13.405, 52.520, True,  "GPL",    None, None),
        ("NBP (NTS)",              "hub",          "GB", -0.118, 51.509, True,  "NBP",    None, None),
        ("PEG Nord Hub",           "hub",          "FR",  2.350, 48.861, True,  "PEGNORD",None, None),
        ("Zeebrugge Hub",          "hub",          "BE",  3.200, 51.340, True,  "ZEE",    None, None),
        ("Baumgarten Hub",         "hub",          "AT", 16.906, 48.218, True,  "BAUM",   None, None),

        # LNG import terminals (Europe)
        ("Gate Terminal Rotterdam","lng_terminal",  "NL",  4.055, 51.958, False, None,   12.0, "import"),
        ("Zeebrugge LNG",          "lng_terminal",  "BE",  3.196, 51.324, False, None,    9.0, "import"),
        ("Eemshaven FSRU",         "lng_terminal",  "NL",  6.836, 53.463, False, None,    8.0, "import"),
        ("Montoir LNG",            "lng_terminal",  "FR", -2.154, 47.277, False, None,   10.0, "import"),
        ("Fos Cavaou",             "lng_terminal",  "FR",  4.860, 43.370, False, None,    8.25,"import"),
        ("Sagunto LNG",            "lng_terminal",  "ES", -0.196, 39.660, False, None,    8.0, "import"),
        ("Huelva LNG",             "lng_terminal",  "ES", -6.960, 37.278, False, None,    5.5, "import"),
        ("Mugardos LNG",           "lng_terminal",  "ES", -8.250, 43.467, False, None,    3.5, "import"),
        ("Panigaglia LNG",         "lng_terminal",  "IT",  9.875, 44.063, False, None,    3.4, "import"),
        ("OLT Offshore LNG",       "lng_terminal",  "IT", 10.127, 43.614, False, None,    3.75,"import"),
        ("Revythoussa LNG",        "lng_terminal",  "GR", 23.395, 37.921, False, None,    5.3, "import"),
        ("Świnoujście LNG",        "lng_terminal",  "PL", 14.240, 53.914, False, None,    6.2, "import"),
        ("Klaipėda FSRU",          "lng_terminal",  "LT", 21.113, 55.709, False, None,    4.0, "import"),

        # Key compressor / border crossing points
        ("Emden entry point",      "border_crossing","DE",  7.206, 53.367, False, None,   None, None),
        ("Dornum entry point",     "border_crossing","DE",  7.429, 53.642, False, None,   None, None),
        ("Eynatten (Belgium)",     "border_crossing","BE",  6.073, 50.687, False, None,   None, None),
        ("Zelzate (Belgium)",      "border_crossing","BE",  3.820, 51.200, False, None,   None, None),
        ("Tarvisio entry",         "border_crossing","IT", 13.580, 46.508, False, None,   None, None),
        ("Almería (Medgaz)",       "border_crossing","ES", -2.455, 36.835, False, None,   None, None),
        ("Mazara del Vallo",       "border_crossing","IT", 12.591, 37.649, False, None,   None, None),

        # LNG export sources (outside Europe)
        ("Sabine Pass LNG",        "lng_terminal",  "US", -93.872, 29.727, False, None,  75.0, "export"),
        ("Freeport LNG",           "lng_terminal",  "US", -95.356, 28.944, False, None,  20.0, "export"),
        ("Corpus Christi LNG",     "lng_terminal",  "US", -97.388, 27.840, False, None,  15.0, "export"),
        ("Ras Laffan LNG",         "lng_terminal",  "QA",  51.556, 25.904, False, None, 110.0, "export"),
        ("Arzew LNG (Algeria)",    "lng_terminal",  "DZ", -0.315, 35.840, False, None,   14.0, "export"),
        ("Skikda LNG (Algeria)",   "lng_terminal",  "DZ",  6.899, 36.876, False, None,    4.0, "export"),
        ("Bonny Island NLNG",      "lng_terminal",  "NG",  7.148,  4.430, False, None,   30.0, "export"),
        ("Gorgon LNG",             "lng_terminal",  "AU", 114.131,-20.444,False, None,   15.6, "export"),

        # Gas producing fields / hubs
        ("Hassi R'Mel (Algeria)",  "production",    "DZ",  3.265, 32.934, False, None,   None, None),
        ("Henry Hub (Louisiana)",  "hub",           "US", -93.313, 29.759, True,  "HH",  None, None),
        ("South Pars (Qatar)",     "production",    "QA",  52.200, 26.500, False, None,  None, None),
        ("Troll Field (Norway)",   "production",    "NO",   3.720, 60.645, False, None,  None, None),
    ]

    with conn.cursor() as cur:
        for row in known_nodes:
            name, ntype, country, lon, lat, is_hub, hub_code, lng_cap, lng_type = row
            cur.execute("""
                INSERT INTO pipeline_nodes
                    (name, node_type, country, geom, status,
                     is_trading_hub, hub_code,
                     lng_capacity_bcm, lng_type)
                VALUES (%s, %s, %s,
                        ST_SetSRID(ST_Point(%s, %s), 4326),
                        'operating',
                        %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (name, ntype, country, lon, lat,
                  is_hub, hub_code, lng_cap, lng_type))

        conn.commit()
        print(f"Seeded {len(known_nodes)} known nodes (hubs, terminals, sources)")


def _safe_int(val) -> int | None:
    try:
        return int(float(val)) if val and not pd.isna(val) else None
    except (ValueError, TypeError):
        return None

def _safe_float(val) -> float | None:
    try:
        return float(val) if val and not pd.isna(val) else None
    except (ValueError, TypeError):
        return None


def main():
    parser = argparse.ArgumentParser(description="Import GEM pipeline data into PostGIS")
    parser.add_argument("--dsn", required=True,
                        help="PostgreSQL DSN, e.g. postgresql://user:pass@localhost/gasdb")
    parser.add_argument("--geojson", default="./data/europe_gas_pipelines.geojson",
                        help="Path to GEM pipeline GeoJSON file")
    parser.add_argument("--seed-nodes-only", action="store_true",
                        help="Only seed known nodes, skip GeoJSON import")
    args = parser.parse_args()

    conn = psycopg2.connect(args.dsn)
    print(f"Connected to database")

    print("\n--- Seeding known nodes ---")
    import_known_nodes(conn)

    if not args.seed_nodes_only:
        if not Path(args.geojson).exists():
            print(f"\nGeoJSON not found at {args.geojson}")
            print("Download from: https://globalenergymonitor.org/projects/global-gas-infrastructure-tracker/")
            print("Or: https://geoplatform.tools4msp.eu/layers/geonode:Gas_pipelines")
            print("\nRunning with seed nodes only.")
        else:
            print("\n--- Importing GeoJSON pipeline segments ---")
            import_geojson(conn, args.geojson)

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()

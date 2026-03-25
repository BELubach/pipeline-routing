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

"""

import argparse
from pathlib import Path

import geopandas as gpd
import pandas as pd
import psycopg2
from shapely.geometry import LineString

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


def import_geojson(conn, geojson_path: str):
    """Main import: GeoJSON pipeline segments → pipeline_edges + auto nodes."""
    print(f"\nImporting pipeline GeoJSON: {geojson_path}")
    gdf = gem_geojson_to_linestrings(geojson_path)


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
    args = parser.parse_args()

    conn = psycopg2.connect(args.dsn)
    print(f"Connected to database")

    if not Path(args.geojson).exists():
        print(f"\nGeoJSON not found at {args.geojson}")
        print("Download from: https://globalenergymonitor.org/projects/global-gas-infrastructure-tracker/")
        print("Or: https://geoplatform.tools4msp.eu/layers/geonode:Gas_pipelines")
        print("\nRunning with seed nodes only.")

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()

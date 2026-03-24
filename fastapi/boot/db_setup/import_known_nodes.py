

import argparse
from pathlib import Path

import geopandas as gpd
import pandas as pd
import psycopg2
from shapely.geometry import LineString

from boot.db_setup.import_gem_pipelines import import_geojson


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



def main():
    print("\n--- Importing GeoJSON pipeline segments ---")


    conn = psycopg2.connect()
    import_known_nodes(conn)
    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()

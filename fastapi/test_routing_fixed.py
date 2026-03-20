#!/usr/bin/env python3
"""Test routing after fixing self-loops"""

import psycopg2
from app.core.config import settings

dsn = (
    f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)

conn = psycopg2.connect(dsn)
cur = conn.cursor()

print("\n=== Testing Route After Self-Loop Fix ===\n")

# First recreate the functions
print("1. Loading fixed SQL functions...")
with open('boot/pipeline_functions.sql', 'r') as f:
    sql = f.read()
    cur.execute(sql)
    conn.commit()
print("   ✅ Functions recreated\n")

print("2. Testing route_by_coordinates()...")
cur.execute("""
    SELECT seq, node_id, node_name, edge_id, 
           ROUND(cumulative_cost::numeric, 4) as total_cost,
           ROUND(segment_km::numeric, 2) as km
    FROM route_by_coordinates(
        6.83, 53.4,  -- Groningen area
        6.78, 52.7,  -- Zwolle area
        'composite',
        200.0
    )
    ORDER BY seq
""")

rows = cur.fetchall()
if rows:
    print(f"   ✅ Found route with {len(rows)} segments!\n")
    print("   Route details:")
    print("   Seq | Node ID | Node Name                    | Edge ID | Total Cost | Segment KM")
    print("   " + "-" * 85)
    for row in rows:
        seq, node_id, node_name, edge_id, cost, km = row
        node_name = (node_name or "")[:30].ljust(30)
        print(f"   {seq:3d} | {node_id or 0:7d} | {node_name} | {edge_id or 0:7d} | {cost or 0:10.4f} | {km or 0:10.2f}")
    
    final_cost = rows[-1][4]
    total_km = sum(row[5] or 0 for row in rows)
    print(f"\n   Total distance: {total_km:.2f} km")
    print(f"   Total cost: {final_cost:.4f} €/MWh")
else:
    print("   ❌ No route found")

cur.close()
conn.close()

print("\n✅ Test complete!")

import psycopg2
from app.core.config import settings

dsn = (
    f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)

conn = psycopg2.connect(dsn)
cur = conn.cursor()

print("\n=== 1. Nodes in Netherlands ===")
cur.execute("""
    SELECT COUNT(*) FROM pipeline_nodes
    WHERE ST_Contains(ST_MakeEnvelope(3.0, 50.0, 7.5, 54.0, 4326), geom)
""")
print(f"Nodes in NL bbox: {cur.fetchone()[0]}")

print("\n=== 2. Total Edges ===")
cur.execute("SELECT COUNT(*) FROM pipeline_edges")
print(f"Total edges: {cur.fetchone()[0]}")

print("\n=== 3. Edge Cost Status ===")
cur.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(cost_distance_km) as has_distance,
        COUNT(cost_composite) as has_composite,
        ROUND(AVG(cost_distance_km)::numeric, 2) as avg_distance,
        ROUND(AVG(cost_composite)::numeric, 4) as avg_composite
    FROM pipeline_edges
""")
row = cur.fetchone()
print(f"Total edges: {row[0]}")
print(f"Has distance cost: {row[1]}")
print(f"Has composite cost: {row[2]}")
print(f"Avg distance (km): {row[3]}")
print(f"Avg composite cost: {row[4]}")

print("\n=== 4. Sample Edges ===")
cur.execute("""
    SELECT id, source, target, pipeline_name, 
           ROUND(cost_distance_km::numeric, 2), 
           ROUND(cost_composite::numeric, 4)
    FROM pipeline_edges 
    LIMIT 3
""")
for row in cur.fetchall():
    print(f"Edge {row[0]}: {row[1]}->{row[2]} | {row[3]} | dist={row[4]}km, cost={row[5]}")

print("\n=== 5. Nearest Nodes to Test Coordinates (6.83, 53.4) ===")
cur.execute("""
    SELECT id, name, node_type,
           ROUND((ST_Distance(
               geom::geography,
               ST_SetSRID(ST_Point(6.83, 53.4), 4326)::geography
           ) / 1000.0)::numeric, 2) AS distance_km
    FROM pipeline_nodes
    WHERE ST_DWithin(
        geom::geography,
        ST_SetSRID(ST_Point(6.83, 53.4), 4326)::geography,
        200000
    )
    ORDER BY geom <-> ST_SetSRID(ST_Point(6.83, 53.4), 4326)
    LIMIT 5
""")
rows = cur.fetchall()
if rows:
    print(f"Found {len(rows)} nodes within 200km:")
    for row in rows:
        print(f"  Node {row[0]}: {row[1]} ({row[2]}) - {row[3]}km away")
else:
    print("❌ NO NODES FOUND within 200km!")

print("\n=== 6. Test nearest_node() Function ===")
try:
    cur.execute("SELECT * FROM nearest_node(6.83, 53.4, 200, NULL)")
    rows = cur.fetchall()
    if rows:
        print(f"nearest_node() returned {len(rows)} results:")
        for row in rows:
            print(f"  Node {row[0]}: {row[1]} ({row[2]}) - {row[3]}km away")
    else:
        print("❌ nearest_node() returned no results!")
except Exception as e:
    print(f"❌ nearest_node() function error: {e}")

cur.close()
conn.close()

print("\n✅ Diagnostic complete!")

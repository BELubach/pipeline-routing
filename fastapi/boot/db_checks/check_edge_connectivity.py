
import psycopg2
from app.core.config import settings

dsn = (
    f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)

conn = psycopg2.connect(dsn)
cur = conn.cursor()

print("\n=== Edge Validity Check ===")

print("\n1. Self-loops (invalid for routing):")
cur.execute("SELECT COUNT(*) FROM pipeline_edges WHERE source = target")
self_loops = cur.fetchone()[0]
print(f"   {self_loops} self-loop edges")

print("\n2. Valid edges (source != target):")
cur.execute("SELECT COUNT(*) FROM pipeline_edges WHERE source != target")
valid_edges = cur.fetchone()[0]
print(f"   {valid_edges} valid edges")

print("\n3. Sample valid edges:")
cur.execute("""
    SELECT id, source, target, pipeline_name, 
           ROUND(cost_distance_km::numeric, 2), 
           ROUND(cost_composite::numeric, 4)
    FROM pipeline_edges 
    WHERE source != target
    LIMIT 5
""")
for row in cur.fetchall():
    print(f"   Edge {row[0]}: {row[1]}->{row[2]} | {row[3]} | dist={row[4]}km, cost={row[5]}")

print("\n4. Check if nodes are connected:")
cur.execute("""
    SELECT COUNT(DISTINCT source) as unique_sources,
           COUNT(DISTINCT target) as unique_targets
    FROM pipeline_edges
    WHERE source != target
""")
row = cur.fetchone()
print(f"   Unique source nodes: {row[0]}")
print(f"   Unique target nodes: {row[1]}")

print("\n5. Check edges from nearest node (6679):")
cur.execute("""
    SELECT COUNT(*) FROM pipeline_edges 
    WHERE (source = 6679 OR target = 6679) AND source != target
""")
edges_from_6679 = cur.fetchone()[0]
print(f"   Node 6679 has {edges_from_6679} valid edges")

if edges_from_6679 > 0:
    cur.execute("""
        SELECT id, source, target, ROUND(cost_composite::numeric, 4)
        FROM pipeline_edges 
        WHERE (source = 6679 OR target = 6679) AND source != target
        LIMIT 3
    """)
    print("   Sample edges from node 6679:")
    for row in cur.fetchall():
        print(f"      Edge {row[0]}: {row[1]}->{row[2]} cost={row[3]}")

print("\n6. Test pgRouting directly with two nearby nodes:")
cur.execute("""
    SELECT source, target 
    FROM pipeline_edges 
    WHERE source != target 
    LIMIT 2
""")
nodes = cur.fetchall()
if len(nodes) >= 2:
    node1, node2 = nodes[0][0], nodes[1][1]
    print(f"   Testing route between node {node1} and {node2}:")
    
    try:
        cur.execute("""
            SELECT * FROM pgr_dijkstra(
                'SELECT id, source, target, cost_composite as cost FROM pipeline_edges WHERE source != target',
                %s, %s,
                directed := false
            )
        """, (node1, node2))
        route = cur.fetchall()
        print(f"   ✅ pgRouting found path with {len(route)} segments")
    except Exception as e:
        print(f"   ❌ pgRouting error: {e}")

cur.close()
conn.close()

print("\n✅ Edge connectivity check complete!")

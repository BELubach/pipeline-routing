import psycopg2
from app.core.config import settings

dsn = (
    f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)

conn = psycopg2.connect(dsn)
cur = conn.cursor()

print("\n=== Detailed Routing Diagnostic ===\n")

start_lon, start_lat = 6.83, 53.4
end_lon, end_lat = 6.78, 52.7

print(f"Start: ({start_lon}, {start_lat})")
print(f"End:   ({end_lon}, {end_lat})\n")

# Step 1: Find nearest start node
print("STEP 1: Find nearest node to START point")
cur.execute("""
    SELECT node_id, name, node_type, distance_km 
    FROM nearest_node(%s, %s, 200, NULL)
    LIMIT 1
""", (start_lon, start_lat))
start_result = cur.fetchone()
if start_result:
    start_node_id, start_name, start_type, start_dist = start_result
    print(f"  ✅ Found: Node {start_node_id} '{start_name}' ({start_type}) - {start_dist}km away\n")
else:
    print("  ❌ No start node found!\n")
    exit(1)

# Step 2: Find nearest end node
print("STEP 2: Find nearest node to END point")
cur.execute("""
    SELECT node_id, name, node_type, distance_km 
    FROM nearest_node(%s, %s, 200, NULL)
    LIMIT 1
""", (end_lon, end_lat))
end_result = cur.fetchone()
if end_result:
    end_node_id, end_name, end_type, end_dist = end_result
    print(f"  ✅ Found: Node {end_node_id} '{end_name}' ({end_type}) - {end_dist}km away\n")
else:
    print("  ❌ No end node found!\n")
    exit(1)

# Step 3: Check if these nodes have valid edges
print(f"STEP 3: Check edges for start node {start_node_id}")
cur.execute("""
    SELECT COUNT(*) FROM pipeline_edges 
    WHERE (source = %s OR target = %s) 
      AND source != target
      AND status IN ('operating', 'construction')
""", (start_node_id, start_node_id))
start_edges = cur.fetchone()[0]
print(f"  Node {start_node_id} has {start_edges} valid edges\n")

print(f"STEP 4: Check edges for end node {end_node_id}")
cur.execute("""
    SELECT COUNT(*) FROM pipeline_edges 
    WHERE (source = %s OR target = %s) 
      AND source != target
      AND status IN ('operating', 'construction')
""", (end_node_id, end_node_id))
end_edges = cur.fetchone()[0]
print(f"  Node {end_node_id} has {end_edges} valid edges\n")

if start_edges == 0 or end_edges == 0:
    print("❌ One or both nodes have no valid edges - cannot route!\n")
    exit(1)

# Step 5: Try direct pgRouting call
print(f"STEP 5: Try pgr_dijkstra directly from {start_node_id} to {end_node_id}")
try:
    cur.execute("""
        SELECT COUNT(*) FROM pgr_dijkstra(
            'SELECT id, source, target, cost_composite as cost, reverse_cost_composite as reverse_cost
             FROM pipeline_edges
             WHERE source != target
               AND status IN (''operating'', ''construction'')
               AND cost_composite > 0
               AND reverse_cost_composite > 0',
            %s, %s,
            directed := false
        )
    """, (start_node_id, end_node_id))
    route_segments = cur.fetchone()[0]
    if route_segments > 0:
        print(f"  ✅ pgRouting found path with {route_segments} segments!\n")
    else:
        print(f"  ❌ pgRouting returned 0 segments - nodes may not be connected\n")
except Exception as e:
    print(f"  ❌ pgRouting error: {e}\n")

# Step 6: Check network connectivity
print("STEP 6: Check if nodes are in same connected component")
try:
    cur.execute("""
        WITH RECURSIVE reachable AS (
            -- Start from start_node_id
            SELECT DISTINCT 
                CASE WHEN source = %s THEN target ELSE source END as node_id,
                0 as depth
            FROM pipeline_edges
            WHERE (source = %s OR target = %s)
              AND source != target
              AND status IN ('operating', 'construction')
            
            UNION
            
            -- Recursively find connected nodes (limit depth to prevent infinite loops)
            SELECT DISTINCT
                CASE WHEN e.source = r.node_id THEN e.target ELSE e.source END,
                r.depth + 1
            FROM reachable r
            JOIN pipeline_edges e ON (e.source = r.node_id OR e.target = r.node_id)
            WHERE r.depth < 20  -- Limit search depth
              AND e.source != e.target
              AND e.status IN ('operating', 'construction')
        )
        SELECT COUNT(*) FROM reachable WHERE node_id = %s
    """, (start_node_id, start_node_id, start_node_id, end_node_id))
    connected = cur.fetchone()[0]
    if connected > 0:
        print(f"  ✅ End node IS reachable from start node (within 20 hops)\n")
    else:
        print(f"  ❌ End node NOT reachable from start node - disconnected network!\n")
        print(f"     This means the pipeline network has isolated components.\n")
except Exception as e:
    print(f"  ⚠️  Connectivity check failed: {e}\n")

# Step 7: Check total connected components
print("STEP 7: Analyze network connectivity")
cur.execute("""
    SELECT COUNT(DISTINCT source) + COUNT(DISTINCT target) as total_nodes_in_edges
    FROM pipeline_edges
    WHERE source != target AND status IN ('operating', 'construction')
""")
nodes_in_graph = cur.fetchone()[0]
print(f"  Total nodes participating in valid edges: {nodes_in_graph}\n")

cur.close()
conn.close()

print("✅ Diagnostic complete!")

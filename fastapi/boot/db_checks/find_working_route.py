import psycopg2
from app.core.config import settings

dsn = (
    f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)

conn = psycopg2.connect(dsn)
cur = conn.cursor()

print("\n=== Finding Connected Nodes for Testing ===\n")

# Strategy: Find a node with many edges, then find another node reachable from it
print("Step 1: Find a well-connected node in Netherlands")
cur.execute("""
    SELECT n.id, n.name, n.node_type, COUNT(e.id) as edge_count,
           ST_X(n.geom) as lon, ST_Y(n.geom) as lat
    FROM pipeline_nodes n
    JOIN pipeline_edges e ON (e.source = n.id OR e.target = n.id)
    WHERE ST_Contains(ST_MakeEnvelope(3.0, 50.0, 7.5, 54.0, 4326), n.geom)
      AND e.source != e.target
      AND e.status IN ('operating', 'construction')
    GROUP BY n.id, n.name, n.node_type, n.geom
    ORDER BY edge_count DESC
    LIMIT 1
""")
hub_node = cur.fetchone()
if not hub_node:
    print("❌ No well-connected nodes found!")
    exit(1)

hub_id, hub_name, hub_type, edge_count, hub_lon, hub_lat = hub_node
print(f"  Found hub: Node {hub_id} '{hub_name}' ({hub_type})")
print(f"  Location: ({hub_lon:.4f}, {hub_lat:.4f})")
print(f"  Connected to {edge_count} edges\n")

# Find a node within 2-3 hops that's at least 50km away
print("Step 2: Find a distant but connected node")
cur.execute("""
    WITH RECURSIVE reachable AS (
        -- Start from hub
        SELECT DISTINCT 
            CASE WHEN source = %s THEN target ELSE source END as node_id,
            1 as depth,
            e.id as via_edge
        FROM pipeline_edges e
        WHERE (source = %s OR target = %s)
          AND source != target
          AND status IN ('operating', 'construction')
        
        UNION
        
        -- Find nodes 2-3 hops away
        SELECT DISTINCT
            CASE WHEN e.source = r.node_id THEN e.target ELSE e.source END as node_id,
            r.depth + 1,
            e.id
        FROM reachable r
        JOIN pipeline_edges e ON (e.source = r.node_id OR e.target = r.node_id)
        WHERE r.depth < 3
          AND e.source != e.target
          AND e.status IN ('operating', 'construction')
    )
    SELECT DISTINCT r.node_id, n.name, n.node_type,
           ST_X(n.geom) as lon, ST_Y(n.geom) as lat,
           ST_Distance(
               n.geom::geography,
               ST_SetSRID(ST_Point(%s, %s), 4326)::geography
           ) / 1000.0 as distance_km,
           r.depth
    FROM reachable r
    JOIN pipeline_nodes n ON n.id = r.node_id
    WHERE ST_Distance(
        n.geom::geography,
        ST_SetSRID(ST_Point(%s, %s), 4326)::geography
    ) > 50000  -- At least 50km away
    ORDER BY distance_km
    LIMIT 5
""", (hub_id, hub_id, hub_id, hub_lon, hub_lat, hub_lon, hub_lat))

destinations = cur.fetchall()
if not destinations:
    print("  ❌ No distant connected nodes found\n")
    exit(1)

print(f"  Found {len(destinations)} connected destinations:\n")
for dest in destinations:
    dest_id, dest_name, dest_type, dest_lon, dest_lat, dist_km, hops = dest
    print(f"    Node {dest_id}: {dest_name} ({dest_type})")
    print(f"      Location: ({dest_lon:.4f}, {dest_lat:.4f})")
    print(f"      Distance: {dist_km:.1f} km, {hops} hops away")

# Pick the first one and test routing
dest_id, dest_name, dest_type, dest_lon, dest_lat, dist_km, hops = destinations[0]

print(f"\n✅ Test route: {hub_name} → {dest_name}")
print(f"   Start: ({hub_lon:.4f}, {hub_lat:.4f})")
print(f"   End:   ({dest_lon:.4f}, {dest_lat:.4f})")
print(f"   Air distance: {dist_km:.1f} km\n")

# Test the route
print("Step 3: Calculate actual pipeline route")
cur.execute("""
    SELECT COUNT(*) FROM pgr_dijkstra(
        'SELECT id, source, target, cost_composite as cost, reverse_cost_composite as reverse_cost
         FROM pipeline_edges
         WHERE source != target
           AND status IN (''operating'', ''construction'')
           AND cost_composite > 0',
        %s, %s,
        directed := false
    )
""", (hub_id, dest_id))
segments = cur.fetchone()[0]

if segments > 0:
    print(f"  ✅ Route found with {segments} segments!\n")
    
    # Get detailed route
    cur.execute("""
        SELECT d.seq, n.name, ROUND(d.agg_cost::numeric, 4) as cumulative_cost,
               ROUND(e.cost_distance_km::numeric, 2) as segment_km
        FROM pgr_dijkstra(
            'SELECT id, source, target, cost_composite as cost, reverse_cost_composite as reverse_cost
             FROM pipeline_edges
             WHERE source != target
               AND status IN (''operating'', ''construction'')
               AND cost_composite > 0',
            %s, %s,
            directed := false
        ) d
        LEFT JOIN pipeline_nodes n ON n.id = d.node
        LEFT JOIN pipeline_edges e ON e.id = d.edge
        ORDER BY d.seq
        LIMIT 10
    """, (hub_id, dest_id))
    
    route_preview = cur.fetchall()
    print("  Route preview (first 10 segments):")
    print("  Seq | Node Name                         | Total Cost | Segment KM")
    print("  " + "-" * 75)
    for row in route_preview:
        seq, name, cost, km = row
        name = (name or "")[:35].ljust(35)
        print(f"  {seq:3d} | {name} | {cost or 0:10.4f} | {km or 0:10.2f}")
    
    print(f"\n✅ Use these coordinates for API testing:")
    print(f"   GET /api/v1/pipelines/route?start_lon={hub_lon:.6f}&start_lat={hub_lat:.6f}&end_lon={dest_lon:.6f}&end_lat={dest_lat:.6f}&cost_type=composite")
else:
    print(f"  ❌ Still no route found")

cur.close()
conn.close()

print("\n✅ Analysis complete!")
